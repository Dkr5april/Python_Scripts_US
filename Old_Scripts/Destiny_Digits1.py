def sum_digits_until_single(num):
    while num > 9:
        num = sum(int(digit) for digit in str(num))
    return num

def calculate_life_path(dob):
    return sum_digits_until_single(sum(int(digit) for digit in dob))

def calculate_destiny_number(dob):
    return sum_digits_until_single(int(dob))

def construct_matrix(dob, destiny):
    destiny_str = str(destiny) if destiny > 9 else "0" + str(destiny)
    return [[int(dob[0]), int(dob[1])], [int(destiny_str[0]), int(destiny_str[1])]]

def reduce_matrix(matrix):
    return [sum_digits_until_single(matrix[0][0] + matrix[1][0]),
            sum_digits_until_single(matrix[0][1] + matrix[1][1])]

def doubling_number(reduced):
    num1, num2 = reduced
    num1_parts = [1, 1, 10 - (1 + 1), num1]
    num2_parts = [8, 8, 10 - (8 + 8), num2]
    return num1_parts, num2_parts

def final_representation(num1_parts, num2_parts):
    largest = max(num1_parts[-2], num2_parts[-2])
    if num1_parts[-2] == largest:
        num1_parts[-2:] = [1, 9, 4]
    else:
        num2_parts[-2:] = [1, 9, 4]
    return num1_parts, num2_parts

def numerology_analysis(dob1, dob2, match_date, debug=False):
    if debug:
        print("\nCalculating for:", dob1, dob2, match_date)
    
    lp1, lp2, lp_match = calculate_life_path(dob1), calculate_life_path(dob2), calculate_life_path(match_date)
    destiny1, destiny2, destiny_match = calculate_destiny_number(dob1), calculate_destiny_number(dob2), calculate_destiny_number(match_date)
    
    if debug:
        print("Life Path Numbers:", lp1, lp2, lp_match)
        print("Destiny Numbers:", destiny1, destiny2, destiny_match)
    
    matrix1, matrix2 = construct_matrix(dob1, destiny1), construct_matrix(dob2, destiny2)
    match_matrix = construct_matrix(match_date, destiny_match)
    
    reduced1, reduced2 = reduce_matrix(matrix1), reduce_matrix(matrix2)
    match_reduced = reduce_matrix(match_matrix)
    
    if debug:
        print("Reduced Matrices:", reduced1, reduced2, match_reduced)
    
    num1_parts, num2_parts = doubling_number(match_reduced)
    final_num1, final_num2 = final_representation(num1_parts, num2_parts)
    
    if debug:
        print("Final Representation:", final_num1, "/", final_num2)
    
    return final_num1, final_num2

if __name__ == "__main__":
    player1_dob = input("Enter Player 1 DOB (DDMMYYYY): ")
    player2_dob = input("Enter Player 2 DOB (DDMMYYYY): ")
    match_date = input("Enter Match Date (DDMMYYYY): ")
    
    numerology_analysis(player1_dob, player2_dob, match_date, debug=True)
