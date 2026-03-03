import streamlit as st
import hashlib
import time
import pandas as pd

# =====================================================
# SESSION INIT
# =====================================================

if "blockchain" not in st.session_state:
    st.session_state.blockchain = []

if "scan_logs" not in st.session_state:
    st.session_state.scan_logs = {}

if "users" not in st.session_state:
    st.session_state.users = {}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current_user" not in st.session_state:
    st.session_state.current_user = None

# =====================================================
# FUNCTIONS
# =====================================================

def generate_hash(data):
    return hashlib.sha256(data.encode()).hexdigest()

def add_block(hallmark_id, purity, city, status):
    previous_hash = st.session_state.blockchain[-1]["block_hash"] if st.session_state.blockchain else "0"
    data_string = f"{hallmark_id}|{purity}|{city}|{status}"
    block_hash = generate_hash(data_string + previous_hash)

    block = {
        "index": len(st.session_state.blockchain) + 1,
        "hallmark_id": hallmark_id,
        "purity": purity,
        "city": city,
        "status": status,
        "previous_hash": previous_hash,
        "block_hash": block_hash
    }

    st.session_state.blockchain.append(block)
    return block

# =====================================================
# UI
# =====================================================

st.set_page_config(page_title="BIS ChainVerify", layout="wide")
st.title("🔐 BIS Blockchain Hallmark Verification System")

# =====================================================
# AUTH PANEL
# =====================================================

st.sidebar.title("🔐 Authentication")
auth_option = st.sidebar.radio("Select Option", ["Consumer", "BIS Register", "BIS Login"])

# -------- REGISTER --------
if auth_option == "BIS Register":

    username = st.sidebar.text_input("Create Username")
    password = st.sidebar.text_input("Create Password", type="password")

    if st.sidebar.button("Register"):
        if username and password:
            if username in st.session_state.users:
                st.sidebar.warning("User already exists")
            else:
                st.session_state.users[username] = password
                st.sidebar.success("Registered Successfully. Please Login.")
        else:
            st.sidebar.warning("Enter Username & Password")

# -------- LOGIN --------
elif auth_option == "BIS Login":

    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if username in st.session_state.users and st.session_state.users[username] == password:
            st.session_state.logged_in = True
            st.session_state.current_user = username
            st.sidebar.success(f"Welcome {username}")
        else:
            st.sidebar.error("Invalid Credentials")

# -------- LOGOUT --------
if st.session_state.logged_in:
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.sidebar.success("Logged Out")

# =====================================================
# BIS DASHBOARD
# =====================================================

if st.session_state.logged_in:

    st.header("🏛 BIS Hallmark Registration Dashboard")

    hallmark_id = st.text_input("Hallmark ID")
    purity = st.text_input("Purity (e.g., 22K916)")
    city = st.text_input("Assay Center City")
    status_option = st.selectbox("Status", ["Active", "Revoked", "Suspicious"])

    if st.button("Submit"):

        if hallmark_id and purity and city:

            existing_block = None
            for block in reversed(st.session_state.blockchain):
                if block["hallmark_id"] == hallmark_id:
                    existing_block = block
                    break

            if existing_block is None:
                block = add_block(hallmark_id, purity, city, status_option)
                st.session_state.scan_logs[hallmark_id] = []
                st.success("✅ New Hallmark Registered")

            else:
                if existing_block["status"] == status_option:
                    st.info("ℹ Same Status Already Exists. No Update Needed.")
                else:
                    block = add_block(
                        hallmark_id,
                        existing_block["purity"],
                        existing_block["city"],
                        status_option
                    )
                    st.success("🔄 Status Updated Successfully")

        else:
            st.warning("Please enter Hallmark ID, Purity and City")

# =====================================================
# CONSUMER DASHBOARD (CLEAN VIEW)
# =====================================================

if not st.session_state.logged_in:

    st.header("👤 Consumer Verification Panel")

    scan_id = st.text_input("Enter Hallmark ID")
    location = st.text_input("Enter Your City")

    if st.button("Verify"):

        block_found = None
        for block in reversed(st.session_state.blockchain):
            if block["hallmark_id"] == scan_id:
                block_found = block
                break

        if block_found:

            st.session_state.scan_logs.setdefault(scan_id, []).append({
                "time": time.time(),
                "location": location
            })

            scan_count = len(st.session_state.scan_logs[scan_id])
            locations = [log["location"] for log in st.session_state.scan_logs[scan_id]]

            risk_score = 0
            if scan_count > 3:
                risk_score += 30
            if len(set(locations)) > 1:
                risk_score += 40

            # STATUS CHECK
            if block_found["status"] != "Active":
                st.warning(f"⚠ Hallmark Status: {block_found['status']}")

            elif risk_score >= 40:
                st.warning("⚠ Suspicious Scan Activity Detected")

            else:
                st.success("✅ Genuine & Active Hallmark")

                st.markdown("### 🏅 Hallmark Certificate Details")
                st.write("**Hallmark ID:**", block_found["hallmark_id"])
                st.write("**Purity:**", block_found["purity"])
                st.write("**Assay Center City:**", block_found["city"])
                st.write("**Current Status:**", block_found["status"])

        else:
            st.error("❌ Hallmark Not Found")

# =====================================================
# BLOCKCHAIN EXPLORER (ADMIN ONLY)
# =====================================================

if st.session_state.logged_in:

    st.markdown("---")
    st.header("📦 Blockchain Explorer (Admin View)")

    if st.session_state.blockchain:
        df = pd.DataFrame(st.session_state.blockchain)
        st.dataframe(df)
    else:
        st.write("No Blocks Yet")