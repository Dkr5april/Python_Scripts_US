#!/usr/bin/env python3
"""
ENHANCED PREDICTION REPORT GENERATOR
Reads the analysis results from 'match_analysis_data.xlsx' and generates
a colorful, detailed, console-based report showing match predictions and
an aggregated toss method breakdown.
"""

import pandas as pd
import sys
import os
from collections import Counter
from io import StringIO

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
    HEADER = '\033[95m'    # Magenta (Title)
    OKBLUE = '\033[94m'    # Blue (Captain A/Team A)
    OKGREEN = '\033[92m'   # Green (Captain B/Team B)
    WARNING = '\033[93m'   # Yellow (Neutral/Tie)
    FAIL = '\033[91m'      # Red (Errors)
    BOLD = '\033[1m'
    ENDC = '\033[0m'       # End Color
    GRAY = '\033[90m'


def colorize_prediction(text):
    """Applies color coding based on the content of the prediction string."""
    text_upper = text.upper()
    if 'A (' in text_upper or 'TEAM A' in text_upper:
        return f"{Colors.OKBLUE}{text}{Colors.ENDC}"
    if 'B (' in text_upper or 'TEAM B' in text_upper:
        return f"{Colors.OKGREEN}{text}{Colors.ENDC}"
    return f"{Colors.WARNING}{text}{Colors.ENDC}"


def generate_report():
    print(f"\n{Colors.HEADER}{Colors.BOLD}======================================================{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}=== FULL ASTRO-NUMEROLOGY PREDICTION REPORT CARD ==={Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}======================================================{Colors.ENDC}\n")
    
    IO_FILE = "match_analysis_data.xlsx"
    TOSS_METHOD_COLS = [f'Toss_Method_{i}_Numerology' for i in range(1, 7)]
    
    try:
        df = pd.read_excel(IO_FILE)
    except FileNotFoundError:
        print(f"{Colors.FAIL}FATAL ERROR: Input file '{IO_FILE}' not found. Run the master script first.{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.FAIL}FATAL ERROR reading Excel file: {e}{Colors.ENDC}")
        sys.exit(1)

    if df.empty:
        print(f"{Colors.WARNING}The Excel file is empty or contains no data.{Colors.ENDC}")
        return
        
    # --- PART 1: Match-by-Match Detailed Prediction Table ---
    print(f"{Colors.BOLD}{Colors.OKBLUE}--- MATCH-BY-MATCH WIN & TOSS PREDICTIONS ---{Colors.ENDC}")
    
    report_data = []
    
    team_a_col = next((col for col in df.columns if 'Team_A_Name' in col), 'Team_A')
    team_b_col = next((col for col in df.columns if 'Team_B_Name' in col), 'Team_B')
    date_col = next((col for col in df.columns if 'Match_Date' in col), 'Date')
    adv_col = 'Overall_Advantage'
    toss_col = 'Final_Toss_Prediction'
    
    
    for index, row in df.iterrows():
        
        if adv_col not in row or toss_col not in row:
            print(f"{Colors.FAIL}Error: Required prediction columns not found. Did the main analysis script run successfully?{Colors.ENDC}")
            return
            
        match_label = f"{row[team_a_col]} vs {row[team_b_col]}"
        
        colored_advantage = colorize_prediction(row[adv_col])
        colored_toss = colorize_prediction(row[toss_col])
        
        report_data.append({
            'Match ID': index + 1,
            'Date': row[date_col],
            'Match': match_label,
            'Win Advantage': colored_advantage,
            'Toss Prediction': colored_toss,
        })

    max_match = max(len(d['Match']) for d in report_data) if report_data else 30
    
    HEADER_FORMAT = f"| {{:<8}} | {{:<10}} | {{:<{max_match}}} | {{:<40}} | {{:<40}} |"
    SEPARATOR = "-" * (8 + 2 + 10 + 2 + max_match + 2 + 40 + 2 + 40 + 2)
    
    print(SEPARATOR)
    print(f"{Colors.BOLD}{Colors.HEADER}" + HEADER_FORMAT.format("ID", "Date", "Matchup", "OVERALL WIN ADVANTAGE", "FINAL TOSS PREDICTION") + f"{Colors.ENDC}")
    print(SEPARATOR)

    for d in report_data:
        print(f"| {d['Match ID']:<8} | {d['Date']:<10} | {d['Match'][:max_match]:<{max_match}} | {d['Win Advantage']:<40} | {d['Toss Prediction']:<40} |")
        print(SEPARATOR)
        
    print("\n")


    # --- PART 2: Aggregated Toss Method Bar Chart ---
    print(f"{Colors.BOLD}{Colors.OKGREEN}--- AGGREGATED TOSS PREDICTION BREAKDOWN ---{Colors.ENDC}")
    
    all_predictions = []
    a_name, b_name = "Team A", "Team B"

    for index, row in df.iterrows():
        if index == 0:
            if 'Captain_A_Name' in row and 'Captain_B_Name' in row:
                a_name = row['Captain_A_Name']
                b_name = row['Captain_B_Name']
        
        for col in TOSS_METHOD_COLS:
            result = str(row.get(col, ''))
            
            if result.startswith("Captain A"):
                all_predictions.append('A')
            elif result.startswith("Captain B"):
                all_predictions.append('B')
            else:
                all_predictions.append('Neutral')

    counts = Counter(all_predictions)
    total = sum(counts.values())
    if total == 0:
        print(f"{Colors.WARNING}No valid predictions found for charting.{Colors.ENDC}")
        return
        
    def create_bar(count, total, color, label):
        percentage = (count / total) * 100
        bar_length = int(percentage / 2)
        bar = "█" * bar_length
        return f" {color}{bar}{Colors.ENDC} {color}{label}: {count} ({percentage:.1f}%){Colors.ENDC}"

    print(f"\n{Colors.BOLD}{Colors.GRAY}Legend: {Colors.OKBLUE}Blue = {a_name}{Colors.ENDC} / {Colors.OKGREEN}Green = {b_name}{Colors.ENDC} / {Colors.WARNING}Yellow = Neutral{Colors.ENDC}")
    print(f"{Colors.GRAY}(Total {total} Method Predictions Across {len(df)} Matches){Colors.ENDC}\n")

    categories = [
        ('A', Colors.OKBLUE, f"Winner {a_name} ({a_name})"), 
        ('B', Colors.OKGREEN, f"Winner {b_name} ({b_name})"), 
        ('Neutral', Colors.WARNING, "Neutral/Tie")
    ]
    
    for label, color, display_label in categories:
        count = counts.get(label, 0)
        bar_output = create_bar(count, total, color, display_label)
        print(bar_output)

    print(f"\n{Colors.HEADER}{Colors.BOLD}======================================================{Colors.ENDC}")


if __name__ == "__main__":
    generate_report()
