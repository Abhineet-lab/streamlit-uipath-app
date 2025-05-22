import streamlit as st
import requests
import pandas as pd
from io import BytesIO
import base64

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

    st.subheader("Selected Job Info:")
    color = get_color_for_job_state(selected_job['State'])
    st.markdown(f"<div style='color:{color}; font-weight:bold;'>State: {selected_job['State']}</div>", unsafe_allow_html=True)

    # Step 4: Filter logs by level
    st.header("Job Logs (Filtered by Job ID)")
    log_levels = ["All", "Fatal", "Error", "Warn", "Info", "Debug", "Trace", "Verbose"]
    selected_log_level = st.selectbox("Select Log Level", log_levels)

    all_logs = api_get("RobotLogs", folder_id=folder_id).get("value", [])
    job_logs = [log for log in all_logs if log.get("JobKey") == selected_job["Key"]]

    if selected_log_level != "All":
        job_logs = [log for log in job_logs if log["Level"] == selected_log_level]

    log_text_output = ""
    if job_logs:
        for log in job_logs:
            log_color = get_color_for_log_level(log["Level"])
            message = f"[{log['TimeStamp']}] {log['Level']} - {log['Message']}"
            st.markdown(f"<div style='color:{log_color}; font-size:15px;'>{message}</div>", unsafe_allow_html=True)
            log_text_output += message + "\n"

        # Convert logs to DataFrame
        df_logs = pd.DataFrame(job_logs)

        # Step 5: Choose download format
        file_format = st.selectbox("Choose download format", ["TXT", "CSV", "XLSX"], key="format1")

        # Generate file data
        if file_format == "TXT":
            file_data = log_text_output
            mime_type = "text/plain"
            file_name = "uipath_job_logs.txt"
        elif file_format == "CSV":
            file_data = df_logs.to_csv(index=False)
            mime_type = "text/csv"
            file_name = "uipath_job_logs.csv"
        elif file_format == "XLSX":
            buffer = BytesIO()
            df_logs.to_excel(buffer, index=False)
            buffer.seek(0)
            file_data = buffer
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            file_name = "uipath_job_logs.xlsx"

        # Encode for download
        if file_format in ["TXT", "CSV"]:
            b64 = base64.b64encode(file_data.encode()).decode()
        else:
            b64 = base64.b64encode(file_data.read()).decode()
            file_data.seek(0)

        st.markdown(f"""
            <div style="text-align: right; margin-top: 20px;">
                <a href="data:{mime_type};base64,{b64}" download="{file_name}">
                    <button style="background-color: #4CAF50; color: white; padding: 10px 20px;
                                   border: none; border-radius: 5px; cursor: pointer;">
                        📥 Download Logs as {file_format}
                    </button>
                </a>
            </div>
        """, unsafe_allow_html=True)

    else:
        st.warning("No logs found for the selected filters.")
else:
    st.warning("No jobs found for this filter.")

# Optional: All logs in folder
st.header("📜 All Logs for Selected Folder (Org Unit)")
show_all_logs = st.checkbox("Show all logs for this folder", value=False)
if show_all_logs:
    all_logs = api_get("RobotLogs", folder_id=folder_id).get("value", [])
    full_log_text = ""
    for log in all_logs:
        log_color = get_color_for_log_level(log["Level"])
        message = f"[{log['TimeStamp']}] {log['Level']} - {log['Message']}"
        st.markdown(f"<div style='color:{log_color}; font-size:15px;'>{message}</div>", unsafe_allow_html=True)
        full_log_text += message + "\n"

    if all_logs:
        df_all_logs = pd.DataFrame(all_logs)
        file_format2 = st.selectbox("Choose download format for all logs", ["TXT", "CSV", "XLSX"], key="format2")

        if file_format2 == "TXT":
            file_data2 = full_log_text
            mime_type2 = "text/plain"
            file_name2 = "uipath_all_logs.txt"
        elif file_format2 == "CSV":
            file_data2 = df_all_logs.to_csv(index=False)
            mime_type2 = "text/csv"
            file_name2 = "uipath_all_logs.csv"
        elif file_format2 == "XLSX":
            buffer2 = BytesIO()
            df_all_logs.to_excel(buffer2, index=False)
            buffer2.seek(0)
            file_data2 = buffer2
            mime_type2 = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            file_name2 = "uipath_all_logs.xlsx"

        if file_format2 in ["TXT", "CSV"]:
            b64_2 = base64.b64encode(file_data2.encode()).decode()
        else:
            b64_2 = base64.b64encode(file_data2.read()).decode()
            file_data2.seek(0)

        st.markdown(f"""
            <div style="text-align: right; margin-top: 20px;">
                <a href="data:{mime_type2};base64,{b64_2}" download="{file_name2}">
                    <button style="background-color: #4CAF50; color: white; padding: 10px 20px;
                                   border: none; border-radius: 5px; cursor: pointer;">
                        📥 Download All Logs as {file_format2}
                    </button>
                </a>
            </div>
        """, unsafe_allow_html=True)
