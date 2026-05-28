# ================================
# DATE NUMEROLOGY FUNCTION LIBRARY
# ================================

def get_day_of_week(day: int, month: int, year: int) -> int:
    """
    Returns day of week as integer:
    0 = Sunday, 1 = Monday, ..., 6 = Saturday
    """
    t = (14 - month) // 12
    y = year - t
    m = month + 12 * t - 2
    return (day + y + y // 4 - y // 100 + y // 400 + (31 * m) // 12) % 7


def get_week_value(day_of_week: int) -> int:
    """
    Chaldean / Lo Shu weekday vibration values:
    Sunday    -> 1
    Monday    -> 2
    Tuesday   -> 9
    Wednesday -> 5
    Thursday  -> 3
    Friday    -> 6
    Saturday  -> 8
    """
    week_values = [1, 2, 9, 5, 3, 6, 8]
    return week_values[day_of_week]


def calculate_date_score(day: int, month: int, year: int) -> int:
    """
    Calculates base numerology score:
    Sum of digits of date + day number + constant 90
    """
    digit_sum = sum(int(d) for d in f"{day}{month}{year}")
    return digit_sum + day + 90


def get_month_number(month_input: str) -> int:
    """
    Accepts numeric month or month name (case-insensitive)
    Returns month number (1–12)
    """
    if month_input.isdigit():
        month = int(month_input)
        if 1 <= month <= 12:
            return month
        raise ValueError("Month number must be between 1 and 12")

    month_names = [
        "january", "february", "march", "april",
        "may", "june", "july", "august",
        "september", "october", "november", "december"
    ]

    month_input = month_input.lower()
    if month_input not in month_names:
        raise ValueError("Invalid month name")

    return month_names.index(month_input) + 1


def calculate_final_score(day: int, month: int, year: int) -> int:
    """
    Master function:
    Final Score = Date Score + Weekday Value
    """
    day_of_week = get_day_of_week(day, month, year)
    week_value = get_week_value(day_of_week)
    base_score = calculate_date_score(day, month, year)
    return base_score + week_value


# ================================
# INTERACTIVE EXECUTION BLOCK
# ================================

if __name__ == "__main__":
    print("--- Date Numerology Calculator ---")
    
    try:
        # 1. Get User Input
        d = int(input("Enter Day (1-31): "))
        m_str = input("Enter Month (Name or 1-12): ")
        y = int(input("Enter Year (e.g. 1995): "))

        # 2. Process Month
        m = get_month_number(m_str)

        # 3. Perform Calculations
        weekday_idx = get_day_of_week(d, m, y)
        weekday_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        
        week_vibe = get_week_value(weekday_idx)
        date_score = calculate_date_score(d, m, y)
        final_score = calculate_final_score(d, m, y)

        # 4. Display Results
        print("\n" + "="*30)
        print(f"Results for: {d}/{m}/{y} ({weekday_names[weekday_idx]})")
        print("-" * 30)
        print(f"Base Date Score: {date_score}")
        print(f"Weekday Vibration: {week_vibe}")
        print(f"FINAL POWER SCORE: {final_score}")
        print("="*30)

    except ValueError as e:
        print(f"\n[Error]: {e}")
    except Exception as e:
        print(f"\n[Unexpected Error]: {e}")