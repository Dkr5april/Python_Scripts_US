import pandas as pd
import numpy as np
import os # CRITICAL for debugging file paths
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report
from sklearn.ensemble import RandomForestClassifier

# --- 1. CORE NUMEROLOGY FUNCTION ---
def calculate_single_digit_sum(num):
    s = 0
    if pd.isna(num) or num == 0:
        return 0
    num = int(num)
    while num:
        s += num % 10
        num //= 10
    if s > 9:
        return calculate_single_digit_sum(s)
    return s

def calculate_numerology_features(date_str, name=None):
    try:
        dt = pd.to_datetime(date_str)
        day = dt.day
        month = dt.month
        year = dt.year
        psychic_number = calculate_single_digit_sum(day)
        destiny_base = day + month + year
        destiny_number = calculate_single_digit_sum(destiny_base)
        return psychic_number, destiny_number
    except:
        return np.nan, np.nan

# --- 2. FEATURE ENGINEERING AND MAPPING ---
def feature_engineer_and_map(df, is_training=True):
    df = df.copy()
    cols_to_drop = ['Match_Time', 'TZ_Offset_Hours', 'TeamA_Color', 'TeamB_Color', 'Stadium_Direction']
    df = df.drop(columns=[col for col in cols_to_drop if col in df.columns], errors='ignore')
    date_cols = ['Captain_A_DOB', 'Captain_B_DOB', 'Match_Date']
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    df[['A_Psychic', 'A_Destiny']] = df['Captain_A_DOB'].apply(lambda x: pd.Series(calculate_numerology_features(x)))
    df[['B_Psychic', 'B_Destiny']] = df['Captain_B_DOB'].apply(lambda x: pd.Series(calculate_numerology_features(x)))
    df[['Match_Day_Num', 'Match_Date_Destiny']] = df['Match_Date'].apply(lambda x: pd.Series(calculate_numerology_features(x)))
    df['Destiny_Diff'] = np.abs(df['A_Destiny'] - df['B_Destiny'])
    df['A_Match_Destiny_Diff'] = np.abs(df['A_Destiny'] - df['Match_Date_Destiny'])
    df['B_Match_Destiny_Diff'] = np.abs(df['B_Destiny'] - df['Match_Date_Destiny'])
    df['A_Age'] = (df['Match_Date'] - df['Captain_A_DOB']).dt.days / 365.25
    df['B_Age'] = (df['Match_Date'] - df['Captain_B_DOB']).dt.days / 365.25
    df['Match_Year'] = df['Match_Date'].dt.year
    df['Match_Month'] = df['Match_Date'].dt.month
    df['Match_DayOfWeek'] = df['Match_Date'].dt.dayofweek
    captain_cols = ['Captain_A_Name', 'Captain_B_Name']
    for col in captain_cols:
        df[f'{col}_ID'] = df[col].astype('category').cat.codes
    df = pd.get_dummies(df, columns=['Series', 'Match_Place', 'Match_Format'], dummy_na=False)
    if is_training:
        df = df.dropna(subset=['Real_Toss', 'Real_Match'])
        df = df[~df['Real_Toss'].isin(['TBD'])]
        df = df[~df['Real_Match'].isin(['TBD'])]
        df['Toss_Winner_A'] = df.apply(
            lambda row: 1 if row['Real_Toss'] == row['Captain_A_Name'] else (0 if row['Real_Toss'] == row['Captain_B_Name'] else np.nan), axis=1
        )
        df['Match_Winner_A'] = df.apply(
            lambda row: 1 if row['Real_Match'] == row['Captain_A_Name'] else (0 if row['Real_Match'] == row['Captain_B_Name'] else np.nan), axis=1
        )
        df = df.dropna(subset=['Toss_Winner_A', 'Match_Winner_A'])
        df['Toss_Winner_A'] = df['Toss_Winner_A'].astype(int)
        df['Match_Winner_A'] = df['Match_Winner_A'].astype(int)
    feature_cols = [
        'A_Psychic', 'A_Destiny', 'B_Psychic', 'B_Destiny', 'Match_Day_Num',
        'Match_Date_Destiny', 'Destiny_Diff', 'A_Match_Destiny_Diff',
        'B_Match_Destiny_Diff', 'A_Age', 'B_Age', 'Match_Year',
        'Match_Month', 'Match_DayOfWeek', 'Captain_A_Name_ID',
        'Captain_B_Name_ID'
    ]
    feature_cols.extend(df.filter(regex='Series_|Match_Place_|Match_Format_').columns.tolist())
    feature_cols = [col for col in feature_cols if col in df.columns]
    return df, feature_cols

# --- 3. ML TRAINING AND EVALUATION ---
def train_and_evaluate_model(X, y, target_name):
    print(f"\n--- Training Model for {target_name} ---")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    model_pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced'))
    ])
    model_pipeline.fit(X_train, y_train)
    y_pred = model_pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred)
    print(f"\n{target_name} Prediction Accuracy: {accuracy:.4f}")
    print(f"\nClassification Report:\n{report}")
    return model_pipeline, accuracy

# --- 4. PREDICTION ---
def predict_future_matches(model, X_predict, original_df):
    print("\n--- Generating Predictions for Future Matches ---")
    X_predict_filled = X_predict.fillna(X_predict.mean())
    predictions = model.predict(X_predict_filled)
    predictions_proba = model.predict_proba(X_predict_filled)
    results = original_df[['Match_Date', 'Captain_A_Name', 'Captain_B_Name', 'Team_A_name', 'Team_B_name']].reset_index(drop=True).copy()
    results['Prediction_A_Win'] = predictions
    results['Win_Probability_A'] = predictions_proba[:, 1]
    results['Win_Probability_B'] = predictions_proba[:, 0]
    results['Predicted_Winner_Captain'] = results.apply(
        lambda row: row['Captain_A_Name'] if row['Prediction_A_Win'] == 1 else row['Captain_B_Name'],
        axis=1
    )
    results['Predicted_Winner_Team'] = results.apply(
        lambda row: row['Team_A_name'] if row['Prediction_A_Win'] == 1 else row['Team_B_name'],
        axis=1
    )
    return results[['Match_Date', 'Team_A_name', 'Team_B_name', 'Predicted_Winner_Team', 'Predicted_Winner_Captain', 'Win_Probability_A', 'Win_Probability_B']]

# --- 5. MAIN SCRIPT EXECUTION ---
def run_universal_script(train_file, predict_file):
    toss_predictions, match_predictions = None, None 
    try:
        # Load Data
        df_train_raw = pd.read_csv(train_file)
        df_predict_raw = pd.read_csv(predict_file)
        
        print(f"DEBUG: Successfully loaded {len(df_train_raw)} training rows and {len(df_predict_raw)} prediction rows.")

        # Feature Engineering (Training)
        df_train_engineered, feature_cols_train = feature_engineer_and_map(df_train_raw, is_training=True)
        X_train = df_train_engineered[feature_cols_train].select_dtypes(include=np.number).fillna(0).apply(pd.to_numeric, errors='coerce').fillna(0)
        y_toss = df_train_engineered['Toss_Winner_A']
        y_match = df_train_engineered['Match_Winner_A']

        print(f"Total rows for training (after cleaning): {len(X_train)}")
        print(f"Total features used: {len(X_train.columns)}")
        print("-" * 50)

        # Model Training and Evaluation
        toss_model, toss_accuracy = train_and_evaluate_model(X_train, y_toss, "Toss Winner")
        match_model, match_accuracy = train_and_evaluate_model(X_train, y_match, "Match Winner")

        print("-" * 50)
        print(f"Overall Toss Prediction Success (Accuracy): {toss_accuracy:.2%}")
        print(f"Overall Match Prediction Success (Accuracy): {match_accuracy:.2%}")
        print("-" * 50)

        # Prediction Data Prep and Generation
        df_predict_engineered, feature_cols_predict = feature_engineer_and_map(df_predict_raw, is_training=False)
        X_predict = pd.DataFrame(0, index=df_predict_engineered.index, columns=X_train.columns)
        for col in X_train.columns:
            if col in df_predict_engineered.columns:
                X_predict[col] = pd.to_numeric(df_predict_engineered[col], errors='coerce').fillna(0)
        
        toss_predictions = predict_future_matches(toss_model, X_predict, df_predict_raw)
        match_predictions = predict_future_matches(match_model, X_predict, df_predict_raw)

        # --- CRITICAL FILE SAVING DEBUGGING ---
        try:
            current_dir = os.getcwd() 
            toss_path = os.path.join(current_dir, 'toss_predictions.csv')
            match_path = os.path.join(current_dir, 'match_predictions.csv')

            print("\n" + "#" * 50)
            print(f"DEBUG: Attempting to save files to ABSOLUTE PATH:")
            print(f"Toss File Path: {toss_path}")
            print(f"Match File Path: {match_path}")
            print("#" * 50)
            
            toss_predictions.to_csv(toss_path, index=False)
            match_predictions.to_csv(match_path, index=False)
            
            print(f"DEBUG: File saving successfully completed.")

        except Exception as file_e:
            print("\n" + "!" * 50)
            print(f"!!! CRITICAL FILE SAVE ERROR !!!")
            print(f"Error saving files: {file_e}")
            print("This is the root cause. If you see this, Windows/Antivirus is blocking the file write.")
            print("!" * 50)
            
        return toss_predictions, match_predictions

    except Exception as e:
        print("\n" + "#" * 50)
        print(f"!!! CRITICAL SCRIPT ERROR !!! Script Execution Failed at start:")
        print(f"Root Cause: {e}")
        print("#" * 50 + "\n")
        return None, None 

# --- EXECUTE THE SCRIPT ---
TRAIN_FILE = 'match_analysis_data.xlsx - Sheet1.csv'
PREDICT_FILE = 'match_analysis_data.xlsx - Sheet2.csv'

# Execute the main function
toss_preds, match_preds = run_universal_script(TRAIN_FILE, PREDICT_FILE)

# --- Display results explicitly ---
if toss_preds is not None and match_preds is not None:
    print("\n--- SCRIPT SUCCESSFUL ---")
    print("\n--- FINAL PREDICTIONS (Toss) ---")
    print(toss_preds.head(3))
    print("\n--- FINAL PREDICTIONS (Match) ---")
    print(match_preds.head(3))
else:
    print("\nSCRIPT FAILED: See the 'CRITICAL ERROR' messages above for details.")