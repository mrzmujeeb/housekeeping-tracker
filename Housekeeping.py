import streamlit as st
import pandas as pd
import datetime
import os
import json
from zoneinfo import ZoneInfo
from twilio.rest import Client

EXCEL_FILE = "Housekeeping_Daily_Log.xlsx"
STATUS_FILE = "lock_status.json"

# Define IST Timezone
IST = ZoneInfo("Asia/Kolkata")

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

# Function to send direct WhatsApp message via Twilio
def send_whatsapp_report(date_str, user_name, task_data):
    try:
        account_sid = st.secrets["TWILIO_ACCOUNT_SID"]
        auth_token = st.secrets["TWILIO_AUTH_TOKEN"]
        twilio_number = st.secrets["TWILIO_WHATSAPP_NUMBER"]  # e.g., "whatsapp:+17372508034"
        target_number = st.secrets["MY_WHATSAPP_NUMBER"]      # e.g., "whatsapp:+919611676450"

        client = Client(account_sid, auth_token)

        # Build clean formatted report body
        report_lines = [f"🧹 *Housekeeping Log Report*", f"📅 *Date:* {date_str}", f"👤 *Logged By:* {user_name}", ""]
        for _, row in task_data.iterrows():
            report_lines.append(f"• {row['Task Name']}: *{row['Status']}*")
            
        message_body = "\n".join(report_lines)

        # Send direct text message
        message = client.messages.create(
            from_=twilio_number,
            to=target_number,
            body=message_body
        )
        return True, message.sid
    except Exception as e:
        return False, str(e)

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
    st.stop()

# MAIN APPLICATION (AUTHENTICATED)
current_user = st.session_state.username
is_admin = (current_user == "admin")

st.sidebar.markdown(f"**Logged in as:** `{current_user.upper()}`")
if is_admin:
    st.sidebar.success("👑 Admin Mode Active")
if st.sidebar.button("Logout", type="secondary"):
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()

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

st.markdown(
    "<h1 style='text-align: center;'>🧹 Housekeeping Task Management</h1>", 
    unsafe_allow_html=True
)

if os.path.exists(EXCEL_FILE):
    df = pd.read_excel(EXCEL_FILE)
else:
    df = pd.DataFrame(columns=["Sl. No", "Date", "Day", "Task Name", "Status", "Timestamp", "Logged By"])

now_ist = datetime.datetime.now(IST)
today = now_ist.date()
formatted_date = today.strftime("%d-%m-%Y")
formatted_day = today.strftime("%A")

is_locked = is_today_locked(formatted_date)

# Fetch current defaults for today if previously saved
today_existing = df[df["Date"] == formatted_date] if not df.empty else pd.DataFrame()
saved_defaults = {}
if not today_existing.empty:
    saved_defaults = dict(zip(today_existing["Task Name"], today_existing["Status"]))

selected_date = st.date_input(
    "Select Date", 
    value=today,
    min_value=today,
    max_value=today,
    disabled=True
)

st.subheader(f"Tasks for {formatted_date} ({formatted_day})")

form_disabled = is_locked and not is_admin

with st.form("task_form"):
    task_responses = {}
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🚪 Chairperson Area")
        for task in LEFT_TASKS:
            default_val = saved_defaults.get(task["name"], task["options"][0])
            idx = task["options"].index(default_val) if default_val in task["options"] else 0
            task_responses[task["name"]] = st.selectbox(
                f"{task['name']}",
                task["options"],
                index=idx,
                disabled=form_disabled
            )

    with col2:
        st.markdown("### 🏢 Office & Staff")
        for task in CENTER_TASKS:
            default_val = saved_defaults.get(task["name"], task["options"][0])
            idx = task["options"].index(default_val) if default_val in task["options"] else 0
            task_responses[task["name"]] = st.selectbox(
                f"{task['name']}",
                task["options"],
                index=idx,
                disabled=form_disabled
            )

    with col3:
        st.markdown("### 🚪 Scanning & Services")
        for task in RIGHT_TASKS:
            default_val = saved_defaults.get(task["name"], task["options"][0])
            idx = task["options"].index(default_val) if default_val in task["options"] else 0
            task_responses[task["name"]] = st.selectbox(
                f"{task['name']}",
                task["options"],
                index=idx,
                disabled=form_disabled
            )

    st.markdown("<br>", unsafe_allow_html=True)
    
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        submitted = st.form_submit_button("Save Current Selection", use_container_width=True, disabled=form_disabled)
    with btn_col2:
        confirm_submitted = st.form_submit_button("✅ CONFIRM ALL TASKS", type="primary", use_container_width=True, disabled=form_disabled)

if (submitted or confirm_submitted) and not form_disabled:
    ist_time = datetime.datetime.now(IST)
    timestamp = ist_time.strftime("%I:%M:%S %p")
    
    # Remove existing entries for today to avoid duplicate accumulation
    if not df.empty:
        df = df[df["Date"] != formatted_date]
        
    new_rows = []
    for task_name, status in task_responses.items():
        sl_no = len(df) + 1 + len(new_rows)
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
        todays_log = pd.DataFrame(new_rows)
        
        # WhatsApp message is ONLY sent if the logged-in user is 'admin'
        if is_admin:
            success, msg = send_whatsapp_report(formatted_date, current_user, todays_log)
            if success:
                st.success("📲 Tasks confirmed & locked! WhatsApp report sent successfully.")
                st.rerun()
            else:
                st.error(f"Tasks saved & locked, BUT WhatsApp failed: {msg}")
        else:
            st.success("📲 Tasks confirmed & locked successfully! (WhatsApp report restricted to Admin)")
            st.rerun()
    else:
        st.success("Tasks saved successfully!")
        st.rerun()

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
        st.warning("🔒 Tasks are currently locked for regular users.")
    else:
        st.info("Tasks have been confirmed for today.")

st.dataframe(df, use_container_width=True)
