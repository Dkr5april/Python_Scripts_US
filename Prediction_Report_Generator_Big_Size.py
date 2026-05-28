#!/usr/bin/env python3
"""
ENHANCED PREDICTION REPORT GENERATOR
Bright & Bold Console Version
Reads 'match_analysis_data.xlsx' and generates
a visually stronger, detailed report for match predictions.
"""

import pandas as pd
import sys
from collections import Counter

# ------------------------------
# FIX FOR WINDOWS JUNK CHARACTERS
# ------------------------------
try:
    import colorama
    colorama.init(autoreset=True)
except:
    pass

# ANSI Color Codes
class Colors:
    HEADER = '\033[95;1m'    # Bright Magenta Bold
    OKBLUE = '\033[94;1m'    # Bright Blue Bold
    OKGREEN = '\033[92;1m'   # Bright Green Bold
    WARNING = '\033[93;1m'   # Bright Yellow Bold
    FAIL = '\033[91;1m'      # Bright Red Bold
    BOLD = '\033[1m'
    ENDC = '\033[0m'
    GRAY = '\033[90;1m'


def colorize_prediction(text):
    text_upper = text.upper()
    if 'A (' in text_upper or 'TEAM A' in text_upper:
        return f"{Colors.OKBLUE}{text}{Colors.ENDC}"
    if 'B (' in text_upper or 'TEAM B' in text_upper:
        return f"{Colors.OKGREEN}{text}{Colors.ENDC}"
    return f"{Colors.WARNING}{text}{Colors.ENDC}"


def parse_row_selection(user_input, max_row):
    user_input = user_input.strip().lower()
    if user_input == "all" or user_input == "":
        return list(range(1, max_row + 1))
    rows = set()
    parts = user_input.split(",")
    for part in parts:
        if "-" in part:
            start, end = part.split("-")
            try:
                start, end = int(start), int(end)
                for r in range(start, end + 1):
                    if 1 <= r <= max_row:
                        rows.add(r)
            except:
                pass
        else:
            try:
                num = int(part)
                if 1 <= num <= max_row:
                    rows.add(num)
            except:
                pass
    return sorted(rows)


def generate_report():
    # --------------------------------
    # HEADER
    # --------------------------------
    print(f"\n{Colors.HEADER}{'='*80}")
    print(f"{Colors.HEADER}{Colors.BOLD}===  🌟 FULL ASTRO-NUMEROLOGY PREDICTION REPORT CARD 🌟  ===")
    print(f"{Colors.HEADER}{'='*80}\n")

    IO_FILE = "match_analysis_data.xlsx"
    TOSS_METHOD_COLS = [f'Toss_Method_{i}_Numerology' for i in range(1, 6)]

    # --------------------------------
    # LOAD EXCEL
    # --------------------------------
    try:
        df = pd.read_excel(IO_FILE)
    except FileNotFoundError:
        print(f"{Colors.FAIL}FATAL ERROR: Input file '{IO_FILE}' not found.{Colors.ENDC}")
        sys.exit(1)

    if df.empty:
        print(f"{Colors.WARNING}The Excel file is empty.{Colors.ENDC}")
        return

    # -----------------------------------
    # ROW SELECTION
    # -----------------------------------
    total_rows = len(df)
    print(f"{Colors.OKBLUE}Total Matches Available: {total_rows}{Colors.ENDC}")
    print(f"{Colors.GRAY}Enter rows like: 1,3,5 or 2-6 or all{Colors.ENDC}")

    selected_input = input(f"{Colors.BOLD}Select match rows to include: {Colors.ENDC}")
    selected_rows = parse_row_selection(selected_input, total_rows)

    if not selected_rows:
        print(f"{Colors.FAIL}No valid rows selected. Exiting.{Colors.ENDC}")
        sys.exit(1)

    selected_indexes = [r - 1 for r in selected_rows]

    # -----------------------------------
    # PART 1: DETAILED MATCH TABLE
    # -----------------------------------
    print(f"\n{Colors.BOLD}{Colors.OKBLUE}{'='*10} MATCH-BY-MATCH WIN & TOSS PREDICTIONS {'='*10}{Colors.ENDC}\n")

    report_data = []

    team_a_col = "Team_A_Name"
    team_b_col = "Team_B_Name"
    date_col = "Match_Date"
    adv_col = "Overall_Advantage"
    toss_col = "Final_Toss_Prediction"

    for idx in selected_indexes:
        row = df.iloc[idx]
        match_label = f"{row[team_a_col]} vs {row[team_b_col]}"
        colored_advantage = colorize_prediction(row[adv_col])
        colored_toss = colorize_prediction(row[toss_col])
        report_data.append({
            'Match ID': idx + 1,
            'Date': row[date_col],
            'Match': match_label,
            'Win Advantage': colored_advantage,
            'Toss Prediction': colored_toss,
        })

    max_match = max(len(d['Match']) for d in report_data)
    HEADER_FORMAT = f"| {{:<8}} | {{:<12}} | {{:<{max_match}}} | {{:<45}} | {{:<45}} |"
    SEPARATOR = "-" * (8 + 2 + 12 + 2 + max_match + 2 + 45 + 2 + 45 + 2)

    print(SEPARATOR)
    print(f"{Colors.BOLD}{Colors.HEADER}" + HEADER_FORMAT.format(
        "ID", "Date", "Matchup", "WIN ADVANTAGE", "TOSS PREDICTION") + f"{Colors.ENDC}")
    print(SEPARATOR)

    for d in report_data:
        print(f"| {d['Match ID']:<8} | {d['Date']:<12} | {d['Match']:<{max_match}} | "
              f"{d['Win Advantage']:<45} | {d['Toss Prediction']:<45} |")
        print(SEPARATOR)

    # -----------------------------------
    # PART 2: TOSS AGGREGATION (TEAM NAMES)
    # -----------------------------------
    print(f"\n{Colors.BOLD}{Colors.OKGREEN}{'='*10} AGGREGATED TOSS PREDICTION BREAKDOWN {'='*10}{Colors.ENDC}\n")

    first_row = df.iloc[selected_indexes[0]]
    team_a = first_row[team_a_col]
    team_b = first_row[team_b_col]

    all_predictions = []

    # Map predictions to team names directly
    for idx in selected_indexes:
        row = df.iloc[idx]
        for col in TOSS_METHOD_COLS:
            result = str(row.get(col, '')).upper()
            if "A" in result:
                all_predictions.append(team_a)
            elif "B" in result:
                all_predictions.append(team_b)
            else:
                all_predictions.append("Neutral")

    counts = Counter(all_predictions)
    total = sum(counts.values())

    def bar(count, total, color, label):
        percentage = (count / total) * 100
        bar_len = int(percentage / 2)
        blocks = "█" * bar_len
        return f"{color}{blocks}{Colors.ENDC} {label}: {count} ({percentage:.1f}%)"

    print(f"{Colors.BOLD}{Colors.GRAY}Legend:{Colors.ENDC} {Colors.OKBLUE}{team_a}{Colors.ENDC} / {Colors.OKGREEN}{team_b}{Colors.ENDC} / {Colors.WARNING}Neutral{Colors.ENDC}\n")

    print(bar(counts.get(team_a, 0), total, Colors.OKBLUE, team_a))
    print(bar(counts.get(team_b, 0), total, Colors.OKGREEN, team_b))
    print(bar(counts.get("Neutral", 0), total, Colors.WARNING, "Neutral"))

    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")


if __name__ == "__main__":
    generate_report()
