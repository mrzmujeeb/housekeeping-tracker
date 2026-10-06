import streamlit as st
import pandas as pd
import datetime
import os

EXCEL_FILE = "Housekeeping_Daily_Log.xlsx"

# Grouping tasks logically into 3 sections
LEFT_TASKS = [
    {"name": "Chairperson Room Door", "options": ["Closed", "Open"]},
    {"name": "Chairperson Room Inside Light", "options": ["OFF", "ON"]},
    {"name": "Chairperson Room Outside Light", "options": ["OFF", "ON"]},
    {"name": "Chairperson Room Setback Area Light", "options": ["OFF", "ON"]},
]

CENTER_TASKS = [
    {"name": "Office Room", "options": ["Locked", "Open"]},
    {"name": "Office Room Lights", "options": ["OFF", "ON"]},
    {"name": "Staff Room", "options": ["Locked", "Open"]},
    {"name": "Staff Room Lights", "options": ["OFF", "ON"]},
]

RIGHT_TASKS = [
    {"name": "Scanning Room", "options": ["Locked", "Open"]},
    {"name": "Scanning Room Lights", "options": ["OFF", "ON"]},
    {"name": "Bathroom - Lights", "options": ["OFF", "ON"]},
    {"name": "Colapsable Door to SCN", "options": ["OPEN", "LOCKED"]},
]

# Set page layout to wide for better 3-column spacing on desktop/tablet
st.set_page_config(page_title="Housekeeping Tracker", layout="wide")

# Centered Title
st.markdown(
    "<h1 style='text-align: center;'>🧹 Housekeeping Task Management</h1>", 
    unsafe_allow_html=True
)

# Load existing data
if os.path.exists(EXCEL_FILE):
    df = pd.read_excel(EXCEL_FILE)
else:
    df = pd.DataFrame(columns=["Sl. No", "Date", "Day", "Task Name", "Status", "Timestamp"])

# Date Selection (Locked strictly to today)
today = datetime.date.today()
selected_date = st.date_input(
    "Select Date", 
    value=today,
    min_value=today,
    max_value=today,
    disabled=True
)
formatted_date = selected_date.strftime("%d-%m-%Y")
formatted_day = selected_date.strftime("%A")

st.subheader(f"Tasks for {formatted_date} ({formatted_day})")

# Form with 3-Column Layout
with st.form("task_form"):
    task_responses = {}
    
    col1, col2, col3 = st.columns(3)

    # Left Column
    with col1:
        st.markdown("### 🚪 Chairperson Area")
        for task in LEFT_TASKS:
            task_responses[task["name"]] = st.selectbox(
                f"{task['name']}",
                task["options"]
            )

    # Center Column
    with col2:
        st.markdown("### 🏢 Office & Staff")
        for task in CENTER_TASKS:
            task_responses[task["name"]] = st.selectbox(
                f"{task['name']}",
                task["options"]
            )

    # Right Column
    with col3:
        st.markdown("### 🚪 Scanning & Services")
        for task in RIGHT_TASKS:
            task_responses[task["name"]] = st.selectbox(
                f"{task['name']}",
                task["options"]
            )

    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button("Submit All Tasks", use_container_width=True)

if submitted:
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    new_rows = []
    
    for task_name, status in task_responses.items():
        sl_no = len(df) + 1
        new_rows.append({
            "Sl. No": sl_no,
            "Date": formatted_date,
            "Day": formatted_day,
            "Task Name": task_name,
            "Status": status,
            "Timestamp": timestamp
        })
    
    df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    df.to_excel(EXCEL_FILE, index=False)
    st.success("All tasks saved successfully!")

# Log View
st.subheader("Task History")
st.dataframe(df, width="stretch")