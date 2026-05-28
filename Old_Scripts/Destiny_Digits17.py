import json
import os

def get_manual_input():
    player1_name = input("Enter Player 1 Name: ")
    player1_dob = input(f"Enter {player1_name}'s DOB (DDMMYYYY): ")

    player2_name = input("Enter Player 2 Name: ")
    player2_dob = input(f"Enter {player2_name}'s DOB (DDMMYYYY): ")

    match_date = input("Enter Match Date (DDMMYYYY): ")
    return player1_name, player1_dob, player2_name, player2_dob, match_date

def get_file_input(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        
        if isinstance(data, dict) and "Matches" in data:
            return data["Matches"]
        elif isinstance(data, list):
            return data
        else:
            raise ValueError("Invalid JSON format. Expected a list or a dictionary with a 'Matches' key.")

def calculate_dob_sum(dob):
    total_sum = sum(int(digit) for digit in dob if digit.isdigit())
    birth_date = int(dob[:2])
    final_sum = total_sum + birth_date
    return total_sum, final_sum

def construct_matrix(dob, final_sum):
    dob_formatted = f"{int(dob[:2]):02d}"
    final_sum_formatted = f"{final_sum:02d}"
    return [[int(dob_formatted[0]), int(dob_formatted[1])],
            [int(final_sum_formatted[0]), int(final_sum_formatted[1])]]

def reduce_to_single_digit(num):
    while num >= 10:
        num = sum(int(digit) for digit in str(num))
    return num

def compute_column_reduction(matrix):
    first_col_sum = matrix[0][0] + matrix[1][0]
    second_col_sum = matrix[0][1] + matrix[1][1]
    return reduce_to_single_digit(first_col_sum), reduce_to_single_digit(second_col_sum)

def process_match(player1_name, player1_dob, player2_name, player2_dob, match_date):
    p1_total_sum, p1_final_sum = calculate_dob_sum(player1_dob)
    p2_total_sum, p2_final_sum = calculate_dob_sum(player2_dob)
    match_total_sum, match_final_sum = calculate_dob_sum(match_date)
    
    matrix1 = construct_matrix(player1_dob, p1_final_sum)
    matrix2 = construct_matrix(player2_dob, p2_final_sum)
    match_matrix = construct_matrix(match_date, match_final_sum)
    
    p1_col1, p1_col2 = compute_column_reduction(matrix1)
    p2_col1, p2_col2 = compute_column_reduction(matrix2)
    match_col1, match_col2 = compute_column_reduction(match_matrix)
    
    output = f"""
Match Analysis:
{player1_name} ({player1_dob}) vs {player2_name} ({player2_dob}) on {match_date}

Player 1 Matrix: {matrix1}
Player 2 Matrix: {matrix2}
Match Date Matrix: {match_matrix}

Column Reductions:
Player 1: {p1_col1}, {p1_col2}
Player 2: {p2_col1}, {p2_col2}
Match: {match_col1}, {match_col2}
"""
    
    print(output)
    with open("BPL_results_file.txt", "w") as out_file:
        out_file.write(output)

def main():
    input_choice = input("Do you want to enter data manually or from a file? (manual/file): ").strip().lower()
    
    if input_choice == "file":
        file_path = input("Enter the JSON file path: ").strip()
        matches = get_file_input(file_path)
        
        if matches:
            match = matches[0]  # Only process the first match for now
            process_match(match["Team1Captain"], match["Team1CaptainDOB"].replace("-", ""),
                          match["Team2Captain"], match["Team2CaptainDOB"].replace("-", ""),
                          match["Date"].replace("-", ""))
    else:
        process_match(*get_manual_input())
    
if __name__ == "__main__":
    main()
