def sum_digits(n):
    """Returns the sum of digits of a number until a single digit is obtained."""
    while n > 9:
        n = sum(int(digit) for digit in str(n))
    return n

def get_life_path_number(dob):
    """Calculates the life path number for a given date of birth (DDMMYYYY)."""
    return sum_digits(sum(int(digit) for digit in dob))

def get_destiny_number(dob):
    """Calculates the destiny number for a given date of birth (DDMMYYYY)."""
    return sum_digits(int(dob[:2]))  # Sum of birth day

def generate_2x2_matrix(number):
    """Generates the 2x2 matrix components based on the doubling method."""
    if number == 7:
        return [1, 1, 5]  # As per given rules
    elif number == 2:
        return [8, 8, 4]  # As per given rules
    return []

def convert_to_final_representation(matrix):
    """Converts the chosen matrix to the final format."""
    last_digit = matrix[-1]
    reference = 10
    additional_values = [1, 9] if last_digit == 5 else [8, 8]  # 10-based transformation
    additional_values.append(reference - sum(additional_values))  # To balance the sum
    return matrix[:-1] + additional_values

def numerology_prediction(player1_dob, player2_dob, match_date):
    """Calculates the final numerology prediction based on the given DOBs and match date."""
    # Compute life path numbers
    lp1 = get_life_path_number(player1_dob)
    lp2 = get_life_path_number(player2_dob)
    match_lp = get_life_path_number(match_date)
    
    # Reduce to final two numbers
    final_1 = sum_digits(lp1 + lp2)
    final_2 = sum_digits(match_lp)
    
    # Generate matrix and get the largest value's transformation
    matrix_1 = generate_2x2_matrix(final_1)
    matrix_2 = generate_2x2_matrix(final_2)
    
    last_digit_1 = matrix_1[-1]
    last_digit_2 = matrix_2[-1]
    
    # Choose the matrix with the highest last digit
    chosen_matrix = matrix_1 if last_digit_1 > last_digit_2 else matrix_2
    final_representation = convert_to_final_representation(chosen_matrix)
    
    return final_representation, chosen_matrix[-1]

# Example usage:
player1_dob = "08091999"  # Shubman Gill
player2_dob = "11101993"  # Hardik Pandya
match_date = "29032025"

final_output, last_digit = numerology_prediction(player1_dob, player2_dob, match_date)
print("Final Representation:", final_output, "/", last_digit)
