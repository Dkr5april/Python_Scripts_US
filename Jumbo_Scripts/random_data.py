import pandas as pd
import random
from datetime import datetime, timedelta

def generate_random_data(num_matches=50, filename="match_analysis_data.xlsx"):
    """Generates a DataFrame with random astrological and numerological input data."""
    
    CAPTAINS = [
        "Virat Kohli", "Joe Root", "Kane Williamson", "Babar Azam", 
        "Steve Smith", "Quinton de Kock", "Ben Stokes", "Rashid Khan",
        "Eoin Morgan", "Rohit Sharma", "Aaron Finch", "Brendon McCullum"
    ]
    CITIES = [
        "London", "Sydney", "Mumbai", "Cape Town", "Dubai", "Auckland",
        "New York", "Kolkata", "Melbourne", "Galle", "Paris", "Lahore"
    ]
    
    # Helper function to generate a random date string (DD/MM/YYYY)
    def random_date(start_year, end_year):
        start = datetime(start_year, 1, 1)
        end = datetime(end_year, 12, 31)
        random_day = start + timedelta(days=random.randint(0, (end - start).days))
        return random_day.strftime("%d/%m/%Y")

    data = []
    
    for _ in range(num_matches):
        # Generate Captain DOBs (Assume born between 1980 and 2000)
        a_dob = random_date(1980, 2000)
        b_dob = random_date(1980, 2000)
        
        # Generate Match Date (Assume matches are in the next 1-2 years)
        match_dt_obj = datetime.now() + timedelta(days=random.randint(1, 730))
        match_date_str = match_dt_obj.strftime("%d/%m/%Y")
        
        # Generate Match Time (HH:MM)
        match_time_str = f"{random.randint(9, 21):02}:{random.choice([0, 15, 30, 45]):02}"
        
        # Generate Timezone Offset (-10.0 to +14.0, common range)
        tz_offset = random.choice([x * 0.5 for x in range(-20, 29)])
        
        # Create the row data
        data.append({
            "Team_A_Name": random.choice(CAPTAINS),
            "Team_A_DOB": a_dob,
            "Team_B_Name": random.choice(CAPTAINS),
            "Team_B_DOB": b_dob,
            "Match_Date": match_date_str,
            "Match_Time": match_time_str,
            "TZ_Offset_Hours": tz_offset,
            "Match_Place": random.choice(CITIES)
        })
    
    # Create the DataFrame and save it to the specified Excel file
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"Successfully created {num_matches} rows of data in {filename}")
    print("This file is now ready to be processed by your main analysis script.")

if __name__ == "__main__":
    # Ensure you have pandas installed: pip install pandas openpyxl
    generate_random_data(num_matches=50)