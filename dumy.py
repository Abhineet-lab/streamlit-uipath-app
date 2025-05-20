import streamlit as st
import requests

# Constants
BEARER_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjRBQjhBQ0Q1QTZBRDczMDExMjQ0NTQ0MDFFM0VEQzdFQTg1MkNBMkIiLCJ4NXQiOiJTcmlzMWFhdGN3RVNSRlJBSGo3Y2ZxaFN5aXMiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2Nsb3VkLnVpcGF0aC5jb20vaWRlbnRpdHlfIiwibmJmIjoxNzQ3NzE5ODgwLCJpYXQiOjE3NDc3MjAxODAsImV4cCI6MTc0NzcyMzc4MCwiYXVkIjpbIklkZW50aXR5U2VydmVyQXBpIiwiT3JjaGVzdHJhdG9yQXBpVXNlckFjY2VzcyIsIkNvbm5lY3Rpb25TZXJ2aWNlIiwiT01TIl0sInNjb3BlIjpbIm9wZW5pZCIsInByb2ZpbGUiLCJlbWFpbCIsInRlbmFudCIsIklkZW50aXR5U2VydmVyQXBpIiwiT3JjaGVzdHJhdG9yQXBpVXNlckFjY2VzcyIsIkNvbm5lY3Rpb25TZXJ2aWNlIiwiT01TIl0sImFtciI6WyJleHRlcm5hbCJdLCJzdWJfdHlwZSI6InVzZXIiLCJjbGllbnRfaWQiOiJiYjU1YzBhMi1kMmNjLTQwN2EtOWMxZS01ZjY1ZTEyZWFlNzciLCJzdWIiOiI1ZTE3NmIzNC04MWVhLTRhYWYtYjk1OC1mZjUzZTc1NGM3MWMiLCJhdXRoX3RpbWUiOjE3NDc3MjAxMDQsImlkcCI6Im9pZGMiLCJlbWFpbCI6ImFiaGluZWV0LmR1YmV5QGRlbnRzdS5jb20iLCJBc3BOZXQuSWRlbnRpdHkuU2VjdXJpdHlTdGFtcCI6IlRKTVM1NjZDRDQ0VlA3R0VPNlFLS0hKRkVKV1kzQUNUIiwiZXh0X3N1YiI6ImdGWGlBUlN2QVR0azJVT1RZaTlXTzRtUGtuSmI4RFVlQ3RteG12aEhLWXMiLCJwcnRfaWQiOiI4NGM1MmFkYS0xYTYxLTRkNDEtYjhlMy1jNTJlODQwZmU2MWEiLCJob3N0IjoiRmFsc2UiLCJmaXJzdF9uYW1lIjoiQUJISU5FRVQiLCJsYXN0X25hbWUiOiJEVUJFWSIsInBydF9hZG0iOiJGYWxzZSIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwicHJlZmVycmVkX3VzZXJuYW1lIjoiYWJoaW5lZXQuZHViZXlAZGVudHN1LmNvbSIsIm5hbWUiOiJhYmhpbmVldC5kdWJleUBkZW50c3UuY29tIiwiZXh0X2lkcF9pZCI6Ijc0IiwiZXh0X2lkcF9kaXNwX25hbWUiOiJhYWQiLCJzaWQiOiI5QzI0QThEOTgyQkQ3QkI5NkFGN0VDODM1MDVGREEwNSJ9.cYLfj18PA5jDWYkdVsFUY61Xg8zBkHD9glnaU674SGCk3Lp0API_ziHwbpWnY6meR633ccSyxjSzwXgzvVcKxqYA6nUypfMPNWoaWpNICp_sJm8CMWS4f70AIxb3PiS7hM5IK6vFQ0FEMwd3R_I70-PWmtyoyDU5qrYVTlwxbBA2_AZWhK0_FDb78yP3It6qUYeQsNjGP48xhbQzhLL-CfNI_NvI66Jcn0av1AbMdnKnjiO0c_TMwIHaQiWUvvWeu_nis24e_JushnHZgD2iy_Slm5pO196aAsVP9PYJy9Vn6-TpuK3d6ejOazkUWnHYFtJ075v2eiCCTG5bHBFZUw"
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
