# app.py
import streamlit as st
import pandas as pd
from pathlib import Path
import shutil
from datetime import datetime
from utils import calculate_points

# Paths
BASE_DIR = Path("D:\Projects\Elle_score_analyzer")
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = DATA_DIR / "match_logs"
MASTER_FILE = DATA_DIR / "players_master.csv"
LEADERBOARD_FILE = DATA_DIR / "leaderboard.csv"

# Ensure data folders exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="Elle Tournament Tracker", layout="wide")
st.title("🥎 Elle Tournament - Match Uploader & Leaderboard")

# Undo/Redo state
if "undo_stack" not in st.session_state:
    st.session_state.undo_stack = []
if "redo_stack" not in st.session_state:
    st.session_state.redo_stack = []

# Save a snapshot
def save_snapshot():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    snapshot_path = DATA_DIR / f"players_master_snapshot_{timestamp}.csv"
    shutil.copy(MASTER_FILE, snapshot_path)
    st.session_state.undo_stack.append(snapshot_path)
    st.session_state.redo_stack.clear()

# Upload match CSV
uploaded_file = st.file_uploader("Upload Match CSV", type="csv")

if uploaded_file:
    match_df = pd.read_csv(uploaded_file)
    match_id = match_df["Match ID"].iloc[0]

    match_path = LOGS_DIR / f"{match_id}.csv"
    match_df.to_csv(match_path, index=False)

    master_df = pd.read_csv(MASTER_FILE)
    save_snapshot()

    updated_df = calculate_points(match_df, master_df)
    updated_df.to_csv(MASTER_FILE, index=False)

    leaderboard = updated_df.sort_values(by="Total Points", ascending=False)
    leaderboard.to_csv(LEADERBOARD_FILE, index=False)

    st.success(f"✅ Match {match_id} uploaded and points updated!")

spacer1, buttons_col, spacer2 = st.columns([4, 3, 4])

with buttons_col:
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        reset = st.button("🔄 Reset")

    with col2:
        undo = st.button("⬅️ Undo")

    with col3:
        redo = st.button("➡️ Redo")


if reset:
    if MASTER_FILE.exists():
        save_snapshot()
        master_df = pd.read_csv(MASTER_FILE)
        master_df["Total Points"] = 0
        master_df.to_csv(MASTER_FILE, index=False)
        st.success("All players' points have been reset.")
    else:
        st.warning("players_master.csv not found.")

if undo:
    if st.session_state.undo_stack:
        last_snapshot = st.session_state.undo_stack.pop()
        redo_path = DATA_DIR / f"redo_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.csv"
        shutil.copy(MASTER_FILE, redo_path)
        st.session_state.redo_stack.append(redo_path)
        shutil.copy(last_snapshot, MASTER_FILE)
        st.success("Undo performed.")
    else:
        st.warning("Nothing to undo.")

if redo:
    if st.session_state.redo_stack:
        next_snapshot = st.session_state.redo_stack.pop()
        undo_path = DATA_DIR / f"undo_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.csv"
        shutil.copy(MASTER_FILE, undo_path)
        st.session_state.undo_stack.append(undo_path)
        shutil.copy(next_snapshot, MASTER_FILE)
        st.success("Redo performed.")
    else:
        st.warning("Nothing to redo.")


# Leaderboard
if MASTER_FILE.exists():
    df = pd.read_csv(MASTER_FILE)
    top5 = df.sort_values(by="Total Points", ascending=False).head(5)
    st.subheader("🏆 Top 5 Players")
    st.dataframe(top5)
else:
    st.warning("Upload players_master.csv to begin tracking.")
