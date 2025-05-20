import streamlit as st
import requests

# Constants
BEARER_TOKEN = st.secrets["BEARER_TOKEN"]
BASE_URL = st.secrets["BASE_URL"]

HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type": "application/json"
}

# Utility functions
def api_get(endpoint, params=None, folder_id=None):
    url = f"{BASE_URL}/{endpoint}"
    headers = HEADERS.copy()
    if folder_id:
        headers["X-UiPath-OrganizationUnitId"] = str(folder_id)
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def get_color_for_job_state(state):
    return {
        "Successful": "#008000",
        "Faulted": "#FF0000",
        "Stopped": "#FFA500"
    }.get(state, "#000000")

def get_color_for_log_level(level):
    return {
        "Fatal": "#800080",
        "Error": "#FF0000",
        "Warn": "#FFA500",
        "Info": "#1E90FF",
        "Debug": "#008000",
        "Trace": "#A9A9A9",
        "Verbose": "#000000"
    }.get(level, "#000000")

# Streamlit UI
st.set_page_config(page_title="UiPath Chatbot Dashboard", layout="wide")
st.title("🤖 UiPath Chatbot UI - Streamlit")

# Step 1: Select Folder
st.header("Select a Folder")
folders = api_get("Folders").get("value", [])
folder_map = {f["DisplayName"]: f["Id"] for f in folders}
selected_folder = st.selectbox("Choose a Folder", list(folder_map.keys()))
folder_id = folder_map[selected_folder]

# Step 2: Select Process
st.header("Select a Process")
processes = api_get("Releases", folder_id=folder_id).get("value", [])
process_names = list({p["ProcessKey"] for p in processes})
selected_process = st.selectbox("Choose a Process", process_names)

# Step 3: Filter Jobs by State
st.header("Choose Job Status")
job_state = st.selectbox("Select Job State", ["All", "Successful", "Faulted", "Stopped"])
filter_clause = f"ProcessKey eq '{selected_process}'"
if job_state != "All":
    filter_clause += f" and State eq '{job_state}'"

params = {
    "$orderby": "CreationTime desc",
    "$top": 20,
    "$filter": filter_clause
}
jobs = api_get("Jobs", params=None, folder_id=folder_id).get("value", [])

if jobs:
    st.success(f"Found {len(jobs)} job(s)")

    job_options = [
        f"{j['ReleaseName']} - {j['State']} - {j['StartTime'] or 'N/A'}"
        for j in jobs
    ]
    selected_index = st.selectbox("Select a Job", range(len(job_options)), format_func=lambda i: job_options[i])
    selected_job = jobs[selected_index]

    # Show colored job info
    st.subheader("Selected Job Info:")
    color = get_color_for_job_state(selected_job['State'])
    st.markdown(
        f"<div style='color:{color}; font-weight:bold;'>State: {selected_job['State']}</div>",
        unsafe_allow_html=True
    )

    # Step 4: Filter logs by level
    st.header("Job Logs (Filtered by Job ID)")
    log_levels = ["All", "Fatal", "Error", "Warn", "Info", "Debug", "Trace", "Verbose"]
    selected_log_level = st.selectbox("Select Log Level", log_levels)

    all_logs = api_get("RobotLogs", folder_id=folder_id).get("value", [])
    job_logs = [log for log in all_logs if log.get("JobKey") == selected_job["Key"]]

    if selected_log_level != "All":
        job_logs = [log for log in job_logs if log["Level"] == selected_log_level]

    if job_logs:
        for log in job_logs:
            log_color = get_color_for_log_level(log["Level"])
            st.markdown(
                f"<div style='color:{log_color}; font-size:15px;'>"
                f"[{log['TimeStamp']}] {log['Level']} - {log['Message']}"
                f"</div>", unsafe_allow_html=True
            )
    else:
        st.warning("No logs found for the selected filters.")
else:
    st.warning("No jobs found for this filter.")

# Optional: All logs in folder
st.header("📜 All Logs for Selected Folder (Org Unit)")
show_all_logs = st.checkbox("Show all logs for this folder", value=False)
if show_all_logs:
    all_logs = api_get("RobotLogs", folder_id=folder_id).get("value", [])
    for log in all_logs:
        log_color = get_color_for_log_level(log["Level"])
        st.markdown(
            f"<div style='color:{log_color}; font-size:15px;'>"
            f"[{log['TimeStamp']}] {log['Level']} - {log['Message']}"
            f"</div>", unsafe_allow_html=True
        )
