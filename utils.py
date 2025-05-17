# utils.py
import pandas as pd

def calculate_points(match_df, master_df):
    weights = {
        "Score": 1,
        "Runner Rounds": 2,
        "Runout (F)": 7,
        "Catch": 5,
        "Assist": 3,
        "Errors": -2,
        "Runout (R)": -3,
    }

    match_df["Match Points"] = (
        match_df["Score"] * weights["Score"] +
        match_df["Runner Rounds"] * weights["Runner Rounds"] +
        match_df["Runout (F)"] * weights["Runout (F)"] +
        match_df["Catch"] * weights["Catch"] +
        match_df["Assist"] * weights["Assist"] +
        match_df["Errors"] * weights["Errors"] +
        match_df["Runout (R)"] * weights["Runout (R)"]
    )

    for _, row in match_df.iterrows():
        jno = row["Jersey No"]
        reg = row["Reg No"]
        points = row["Match Points"]

        mask = (master_df["Jersey No"] == jno) & (master_df["Reg No"] == reg)
        master_df.loc[mask, "Total Points"] += points

    return master_df
