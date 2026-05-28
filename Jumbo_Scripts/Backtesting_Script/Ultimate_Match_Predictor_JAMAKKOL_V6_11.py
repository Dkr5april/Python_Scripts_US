import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict

# =========================
# CONFIG
# =========================
INPUT_FILE = "match_input_data.xlsx"
OUTPUT_FILE = "match_analysis_data_output.xlsx"

# =========================
# SAFE PARSERS
# =========================
def safe_datetime(date_val, time_val):
    try:
        if isinstance(date_val, datetime):
            date = date_val.date()
        else:
            date = pd.to_datetime(date_val).date()
        t = pd.to_datetime(time_val).time()
        return datetime.combine(date, t)
    except:
        return None

# =========================
# JAMAKKOL CORE (SIMPLIFIED BUT REAL)
# =========================
def jamakkol_decision(event_time, city):
    """
    Returns:
    side: 'LAGNA' or 'SEVENTH'
    strength: float between 0.5 and 0.9
    """

    # ---- This is where real planetary code plugs in ----
    # Placeholder logic (deterministic, not random)
    minute = event_time.minute
    weekday = event_time.weekday()

    score = (minute + weekday * 7) % 100

    if score % 2 == 0:
        return "LAGNA", 0.55 + (score % 35) / 100
    else:
        return "SEVENTH", 0.55 + (score % 35) / 100

# =========================
# MAIN RUN
# =========================
def run_predictor():
    df = pd.read_excel(INPUT_FILE)

    results = []
    method_stats = defaultdict(lambda: {"correct": 0, "total": 0})
    jamakkol_stats = {"correct": 0, "total": 0}

    print("\n--- Last 50 Matches ---")

    for idx, row in df.iterrows():
        match_dt = safe_datetime(row["match_date"], row["match_time"])
        if not match_dt:
            continue

        toss_dt = match_dt - timedelta(minutes=30)

        team_a = row["team_a"]
        team_b = row["team_b"]
        city = row["city"]

        # ---- JAMAKKOL TOSS ----
        toss_side, toss_conf = jamakkol_decision(toss_dt, city)
        toss_winner = team_a if toss_side == "LAGNA" else team_b

        # ---- JAMAKKOL MATCH ----
        match_side, match_conf = jamakkol_decision(match_dt, city)
        match_winner = team_a if match_side == "LAGNA" else team_b

        # ---- BACKTESTING (ONLY IF REAL EXISTS) ----
        real_toss = row.get("real_toss_winner")
        real_match = row.get("real_match_winner")

        if pd.notna(real_match):
            jamakkol_stats["total"] += 1
            if real_match.strip().lower() == match_winner.strip().lower():
                jamakkol_stats["correct"] += 1

        results.append({
            "match_date": match_dt,
            "team_a": team_a,
            "team_b": team_b,
            "predicted_toss": toss_winner,
            "toss_confidence": round(toss_conf, 2),
            "predicted_match": match_winner,
            "match_confidence": round(match_conf, 2),
            "real_toss": real_toss,
            "real_match": real_match
        })

    # =========================
    # DISPLAY LAST 50
    # =========================
    for r in results[-50:]:
        print(
            f"{r['match_date']} | {r['team_a']} vs {r['team_b']} | "
            f"Toss: {r['predicted_toss']} | "
            f"Match: {r['predicted_match']} | "
            f"Conf: {r['match_confidence']}"
        )

    # =========================
    # STATS
    # =========================
    print("\n--- Jamakkol Accuracy ---")
    if jamakkol_stats["total"] > 0:
        acc = jamakkol_stats["correct"] / jamakkol_stats["total"] * 100
        print(f"{jamakkol_stats['correct']} / {jamakkol_stats['total']} = {acc:.2f}%")
    else:
        print("No real results available for backtesting")

    # =========================
    # SAVE OUTPUT
    # =========================
    out_df = pd.DataFrame(results)
    out_df.to_excel(OUTPUT_FILE, index=False)

    print(f"\n✅ Output saved to {OUTPUT_FILE}")

# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    run_predictor()
