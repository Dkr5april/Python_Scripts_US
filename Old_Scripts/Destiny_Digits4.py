# Step 1: Take Inputs
player1_dob = input("Enter Player 1 DOB (DDMMYYYY): ")
player2_dob = input("Enter Player 2 DOB (DDMMYYYY): ")
match_date = input("Enter Match Date (DDMMYYYY): ")

# Function to Compute the Required Sum
def calculate_dob_sum(dob):
    total_sum = sum(int(digit) for digit in dob)  # Sum of all digits
    birth_date = int(dob[:2])  # Extract DD (first two digits)
    final_sum = total_sum + birth_date  # Add DD to the sum
    return total_sum, final_sum

# Function to Format and Construct 2×2 Matrix
def construct_matrix(dob, final_sum):
    dob_formatted = f"{int(dob[:2]):02d}"  # Ensure two-digit format for DD
    final_sum_formatted = f"{final_sum:02d}"  # Ensure two-digit format for the sum
    
    # Format for spacing between digits
    dob_spaced = " ".join(dob_formatted)
    sum_spaced = " ".join(final_sum_formatted)
    
    return [[dob_spaced], [sum_spaced]]

# Function to Reduce a Number to a Single Digit
def reduce_to_single_digit(num):
    while num >= 10:
        num = sum(int(digit) for digit in str(num))
    return num

# Function to Compute Column-Wise Reduction
def compute_column_reduction(matrix):
    first_col_sum = sum(int(matrix[i][0][0]) for i in range(2))
    second_col_sum = sum(int(matrix[i][0][2]) for i in range(2))
    
    return reduce_to_single_digit(first_col_sum), reduce_to_single_digit(second_col_sum)

# Compute results for each input
p1_total_sum, p1_final_sum = calculate_dob_sum(player1_dob)
p2_total_sum, p2_final_sum = calculate_dob_sum(player2_dob)
match_total_sum, match_final_sum = calculate_dob_sum(match_date)

# Construct matrices
matrix1 = construct_matrix(player1_dob, p1_final_sum)
matrix2 = construct_matrix(player2_dob, p2_final_sum)
match_matrix = construct_matrix(match_date, match_final_sum)

# Compute column reductions
p1_col1, p1_col2 = compute_column_reduction(matrix1)
p2_col1, p2_col2 = compute_column_reduction(matrix2)
match_col1, match_col2 = compute_column_reduction(match_matrix)

# Construct new 2x2 matrices
combined_matrix1 = [[p1_col1, p1_col2], [match_col1, match_col2]]
combined_matrix2 = [[p2_col1, p2_col2], [match_col1, match_col2]]

# Print the outputs
print("\nPlayer 1 Matrix:")
print(f"[{matrix1[0][0]}]")
print(f"[{matrix1[1][0]}]")
print(f"Reduced: First Column: {p1_col1}, Second Column: {p1_col2}")

print("\nPlayer 2 Matrix:")
print(f"[{matrix2[0][0]}]")
print(f"[{matrix2[1][0]}]")
print(f"Reduced: First Column: {p2_col1}, Second Column: {p2_col2}")

print("\nMatch Date Matrix:")
print(f"[{match_matrix[0][0]}]")
print(f"[{match_matrix[1][0]}]")
print(f"Reduced: First Column: {match_col1}, Second Column: {match_col2}")

print("\nCombined Matrix 1 (Player 1 & Match Date):")
print(f"[{combined_matrix1[0][0]} {combined_matrix1[0][1]}]")
print(f"[{combined_matrix1[1][0]} {combined_matrix1[1][1]}]")

print("\nCombined Matrix 2 (Player 2 & Match Date):")
print(f"[{combined_matrix2[0][0]} {combined_matrix2[0][1]}]")
print(f"[{combined_matrix2[1][0]} {combined_matrix2[1][1]}]")
