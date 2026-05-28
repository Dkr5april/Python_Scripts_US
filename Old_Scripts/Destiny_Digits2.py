# Step 1: Take Inputs
player1_dob = input("Enter Player 1 DOB (DDMMYYYY): ")
player2_dob = input("Enter Player 2 DOB (DDMMYYYY): ")
match_date = input("Enter Match Date (DDMMYYYY): ")

# Step 2: Function to Compute the Required Sum
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

# Compute results for each input
p1_total_sum, p1_final_sum = calculate_dob_sum(player1_dob)
p2_total_sum, p2_final_sum = calculate_dob_sum(player2_dob)
match_total_sum, match_final_sum = calculate_dob_sum(match_date)

# Construct matrices
matrix1 = construct_matrix(player1_dob, p1_final_sum)
matrix2 = construct_matrix(player2_dob, p2_final_sum)
match_matrix = construct_matrix(match_date, match_final_sum)

# Print the outputs in 2×2 form with proper spacing
print("\nPlayer 1 Matrix:")
print(f"[{matrix1[0][0]}]")
print(f"[{matrix1[1][0]}]")

print("\nPlayer 2 Matrix:")
print(f"[{matrix2[0][0]}]")
print(f"[{matrix2[1][0]}]")

print("\nMatch Date Matrix:")
print(f"[{match_matrix[0][0]}]")
print(f"[{match_matrix[1][0]}]")
