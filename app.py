# app.py
import streamlit as st
import pandas as pd
from pathlib import Path
import shutil
from datetime import datetime
from utils import calculate_points

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = DATA_DIR / "match_logs"
MASTER_FILE = DATA_DIR / "players_master.csv"
LEADERBOARD_FILE = DATA_DIR / "leaderboard.csv"
UPLOADED_MATCHES_FILE = DATA_DIR / "uploaded_matches.csv"

# Ensure folders exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Initialize uploaded_matches.csv if not present
if not UPLOADED_MATCHES_FILE.exists():
    pd.DataFrame(columns=["Match ID", "Timestamp"]).to_csv(UPLOADED_MATCHES_FILE, index=False)

# Streamlit setup
st.set_page_config(page_title="Elle Tournament Tracker", layout="wide")
st.title("🥎 Elle Tournament - Match Uploader & Leaderboard")

# Undo/Redo state
if "undo_stack" not in st.session_state:
    st.session_state.undo_stack = []
if "redo_stack" not in st.session_state:
    st.session_state.redo_stack = []

def save_snapshot():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    snapshot = DATA_DIR / f"players_master_snapshot_{timestamp}.csv"
    if MASTER_FILE.exists():
        shutil.copy(MASTER_FILE, snapshot)
        st.session_state.undo_stack.append(snapshot)
        st.session_state.redo_stack.clear()

# Upload match
uploaded_file = st.file_uploader("Upload Match CSV", type="csv")

if uploaded_file:
    match_df = pd.read_csv(uploaded_file)
    match_id = match_df["Match ID"].iloc[0]

    # Read uploaded match log safely
    if UPLOADED_MATCHES_FILE.stat().st_size > 0:
        uploaded_matches_df = pd.read_csv(UPLOADED_MATCHES_FILE)
    else:
        uploaded_matches_df = pd.DataFrame(columns=["Match ID", "Timestamp"])

    if match_id in uploaded_matches_df["Match ID"].values:
        st.warning(f"⚠️ Match {match_id} already uploaded.")
    else:
        # Save match ID only, not the file itself
        new_row = pd.DataFrame([{
            "Match ID": match_id,
            "Timestamp": datetime.now().isoformat()
        }])
        uploaded_matches_df = pd.concat([uploaded_matches_df, new_row], ignore_index=True)
        uploaded_matches_df.to_csv(UPLOADED_MATCHES_FILE, index=False)
        st.success(f"✅ Match {match_id} logged.")

        # Process points
        if MASTER_FILE.exists():
            master_df = pd.read_csv(MASTER_FILE)
            save_snapshot()
            updated_df = calculate_points(match_df, master_df)
            updated_df.to_csv(MASTER_FILE, index=False)

            leaderboard = updated_df.sort_values(by="Total Points", ascending=False)
            leaderboard.to_csv(LEADERBOARD_FILE, index=False)
            st.success("✅ Player points updated and leaderboard refreshed.")
        else:
            st.warning("⚠️ players_master.csv not found. Please upload it in data folder.")

# Controls
spacer1, center_col, spacer2 = st.columns([4, 3, 4])
with center_col:
    col1, col2, col3 = st.columns(3)
    with col1:
        reset = st.button("🔄 Reset")
    with col2:
        undo = st.button("⬅️ Undo")
    with col3:
        redo = st.button("➡️ Redo")

if reset and MASTER_FILE.exists():
    save_snapshot()
    df = pd.read_csv(MASTER_FILE)
    df["Total Points"] = 0
    df.to_csv(MASTER_FILE, index=False)
    st.success("🔄 All player points reset.")

if undo and st.session_state.undo_stack:
    last = st.session_state.undo_stack.pop()
    redo_path = DATA_DIR / f"redo_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.csv"
    shutil.copy(MASTER_FILE, redo_path)
    st.session_state.redo_stack.append(redo_path)
    shutil.copy(last, MASTER_FILE)
    st.success("⬅️ Undo complete.")

if redo and st.session_state.redo_stack:
    next_ = st.session_state.redo_stack.pop()
    undo_path = DATA_DIR / f"undo_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.csv"
    shutil.copy(MASTER_FILE, undo_path)
    st.session_state.undo_stack.append(undo_path)
    shutil.copy(next_, MASTER_FILE)
    st.success("➡️ Redo complete.")

# Leaderboard
if MASTER_FILE.exists():
    df = pd.read_csv(MASTER_FILE)
    top5 = df.sort_values(by="Total Points", ascending=False).head(5)
    st.subheader("🏆 Top 5 Players")
    st.dataframe(top5)
else:
    st.warning("No player data found. Please upload players_master.csv.")

# Uploaded match list
if UPLOADED_MATCHES_FILE.exists() and UPLOADED_MATCHES_FILE.stat().st_size > 0:
    st.subheader("📋 Uploaded Matches")
    uploaded_log_df = pd.read_csv(UPLOADED_MATCHES_FILE)
    st.dataframe(uploaded_log_df)
