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
    
    return [[int(dob_formatted[0]), int(dob_formatted[1])], 
            [int(final_sum_formatted[0]), int(final_sum_formatted[1])]]

# Function to Reduce a Number to a Single Digit
def reduce_to_single_digit(num):
    while num >= 10:
        num = sum(int(digit) for digit in str(num))
    return num

# Function to Compute Column-Wise Reduction
def compute_column_reduction(matrix):
    first_col_sum = matrix[0][0] + matrix[1][0]
    second_col_sum = matrix[0][1] + matrix[1][1]
    
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

# Compute column reductions for combined matrices
c1_col1, c1_col2 = compute_column_reduction(combined_matrix1)
c2_col1, c2_col2 = compute_column_reduction(combined_matrix2)

# Final reduction
final_number1 = reduce_to_single_digit(c1_col1 + c1_col2)
final_number2 = reduce_to_single_digit(c2_col1 + c2_col2)

# Doubling Concept Mapping
doubling_dict = {
    1: [5, 5], 2: [1, 1], 3: [6, 6], 4: [2, 2], 5: [7, 7],
    6: [3, 3], 7: [8, 8], 8: [4, 4], 9: [9, 9]
}

# Compute the triplets
def compute_triplet(final_number, reference_number):
    first_two_digits = doubling_dict.get(reference_number, [0, 0])
    required_sum = final_number - sum(first_two_digits)
    while required_sum < 0:
        required_sum += 9  # Adjusting negative sum cases
    third_digit = reduce_to_single_digit(required_sum)
    return first_two_digits + [third_digit]

triplet1 = compute_triplet(final_number1, final_number2)
triplet2 = compute_triplet(final_number2, final_number1)

# Compute final breakdown
highest_last_digit = max(triplet1[-1], triplet2[-1])
X = 0
while reduce_to_single_digit(1 + 9 + X) != highest_last_digit:
    X += 1

final_breakdown = f"1,9,{X}"

# Win/Loss Theory Calculations
win_loss_matrix = [[final_number1 - 1, final_number1 + 1], [final_number2 - 1, final_number2 + 1]]

# Print the outputs
print("\nPlayer 1 Matrix:")
print(f"[{matrix1[0][0]} {matrix1[0][1]}]")
print(f"[{matrix1[1][0]} {matrix1[1][1]}]")
print(f"Reduced: First Column: {p1_col1}, Second Column: {p1_col2}")

print("\nPlayer 2 Matrix:")
print(f"[{matrix2[0][0]} {matrix2[0][1]}]")
print(f"[{matrix2[1][0]} {matrix2[1][1]}]")
print(f"Reduced: First Column: {p2_col1}, Second Column: {p2_col2}")

print("\nMatch Date Matrix:")
print(f"[{match_matrix[0][0]} {match_matrix[0][1]}]")
print(f"[{match_matrix[1][0]} {match_matrix[1][1]}]")
print(f"Reduced: First Column: {match_col1}, Second Column: {match_col2}")

print("\nCombined Matrix 1 (Player 1 & Match Date):")
print(f"[{combined_matrix1[0][0]} {combined_matrix1[0][1]}]")
print(f"[{combined_matrix1[1][0]} {combined_matrix1[1][1]}]")
print(f"Reduced: First Column: {c1_col1}, Second Column: {c1_col2}")

print("\nCombined Matrix 2 (Player 2 & Match Date):")
print(f"[{combined_matrix2[0][0]} {combined_matrix2[0][1]}]")
print(f"[{combined_matrix2[1][0]} {combined_matrix2[1][1]}]")
print(f"Reduced: First Column: {c2_col1}, Second Column: {c2_col2}")

print("\nFinal Numbers:")
print(f"Final Number 1: {final_number1} ({', '.join(map(str, triplet1))})")
print(f"Final Number 2: {final_number2} ({', '.join(map(str, triplet2))})")
print(f"Final Breakdown: {final_breakdown}/{highest_last_digit}")

print("\nWin/Loss Theory Matrix:")
print(f"[{win_loss_matrix[0][0]} {win_loss_matrix[0][1]}]")
print(f"[{win_loss_matrix[1][0]} {win_loss_matrix[1][1]}]")
