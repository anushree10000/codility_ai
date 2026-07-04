import requests
import json
from datetime import datetime, timezone, timedelta

API_URL = "http://localhost:8000/api/v1"

def seed():
    print("Seeding database via API...")

    # 1. Register User
    print("1. Creating user...")
    user_data = {
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User"
    }
    res = requests.post(f"{API_URL}/auth/register", json=user_data)
    if res.status_code != 201 and "already registered" not in res.text:
        print(f"Failed to register user: {res.text}")
        return

    # 2. Login
    print("2. Logging in...")
    res = requests.post(f"{API_URL}/auth/login", json={"email": "test@example.com", "password": "password123"})
    if res.status_code != 200:
        print(f"Login failed: {res.text}")
        return
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create Organization
    print("3. Creating organization...")
    org_data = {"name": "Acme Corp", "slug": "acme-corp"}
    res = requests.post(f"{API_URL}/organizations", json=org_data, headers=headers)
    
    if res.status_code == 201:
        org_id = res.json()["id"]
    else:
        # Fetch existing orgs
        orgs = requests.get(f"{API_URL}/organizations", headers=headers).json()
        org_id = orgs[0]["id"] if orgs else None
        
    if not org_id:
        print("Failed to get organization")
        return

    # 4. Create Project
    print("4. Creating project...")
    proj_data = {"name": "Data Pipeline", "slug": "data-pipeline", "description": "Nightly ETL jobs"}
    res = requests.post(f"{API_URL}/organizations/{org_id}/projects", json=proj_data, headers=headers)
    if res.status_code == 201:
        proj_id = res.json()["id"]
    else:
        projs = requests.get(f"{API_URL}/organizations/{org_id}/projects", headers=headers).json()
        proj_id = projs[0]["id"] if projs else None

    # 5. Create Retry Policy
    print("5. Creating retry policy...")
    policy_data = {
        "name": "Exponential Backoff",
        "strategy": "exponential",
        "max_retries": 3,
        "base_delay_seconds": 10,
        "max_delay_seconds": 300,
        "jitter": True
    }
    res = requests.post(f"{API_URL}/retry-policies", json=policy_data, headers=headers)
    if res.status_code == 201:
        policy_id = res.json()["id"]
    else:
        policies = requests.get(f"{API_URL}/retry-policies", headers=headers).json()
        policy_id = policies[0]["id"] if policies else None

    # 6. Create Queue
    print("6. Creating queue...")
    queue_data = {
        "name": "High Priority ETL",
        "slug": "high-priority-etl",
        "priority": 10,
        "concurrency_limit": 5,
        "retry_policy_id": policy_id,
        "is_paused": False
    }
    res = requests.post(f"{API_URL}/projects/{proj_id}/queues", json=queue_data, headers=headers)
    if res.status_code == 201:
        queue_id = res.json()["id"]
    else:
        queues = requests.get(f"{API_URL}/projects/{proj_id}/queues", headers=headers).json()
        queue_id = queues[0]["id"] if queues else None

    # 7. Create Sample Jobs
    print("7. Spawning sample jobs...")
    
    # Job 1: Immediate success
    requests.post(f"{API_URL}/queues/{queue_id}/jobs", headers=headers, json={
        "type": "immediate",
        "priority": 5,
        "payload": {"task": "extract_data", "source": "aws_s3"}
    })
    
    # Job 2: Delayed job
    future_time = (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat()
    requests.post(f"{API_URL}/queues/{queue_id}/jobs", headers=headers, json={
        "type": "delayed",
        "priority": 1,
        "payload": {"task": "send_report", "recipient": "admin@acme.com"},
        "scheduled_at": future_time
    })
    
    # Job 3: Will fail to test retry/DLQ (The worker simulates work right now, so it will actually just succeed unless we modify the worker to fail based on payload. For now, it just shows as a queued job.)
    requests.post(f"{API_URL}/queues/{queue_id}/jobs", headers=headers, json={
        "type": "immediate",
        "priority": 10,
        "payload": {"task": "risky_operation", "should_fail": True}
    })

    print("Seed complete! You can now log into the dashboard with:")
    print("Email: test@example.com")
    print("Password: password123")

if __name__ == "__main__":
    seed()
