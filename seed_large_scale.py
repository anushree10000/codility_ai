import sys
import uuid
import random
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text
from app.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url_sync)

def generate_uuid():
    return str(uuid.uuid4())

def seed_large_scale():
    print("Seeding large scale data...")
    with engine.begin() as conn:
        # Clear existing data
        print("Clearing existing data...")
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        conn.execute(text("TRUNCATE TABLE dead_letter_queue;"))
        conn.execute(text("TRUNCATE TABLE job_logs;"))
        conn.execute(text("TRUNCATE TABLE job_executions;"))
        conn.execute(text("TRUNCATE TABLE jobs;"))
        conn.execute(text("TRUNCATE TABLE queues;"))
        conn.execute(text("TRUNCATE TABLE retry_policies;"))
        conn.execute(text("TRUNCATE TABLE projects;"))
        conn.execute(text("TRUNCATE TABLE org_members;"))
        conn.execute(text("TRUNCATE TABLE organizations;"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))

        # 1. User (assume one exists, or create a demo user)
        user_id = generate_uuid()
        conn.execute(text("""
            INSERT IGNORE INTO users (id, email, password_hash, full_name, is_active, created_at) 
            VALUES (:id, :email, 'hash', 'Demo User', 1, NOW())
        """), {"id": user_id, "email": "demo@codity.local"})

        # 2. Orgs
        print("Creating Organizations & Projects...")
        org_id = generate_uuid()
        conn.execute(text("INSERT INTO organizations (id, name, slug, created_at) VALUES (:id, :name, :slug, NOW())"), 
                     {"id": org_id, "name": "Codity Enterprise", "slug": "codity-ent"})

        # 3. Projects
        proj_id_1 = generate_uuid()
        proj_id_2 = generate_uuid()
        conn.execute(text("INSERT INTO projects (id, org_id, name, slug, created_at, updated_at) VALUES (:id, :org, :name, :slug, NOW(), NOW())"),
                     [{"id": proj_id_1, "org": org_id, "name": "Payment Processing", "slug": "payments"},
                      {"id": proj_id_2, "org": org_id, "name": "Data Engineering", "slug": "data-eng"}])

        # 4. Retry Policy
        policy_id = generate_uuid()
        conn.execute(text("INSERT INTO retry_policies (id, name, strategy, max_retries, base_delay_seconds, max_delay_seconds, jitter, created_at) VALUES (:id, :name, :strategy, 5, 10, 3600, 1, NOW())"),
                     {"id": policy_id, "name": "Standard Retry", "strategy": "exponential"})

        # 5. Queues
        print("Creating Queues...")
        queues = [
            {"id": generate_uuid(), "project_id": proj_id_1, "name": "Stripe Webhooks", "slug": "stripe-webhooks", "retry_policy_id": policy_id},
            {"id": generate_uuid(), "project_id": proj_id_1, "name": "Email Notifications", "slug": "emails", "retry_policy_id": policy_id},
            {"id": generate_uuid(), "project_id": proj_id_2, "name": "Nightly ETL", "slug": "etl", "retry_policy_id": policy_id},
            {"id": generate_uuid(), "project_id": proj_id_2, "name": "Image Processing", "slug": "images", "retry_policy_id": policy_id}
        ]
        conn.execute(text("INSERT INTO queues (id, project_id, name, slug, retry_policy_id, priority, concurrency_limit, is_paused, max_job_duration_seconds, created_at, updated_at) VALUES (:id, :project_id, :name, :slug, :retry_policy_id, 0, 20, 0, 3600, NOW(), NOW())"), queues)

        # 6. Jobs (Generate ~500 jobs over the last 7 days)
        print("Spawning 1000 simulated jobs across the last 7 days...")
        statuses = ["completed"] * 70 + ["failed"] * 10 + ["dead_lettered"] * 5 + ["queued"] * 10 + ["running"] * 5
        
        now = datetime.now(timezone.utc)
        jobs_data = []
        for i in range(1000):
            job_id = generate_uuid()
            q_id = random.choice(queues)["id"]
            status = random.choice(statuses)
            
            # Random date in the last 7 days
            days_ago = random.uniform(0, 7)
            created_at = now - timedelta(days=days_ago)
            
            completed_at = None
            if status in ["completed", "failed", "dead_lettered"]:
                completed_at = created_at + timedelta(seconds=random.uniform(2, 60))
                
            jobs_data.append({
                "id": job_id,
                "queue_id": q_id,
                "type": "immediate",
                "status": status,
                "priority": random.randint(1, 10),
                "payload": '{"task": "simulated_work", "data": "dummy"}',
                "attempt_count": random.randint(1, 3) if status != "queued" else 0,
                "max_retries": 3,
                "created_by": user_id,
                "created_at": created_at,
                "completed_at": completed_at
            })

        # Insert jobs in batches
        stmt = text("""
            INSERT INTO jobs (id, queue_id, type, status, priority, payload, attempt_count, max_retries, created_by, created_at, completed_at)
            VALUES (:id, :queue_id, :type, :status, :priority, :payload, :attempt_count, :max_retries, :created_by, :created_at, :completed_at)
        """)
        conn.execute(stmt, jobs_data)
        
        print("Successfully seeded full scale production data!")

if __name__ == "__main__":
    seed_large_scale()
