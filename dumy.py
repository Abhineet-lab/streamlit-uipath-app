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

st.set_page_config(page_title="UiPath Chatbot Dashboard", layout="wide")
st.title("🤖 UiPath Chatbot UI - Streamlit")

with st.expander("Select a Folder", expanded=False):
    folders = api_get("Folders").get("value", [])
    folder_map = {f["DisplayName"]: f["Id"] for f in folders}
    selected_folder = st.selectbox("Choose a Folder", list(folder_map.keys()))
    folder_id = folder_map[selected_folder]

with st.expander("Select a Process", expanded=False):
    processes = api_get("Releases", folder_id=folder_id).get("value", [])
    process_names = list({p["ProcessKey"] for p in processes})
    selected_process = st.selectbox("Choose a Process", process_names)

with st.expander("Choose Job Status", expanded=False):
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

with st.expander("Select a Job", expanded=False):
    if jobs:
        st.success(f"Found {len(jobs)} job(s)")
        job_options = [
            f"{j['ReleaseName']} - {j['State']} - {j['StartTime'] or 'N/A'}"
            for j in jobs
        ]
        selected_index = st.selectbox("Select a Job", range(len(job_options)), format_func=lambda i: job_options[i])
        selected_job = jobs[selected_index]

        color = get_color_for_job_state(selected_job['State'])
        st.markdown(f"<div style='color:{color}; font-weight:bold;'>State: {selected_job['State']}</div>", unsafe_allow_html=True)
    else:
        st.warning("No jobs found for this filter.")
        selected_job = None

if selected_job:
    with st.expander("Job Logs", expanded=False):
        selected_log_level = st.selectbox("Select Log Level",
                                          ["All", "Fatal", "Error", "Warn", "Info", "Debug", "Trace", "Verbose"])
        page_size = st.selectbox("Logs per page", [25, 50, 100])

        # Session state for pagination
        if "job_log_page" not in st.session_state:
            st.session_state.job_log_page = 1

        all_logs = api_get("RobotLogs", folder_id=folder_id).get("value", [])
        job_logs = [log for log in all_logs if log.get("JobKey") == selected_job["Key"]]

        if selected_log_level != "All":
            job_logs = [log for log in job_logs if log["Level"] == selected_log_level]

        total_logs = len(job_logs)
        total_pages = (total_logs + page_size - 1) // page_size

        # Clamp page number
        st.session_state.job_log_page = max(1, min(st.session_state.job_log_page, total_pages))

        start_idx = (st.session_state.job_log_page - 1) * page_size
        end_idx = start_idx + page_size
        paged_logs = job_logs[start_idx:end_idx]

        log_text_output = ""

        if paged_logs:
            for log in paged_logs:
                log_color = get_color_for_log_level(log["Level"])
                message = f"[{log['TimeStamp']}] {log['Level']} - {log['Message']}"
                st.markdown(f"<div style='color:{log_color}; font-size:15px;'>{message}</div>", unsafe_allow_html=True)
                log_text_output += message + "\n"

            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("⬅️ Previous"):
                    if st.session_state.job_log_page > 1:
                        st.session_state.job_log_page -= 1
                        st.rerun()
            with col2:
                st.markdown(
                    f"<div style='text-align:center; font-weight:bold;'>Page {st.session_state.job_log_page} of {total_pages}</div>",
                    unsafe_allow_html=True)
            with col3:
                if st.button("Next ➡️"):
                    if st.session_state.job_log_page < total_pages:
                        st.session_state.job_log_page += 1
                        st.rerun()

            # Download logs
            df_logs = pd.DataFrame(job_logs)
            file_format = st.selectbox("Choose download format", ["TXT", "CSV", "XLSX"])
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

            b64 = base64.b64encode(file_data.encode() if file_format != "XLSX" else file_data.read()).decode()
            if file_format == "XLSX":
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

with st.expander("All Logs in Folder (Optional)", expanded=False):
    show_all_logs = st.checkbox("Show all logs in this folder")
    if show_all_logs:
        # Initialize pagination offset in session state if not set
        if "all_logs_offset" not in st.session_state:
            st.session_state.all_logs_offset = 0

        selected_log_level_all = st.selectbox("Select Log Level for All Logs", ["All", "Fatal", "Error", "Warn", "Info", "Debug", "Trace", "Verbose"], key="all_logs_level")
        page_size_all = st.selectbox("Logs per page for All Logs", [25, 50, 100], key="all_logs_page_size")

        all_logs = api_get("RobotLogs", folder_id=folder_id).get("value", [])

        # Filter by log level if needed
        if selected_log_level_all != "All":
            filtered_logs = [log for log in all_logs if log["Level"] == selected_log_level_all]
        else:
            filtered_logs = all_logs

        # Pagination
        paged_logs_all = filtered_logs[st.session_state.all_logs_offset : st.session_state.all_logs_offset + page_size_all]

        # Display logs
        if paged_logs_all:
            for log in paged_logs_all:
                log_color = get_color_for_log_level(log["Level"])
                st.markdown(
                    f"<div style='color:{log_color}; font-size:15px;'>"
                    f"[{log['TimeStamp']}] {log['Level']} - {log['Message']}</div>",
                    unsafe_allow_html=True
                )

            if st.button("Load More Logs (All Logs)"):
                st.session_state.all_logs_offset += page_size_all
                st.rerun()

            # Prepare logs text for download
            log_text_all = "\n".join([f"[{log['TimeStamp']}] {log['Level']} - {log['Message']}" for log in filtered_logs])

            # Create dataframe for download
            df_all_logs = pd.DataFrame(filtered_logs)

            file_format_all = st.selectbox("Choose download format for All Logs", ["TXT", "CSV", "XLSX"], key="all_logs_download_format")

            if file_format_all == "TXT":
                file_data_all = log_text_all
                mime_type_all = "text/plain"
                file_name_all = "uipath_all_logs.txt"
            elif file_format_all == "CSV":
                file_data_all = df_all_logs.to_csv(index=False)
                mime_type_all = "text/csv"
                file_name_all = "uipath_all_logs.csv"
            elif file_format_all == "XLSX":
                buffer_all = BytesIO()
                df_all_logs.to_excel(buffer_all, index=False)
                buffer_all.seek(0)
                file_data_all = buffer_all
                mime_type_all = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                file_name_all = "uipath_all_logs.xlsx"

            b64_all = base64.b64encode(file_data_all.encode() if file_format_all != "XLSX" else file_data_all.read()).decode()
            if file_format_all == "XLSX":
                file_data_all.seek(0)

            st.markdown(f"""
                <div style="text-align: right; margin-top: 20px;">
                    <a href="data:{mime_type_all};base64,{b64_all}" download="{file_name_all}">
                        <button style="background-color: #4CAF50; color: white; padding: 10px 20px;
                                       border: none; border-radius: 5px; cursor: pointer;">
                            📥 Download All Logs as {file_format_all}
                        </button>
                    </a>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("No logs found for the selected filters.")
