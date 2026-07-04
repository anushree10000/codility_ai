import streamlit as st
import requests
import os
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")

st.set_page_config(page_title="Codity Job Scheduler", page_icon="⚙️", layout="wide")

# Custom CSS for metrics and styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        text-align: center;
        border-left: 5px solid #00C853;
    }
    .metric-title { font-size: 1.1rem; color: #B0BEC5; margin-bottom: 5px; }
    .metric-value { font-size: 2.5rem; font-weight: bold; color: white; }
    div[data-testid="stSidebarNav"] { display: none; }
</style>
""", unsafe_allow_html=True)

if "token" not in st.session_state:
    st.session_state.token = None

def api_get(endpoint):
    headers = {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}
    try:
        response = requests.get(f"{API_URL}{endpoint}", headers=headers)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def api_post(endpoint, json=None):
    headers = {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}
    try:
        response = requests.post(f"{API_URL}{endpoint}", json=json, headers=headers)
        return response.json() if response.status_code in [200, 201] else {"error": response.text}
    except Exception as e:
        return {"error": str(e)}

def login():
    st.title("⚙️ Codity Scheduler")
    st.markdown("Welcome to the Distributed Job Scheduler Dashboard. Please login to continue.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Login")
        email = st.text_input("Email", key="log_email")
        password = st.text_input("Password", type="password", key="log_pass")
        if st.button("Login", use_container_width=True):
            res = api_post("/auth/login", json={"email": email, "password": password})
            if "access_token" in res:
                st.session_state.token = res["access_token"]
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error(res.get("error", "Login failed"))
                
    with col2:
        st.subheader("Register")
        full_name = st.text_input("Full Name")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_pass")
        if st.button("Register", use_container_width=True):
            res = api_post("/auth/register", json={"email": reg_email, "password": reg_password, "full_name": full_name})
            if "id" in res:
                st.success("Registered successfully. Please login on the left.")
            else:
                st.error(res.get("error", "Registration failed"))

def render_overview(workers, queues):
    st.header("📊 System Overview")
    
    # Calculate metrics
    active_workers = len(workers) if workers else 0
    total_active_jobs = sum(w.get("active_jobs", 0) for w in workers) if workers else 0
    total_queues = len(queues) if queues else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #29B6F6;">
            <div class="metric-title">Active Workers</div>
            <div class="metric-value">{active_workers}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #FFA726;">
            <div class="metric-title">Jobs Running Now</div>
            <div class="metric-value">{total_active_jobs}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #66BB6A;">
            <div class="metric-title">Total Queues</div>
            <div class="metric-value">{total_queues}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #AB47BC;">
            <div class="metric-title">System Health</div>
            <div class="metric-value">{"Healthy" if active_workers > 0 else "Degraded"}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    
    if queues:
        # Fetch some jobs for the global chart (using the first queue for demo purposes)
        # In a real app, you might have a global jobs endpoint or aggregate them
        first_q = queues[0]["id"]
        jobs = api_get(f"/queues/{first_q}/jobs")
        if jobs:
            df = pd.DataFrame(jobs)
            status_counts = df['status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            
            c1, c2 = st.columns(2)
            with c1:
                fig = px.pie(status_counts, values='Count', names='Status', title=f"Job Status Distribution (Queue: {queues[0]['name']})", 
                             color='Status', color_discrete_map={'completed':'green', 'failed':'red', 'queued':'orange', 'running':'blue', 'dead_lettered':'purple'})
                st.plotly_chart(fig, use_container_width=True)
                
            with c2:
                # Use real historical data for the throughput graph
                df['created_at'] = pd.to_datetime(df['created_at'])
                df['Date'] = df['created_at'].dt.date
                throughput = df.groupby('Date').size().reset_index(name='Jobs Processed')
                
                # Fill missing dates if necessary
                if not throughput.empty:
                    idx = pd.date_range(throughput['Date'].min(), throughput['Date'].max())
                    throughput.set_index('Date', inplace=True)
                    throughput.index = pd.DatetimeIndex(throughput.index)
                    throughput = throughput.reindex(idx, fill_value=0).reset_index()
                    throughput.rename(columns={'index': 'Date'}, inplace=True)
                
                fig2 = px.line(throughput, x='Date', y='Jobs Processed', title='System Throughput (Last 7 Days)', markers=True)
                st.plotly_chart(fig2, use_container_width=True)
                
            c3, c4 = st.columns(2)
            with c3:
                # Job Creation vs Completion
                created_df = df.copy()
                created_counts = created_df.groupby('Date').size().reset_index(name='Jobs Created')
                
                completed_df = df[df['status'] == 'completed'].copy()
                if not completed_df.empty:
                    completed_df['completed_at'] = pd.to_datetime(completed_df['completed_at'])
                    completed_df['Date_completed'] = completed_df['completed_at'].dt.date
                    completed_counts = completed_df.groupby('Date_completed').size().reset_index(name='Jobs Completed')
                    
                    merged = pd.merge(created_counts, completed_counts, left_on='Date', right_on='Date_completed', how='outer').fillna(0)
                    merged['Date'] = merged['Date'].fillna(merged['Date_completed'])
                    merged = merged.drop(columns=['Date_completed'])
                else:
                    merged = created_counts
                    merged['Jobs Completed'] = 0
                
                melted = pd.melt(merged, id_vars=['Date'], value_vars=['Jobs Created', 'Jobs Completed'], var_name='Metric', value_name='Count')
                fig3 = px.line(melted, x='Date', y='Count', color='Metric', title='Creation vs Completion Over Time', markers=True)
                st.plotly_chart(fig3, use_container_width=True)
                
            with c4:
                # Failure Rate Over Time
                total_by_date = df.groupby('Date').size().reset_index(name='Total')
                failed_df = df[df['status'].isin(['failed', 'dead_lettered'])].copy()
                failed_counts = failed_df.groupby('Date').size().reset_index(name='Failed')
                
                failure_merged = pd.merge(total_by_date, failed_counts, on='Date', how='left').fillna(0)
                failure_merged['Failure Rate (%)'] = (failure_merged['Failed'] / failure_merged['Total']) * 100
                
                fig4 = px.line(failure_merged, x='Date', y='Failure Rate (%)', title='Failure Rate Over Time (%)', markers=True, color_discrete_sequence=['red'])
                st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No jobs found in the primary queue yet to generate charts.")

def render_queues(queues):
    st.header("🗂️ Queue Management")
    if not queues:
        st.info("No queues found. Please create a project and queue.")
        return
        
    q_names = [q["name"] for q in queues]
    selected_q_name = st.selectbox("Select Queue", q_names)
    selected_queue = next(q for q in queues if q["name"] == selected_q_name)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"Queue Details: {selected_queue['name']}")
        st.write(f"**ID:** `{selected_queue['id']}`")
        st.write(f"**Concurrency Limit:** {selected_queue['concurrency_limit']}")
        st.write(f"**Status:** {'⏸️ Paused' if selected_queue['is_paused'] else '▶️ Active'}")
        
    with col2:
        st.subheader("Spawn Test Job")
        with st.form("spawn_job"):
            job_type = st.selectbox("Job Type", ["immediate", "delayed"])
            should_fail = st.checkbox("Simulate Failure (Test Retries & DLQ)")
            if st.form_submit_button("Spawn Job"):
                payload = {"task": "test_job", "should_fail": should_fail}
                res = api_post(f"/queues/{selected_queue['id']}/jobs", json={
                    "type": job_type,
                    "priority": 5,
                    "payload": payload
                })
                if "id" in res:
                    st.success("Job spawned successfully!")
                else:
                    st.error("Failed to spawn job.")

def render_jobs(queues):
    st.header("🔍 Jobs Explorer")
    if not queues:
        st.warning("No queues available.")
        return
        
    selected_q = st.selectbox("Filter by Queue", [q["id"] for q in queues], format_func=lambda x: next(q["name"] for q in queues if q["id"] == x))
    jobs = api_get(f"/queues/{selected_q}/jobs")
    
    if jobs:
        df = pd.DataFrame(jobs)
        # Clean up dataframe for display
        display_df = df[['id', 'status', 'type', 'priority', 'attempt_count', 'created_at']]
        
        # Add color coding to status
        def color_status(val):
            color = 'green' if val == 'completed' else 'red' if val in ['failed', 'dead_lettered'] else 'orange' if val == 'queued' else 'blue'
            return f'color: {color}; font-weight: bold;'
            
        st.dataframe(display_df.style.map(color_status, subset=['status']), use_container_width=True)
        
        st.subheader("Job Details")
        selected_job_id = st.selectbox("Inspect Job", display_df['id'].tolist())
        selected_job = next(j for j in jobs if j["id"] == selected_job_id)
        
        c1, c2 = st.columns(2)
        with c1:
            st.json(selected_job.get("payload", {}))
        with c2:
            if selected_job["status"] in ["failed", "dead_lettered"]:
                st.error(f"Job is currently {selected_job['status']}")
                # A button to retry logic could go here
    else:
        st.info("No jobs found in this queue.")

def render_workers(workers):
    st.header("🤖 Workers Topology")
    if not workers:
        st.warning("No active workers detected. Ensure `worker/main.py` is running.")
        return
        
    cols = st.columns(3)
    for i, worker in enumerate(workers):
        with cols[i % 3]:
            status_color = "#4CAF50" if worker["status"] == "online" else "#FF9800" if worker["status"] == "busy" else "#F44336"
            st.markdown(f"""
            <div style="background-color: #2C2C2C; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-top: 4px solid {status_color};">
                <h4 style="margin-top: 0;">{worker['hostname']}</h4>
                <p style="margin-bottom: 5px; color: #AAA;">ID: <code>{worker['id'][:8]}...</code></p>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 15px;">
                    <span style="background-color: {status_color}20; color: {status_color}; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem;">{worker['status'].upper()}</span>
                    <span style="font-size: 0.9rem;"><strong>{worker['active_jobs']}</strong> / {worker['concurrency']} jobs</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

def render_dlq(queues):
    st.header("☠️ Dead Letter Queue")
    st.info("Jobs that exhaust all retries are sent here.")
    if not queues:
        st.warning("No queues available.")
        return
        
    selected_q = st.selectbox("Select Queue for DLQ", [q["id"] for q in queues], format_func=lambda x: next(q["name"] for q in queues if q["id"] == x), key="dlq_queue_select")
    dlq_entries = api_get(f"/queues/{selected_q}/dlq")
    
    if dlq_entries:
        df = pd.DataFrame(dlq_entries)
        display_df = df[['id', 'job_id', 'total_attempts', 'dead_lettered_at', 'failure_reason']]
        
        st.dataframe(display_df, use_container_width=True)
        
        st.subheader("Requeue Job")
        selected_dlq_id = st.selectbox("Select DLQ Entry to Requeue", display_df['id'].tolist(), key="dlq_entry_select")
        
        if st.button("Requeue Job"):
            res = api_post(f"/dlq/{selected_dlq_id}/requeue")
            if "id" in res:
                st.success("Job successfully requeued!")
            else:
                st.error("Failed to requeue job.")
    else:
        st.success("No dead letters currently visible for this queue.")

def dashboard():
    # Auto-refresh the page every 5 seconds (5000 milliseconds)
    st_autorefresh(interval=5000, limit=None, key="dashboard_autorefresh")
    
    # Top header area
    head_col1, head_col2 = st.columns([5, 1])
    with head_col1:
        st.title("⚙️ Codity Scheduler")
    with head_col2:
        st.write("") # Spacing
        if st.button("Logout", use_container_width=True):
            st.session_state.token = None
            st.rerun()
            
    st.markdown("---")
    
    # Fetch global data for the dashboard
    orgs = api_get("/organizations")
    projects = []
    queues = []
    if orgs:
        projects = api_get(f"/organizations/{orgs[0]['id']}/projects")
        if projects:
            queues = api_get(f"/projects/{projects[0]['id']}/queues")
            
    workers = api_get("/workers")
    
    tabs = st.tabs(["📊 Overview", "🗂️ Queues", "🔍 Jobs", "🤖 Workers", "☠️ DLQ"])
    
    with tabs[0]:
        render_overview(workers, queues)
        
    with tabs[1]:
        render_queues(queues)
        
    with tabs[2]:
        render_jobs(queues)
        
    with tabs[3]:
        render_workers(workers)
        
    with tabs[4]:
        render_dlq(queues)

if not st.session_state.token:
    login()
else:
    dashboard()
