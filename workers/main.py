import asyncio
import signal
import uuid
import socket
import logging
import sys
from pathlib import Path
from datetime import datetime, timezone
import traceback

# Add the parent directory to sys.path so we can import 'app'
sys.path.append(str(Path(__file__).resolve().parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session
from app.config import get_settings
from app.models.worker import Worker
from app.models.worker_heartbeat import WorkerHeartbeat
from app.models.job_execution import JobExecution
from app.models.dead_letter_queue import DeadLetterQueue
from app.repositories import worker_repo, job_repo, queue_repo
from app.utils.retry import calculate_retry_delay
from app.core.constants import WorkerStatus, JobStatus, ExecutionStatus
import psutil

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class WorkerNode:
    def __init__(self, queue_id: str | None = None, concurrency: int = 5):
        self.worker_id = str(uuid.uuid4())
        self.hostname = socket.gethostname()
        self.pid = psutil.Process().pid
        self.queue_id = queue_id
        self.concurrency = concurrency
        self.active_jobs = 0
        self.is_running = False
        self.semaphore = asyncio.Semaphore(concurrency)

    async def register(self, db: AsyncSession):
        worker = Worker(
            id=self.worker_id,
            hostname=self.hostname,
            pid=self.pid,
            queue_id=self.queue_id,
            status=WorkerStatus.online.value,
            concurrency=self.concurrency,
            active_jobs=0,
            registered_at=datetime.now(timezone.utc),
            last_heartbeat_at=datetime.now(timezone.utc)
        )
        await worker_repo.register_worker(db, worker)
        logger.info(f"Worker {self.worker_id} registered.")

    async def heartbeat_loop(self):
        while self.is_running:
            try:
                async with async_session() as db:
                    worker = await worker_repo.get_worker_by_id(db, self.worker_id)
                    if worker:
                        worker.last_heartbeat_at = datetime.now(timezone.utc)
                        worker.active_jobs = self.active_jobs
                        worker.status = WorkerStatus.online.value if self.active_jobs < self.concurrency else WorkerStatus.busy.value
                        await worker_repo.update_worker(db, worker)

                        hb = WorkerHeartbeat(
                            worker_id=self.worker_id,
                            active_jobs=self.active_jobs,
                            cpu_usage=psutil.cpu_percent(),
                            memory_usage=psutil.virtual_memory().percent,
                            timestamp=datetime.now(timezone.utc)
                        )
                        db.add(hb)
                        await db.commit()
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
            await asyncio.sleep(10)

    async def execute_job(self, job_id: str):
        self.active_jobs += 1
        start_time = datetime.now(timezone.utc)
        
        async with async_session() as db:
            job = await job_repo.get_job_by_id(db, job_id)
            if not job:
                self.active_jobs -= 1
                return

            job.attempt_count += 1
            job.started_at = start_time
            job.status = JobStatus.running.value
            await job_repo.update_job(db, job)

            execution = JobExecution(
                id=str(uuid.uuid4()),
                job_id=job.id,
                worker_id=self.worker_id,
                attempt_number=job.attempt_count,
                status=ExecutionStatus.running.value,
                started_at=start_time
            )
            await job_repo.create_job_execution(db, execution)
            await db.commit()

            error_msg = None
            error_tb = None
            success = False

            try:
                # Simulate job execution
                logger.info(f"Executing job {job.id} (type: {job.type}, attempt: {job.attempt_count})")
                await asyncio.sleep(2)  # Simulating work
                
                if job.payload and job.payload.get("should_fail"):
                    raise Exception("Simulated job failure based on payload!")
                    
                logger.info(f"Job {job.id} completed successfully.")
                success = True
            except Exception as e:
                error_msg = str(e)
                error_tb = traceback.format_exc()
                logger.error(f"Job {job.id} failed: {error_msg}")

            # Update completion status
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            execution.completed_at = end_time
            execution.duration_ms = duration_ms
            execution.status = ExecutionStatus.completed.value if success else ExecutionStatus.failed.value
            if not success:
                execution.error_message = error_msg
                execution.error_traceback = error_tb
            await db.merge(execution)

            if success:
                job.status = JobStatus.completed.value
                job.completed_at = end_time
            else:
                if job.attempt_count >= job.max_retries:
                    job.status = JobStatus.dead_lettered.value
                    dlq = DeadLetterQueue(
                        id=str(uuid.uuid4()),
                        job_id=job.id,
                        queue_id=job.queue_id,
                        failure_reason=error_msg,
                        last_error=error_tb,
                        total_attempts=job.attempt_count,
                        dead_lettered_at=end_time
                    )
                    await job_repo.create_dlq_entry(db, dlq)
                    logger.warning(f"Job {job.id} moved to DLQ.")
                else:
                    queue = await queue_repo.get_queue_by_id(db, job.queue_id)
                    retry_policy = await db.get(queue_repo.RetryPolicy, queue.retry_policy_id) if queue.retry_policy_id else None
                    delay = 60
                    if retry_policy:
                        delay = calculate_retry_delay(
                            strategy=retry_policy.strategy,
                            attempt=job.attempt_count,
                            base_delay=retry_policy.base_delay_seconds,
                            max_delay=retry_policy.max_delay_seconds,
                            jitter=retry_policy.jitter
                        )
                    job.status = JobStatus.queued.value
                    job.scheduled_at = datetime.fromtimestamp(end_time.timestamp() + delay, tz=timezone.utc)
                    job.worker_id = None
                    logger.info(f"Job {job.id} failed. Retrying in {delay}s...")
            
            await job_repo.update_job(db, job)
            await db.commit()

        self.active_jobs -= 1
        self.semaphore.release()

    async def poll_queues(self):
        while self.is_running:
            await self.semaphore.acquire()
            
            job_claimed = False
            try:
                async with async_session() as db:
                    # Fetch active queues
                    queues = []
                    if self.queue_id:
                        queues = [await queue_repo.get_queue_by_id(db, self.queue_id)]
                    else:
                        # Poll all queues (naive for now)
                        res = await db.execute(queue_repo.select(queue_repo.Queue).where(queue_repo.Queue.is_paused == False))
                        queues = res.scalars().all()

                    for queue in queues:
                        if not queue or queue.is_paused:
                            continue
                            
                        job = await job_repo.claim_next_job(db, str(queue.id), self.worker_id)
                        if job:
                            await db.commit()
                            job_claimed = True
                            asyncio.create_task(self.execute_job(str(job.id)))
                            break  # Move to next tick to process claimed job

            except Exception as e:
                logger.error(f"Polling error: {e}")
                self.semaphore.release()
                await asyncio.sleep(5)
                continue

            if not job_claimed:
                self.semaphore.release()
                await asyncio.sleep(1) # Backoff if no jobs

    async def start(self):
        self.is_running = True
        async with async_session() as db:
            await self.register(db)
            await db.commit()

        asyncio.create_task(self.heartbeat_loop())
        await self.poll_queues()

    async def stop(self):
        logger.info("Worker draining...")
        self.is_running = False
        # Wait for active jobs to finish
        while self.active_jobs > 0:
            await asyncio.sleep(1)
            
        async with async_session() as db:
            worker = await worker_repo.get_worker_by_id(db, self.worker_id)
            if worker:
                worker.status = WorkerStatus.offline.value
                await worker_repo.update_worker(db, worker)
                await db.commit()
        logger.info("Worker stopped cleanly.")


async def main():
    worker = WorkerNode(concurrency=5)

    loop = asyncio.get_running_loop()
    
    stop_event = asyncio.Event()

    def handle_sigterm():
        logger.info("Received termination signal")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_sigterm)

    worker_task = asyncio.create_task(worker.start())
    
    await stop_event.wait()
    await worker.stop()
    worker_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
