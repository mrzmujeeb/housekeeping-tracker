import streamlit as st
import pandas as pd
import datetime
import os
import json

EXCEL_FILE = "Housekeeping_Daily_Log.xlsx"
STATUS_FILE = "lock_status.json"

# Set page layout to wide
st.set_page_config(page_title="Housekeeping Tracker", layout="wide")

# User Authentication Database
USER_CREDENTIALS = {
    "ramesh": "ramesh",
    "admin": "admin"
}

# Initialize authentication state in session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None

# Function to check if today is locked
def is_today_locked(today_str):
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r") as f:
                data = json.load(f)
                return data.get(today_str, False)
        except Exception:
            return False
    return False

# Function to mark today as locked
def lock_today(today_str):
    data = {}
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
    data[today_str] = True
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f)

# Function to unlock today
def unlock_today(today_str):
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r") as f:
                data = json.load(f)
            data[today_str] = False
            with open(STATUS_FILE, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

# LOGIN PAGE LOGIC
if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center;'>🔐 Housekeeping Login</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button("Login", use_container_width=True, type="primary")
            
            if login_submitted:
                user_key = username_input.strip().lower()
                if user_key in USER_CREDENTIALS and USER_CREDENTIALS[user_key] == password_input:
                    st.session_state.authenticated = True
                    st.session_state.username = user_key
                    st.success(f"Welcome, {username_input}!")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
    st.stop()  # Halt execution until authenticated

# MAIN APPLICATION (AUTHENTICATED)
current_user = st.session_state.username
is_admin = (current_user == "admin")

# Sidebar Logout & Role Info
st.sidebar.markdown(f"**Logged in as:** `{current_user.upper()}`")
if is_admin:
    st.sidebar.success("👑 Admin Mode Active")
if st.sidebar.button("Logout", type="secondary"):
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()

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

# Centered Title
st.markdown(
    "<h1 style='text-align: center;'>🧹 Housekeeping Task Management</h1>", 
    unsafe_allow_html=True
)

# Load existing data
if os.path.exists(EXCEL_FILE):
    df = pd.read_excel(EXCEL_FILE)
else:
    df = pd.DataFrame(columns=["Sl. No", "Date", "Day", "Task Name", "Status", "Timestamp", "Logged By"])

# Date Selection (Locked strictly to today)
today = datetime.date.today()
formatted_date = today.strftime("%d-%m-%Y")
formatted_day = today.strftime("%A")

# Check persistent lock status for today
is_locked = is_today_locked(formatted_date)

selected_date = st.date_input(
    "Select Date", 
    value=today,
    min_value=today,
    max_value=today,
    disabled=True
)

st.subheader(f"Tasks for {formatted_date} ({formatted_day})")

# Form with 3-Column Layout
# Form inputs are disabled for non-admins if locked
form_disabled = is_locked and not is_admin

with st.form("task_form"):
    task_responses = {}
    
    col1, col2, col3 = st.columns(3)

    # Left Column
    with col1:
        st.markdown("### 🚪 Chairperson Area")
        for task in LEFT_TASKS:
            task_responses[task["name"]] = st.selectbox(
                f"{task['name']}",
                task["options"],
                disabled=form_disabled
            )

    # Center Column
    with col2:
        st.markdown("### 🏢 Office & Staff")
        for task in CENTER_TASKS:
            task_responses[task["name"]] = st.selectbox(
                f"{task['name']}",
                task["options"],
                disabled=form_disabled
            )

    # Right Column
    with col3:
        st.markdown("### 🚪 Scanning & Services")
        for task in RIGHT_TASKS:
            task_responses[task["name"]] = st.selectbox(
                f"{task['name']}",
                task["options"],
                disabled=form_disabled
            )

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Dual buttons inside form
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        submitted = st.form_submit_button("Save Current Selection", use_container_width=True, disabled=form_disabled)
    with btn_col2:
        confirm_submitted = st.form_submit_button("✅ CONFIRM ALL TASKS", type="primary", use_container_width=True, disabled=form_disabled)

# Handle Data Saving
if (submitted or confirm_submitted) and not form_disabled:
    timestamp = datetime.datetime.now().strftime("%I:%M:%S %p")
    new_rows = []
    
    for task_name, status in task_responses.items():
        sl_no = len(df) + 1
        new_rows.append({
            "Sl. No": sl_no,
            "Date": formatted_date,
            "Day": formatted_day,
            "Task Name": task_name,
            "Status": status,
            "Timestamp": timestamp,
            "Logged By": current_user
        })
    
    df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    df.to_excel(EXCEL_FILE, index=False)
    
    if confirm_submitted:
        lock_today(formatted_date)
        st.success("Tasks confirmed and locked!")
    else:
        st.success("Tasks saved successfully!")
    
    st.rerun()

# Log View Header & Admin Control Actions
if is_admin:
    col_header, col_unlock, col_reset = st.columns([3, 1, 1])
    with col_header:
        st.subheader("Task History")
    
    with col_unlock:
        if st.button("🔓 Unlock Today", type="secondary", use_container_width=True, disabled=not is_locked):
            unlock_today(formatted_date)
            st.success("Unlocked today's log for all users!")
            st.rerun()
            
    with col_reset:
        if st.button("🗑️ Reset All History", type="secondary", use_container_width=True):
            if os.path.exists(EXCEL_FILE):
                os.remove(EXCEL_FILE)
            unlock_today(formatted_date)
            st.success("Task history cleared & unlocked!")
            st.rerun()
else:
    st.subheader("Task History")

if is_locked:
    if is_admin:
        st.warning("🔒 Tasks are currently locked for regular users. As Admin, you can click '🔓 Unlock Today' or '🗑️ Reset All History' above to restore access.")
    else:
        st.info("🔒 Tasks have been confirmed for today. Reset and form editing are locked for your account.")

# Display Task History Table
st.dataframe(df, width="stretch")
