#!/usr/bin/env python3
"""
Reads the output Excel file from astro_numerology_analysis.py
and extracts only the key prediction results.

Now includes all 6 toss prediction methods to show the breakdown of the 
Final Toss Prediction (which is based on a majority vote).

USAGE:
1. Ensure 'match_analysis_data.xlsx' (the output file) is in the same folder.
2. Run the script: python extract_results.py
"""
import sys
import pandas as pd

def extract_key_results(filename="match_analysis_data.xlsx"):
    """
    Loads the Excel analysis file and filters for key prediction columns, 
    including all six toss methods.
    """
    print(f"Reading results from: {filename}")
    
    try:
        # We assume the file is the output from the main script
        df = pd.read_excel(filename)
    except FileNotFoundError:
        print(f"\nFATAL ERROR: The file '{filename}' was not found.")
        print("Please ensure you have run 'astro_numerology_analysis.py' first.")
        sys.exit(1)
    except Exception as e:
        print(f"\nFATAL ERROR reading Excel file: {e}")
        sys.exit(1)

    # ----------------------------------------------------
    # Define the exact columns you want to view - now including all 6 methods
    # ----------------------------------------------------
    KEY_COLUMNS = [
        # Context Columns
        'Match_Date', 
        'Team_A_Name', 
        'Team_B_Name', 
        'Captain_A_Name',
        'Captain_B_Name',

        # Match Trend Prediction
        'Overall_Advantage', 
        'Predicted_Score_Range',
        
        # Detailed Toss Predictions (The six methods)
        'Toss_Method_1_Numerology',
        'Toss_Method_2_Horary_Ruler',
        'Toss_Method_3_Star_Lord',
        'Toss_Method_4_Ruling_No',
        'Toss_Method_5_Compound_Score',
        'Toss_Method_6_Moon_Sign_Lord',
        
        # Final Consolidated Result
        'Final_Toss_Prediction', 
    ]

    # Filter the DataFrame to only include the requested columns
    try:
        # Filter columns, ignoring errors if a column name is slightly off
        df_filtered = df[KEY_COLUMNS]
        
        print("\n=== Filtered Match Predictions (Toss Breakdown Included) ===")
        # Use to_string() for better console formatting of wide dataframes
        print(df_filtered.to_string(index=False))
        
        # Optional: Save the filtered results to a new, simpler CSV file
        simple_csv_file = "simplified_match_predictions.csv"
        df_filtered.to_csv(simple_csv_file, index=False)
        print(f"\nResults also saved to **{simple_csv_file}** for easy viewing.")

    except KeyError as e:
        print(f"\nERROR: One or more required columns are missing in the Excel file.")
        print(f"Missing column: {e}")
        print("Please check that the analysis script ran completely and verify the column names.")

if __name__ == "__main__":
    extract_key_results()