# ==========================================
# DEBUG SCRIPT: DATE POWER ANALYSIS
# ==========================================

def debug_day_of_week(d, m, y):
    print(f"\n[DEBUG: Weekday Calculation]")
    # Zeller's style logic
    t = [0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4]
    if m < 3:
        y -= 1
    
    formula_step = (y + y // 4 - y // 100 + y // 400 + t[m - 1] + d)
    idx = formula_step % 7
    
    weekday_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    print(f"  -> Year Adjusted: {y}")
    print(f"  -> Formula Result: {formula_step}")
    print(f"  -> Weekday Index: {idx} ({weekday_names[idx]})")
    return idx

def debug_date_score(d, m, y):
    print(f"\n[DEBUG: Base Date Score]")
    date_str = f"{d}{m}{year}"
    
    # Show the individual digits being summed
    digits = [int(char) for char in date_str if char.isdigit()]
    digit_sum = sum(digits)
    
    print(f"  -> Date String: '{date_str}'")
    print(f"  -> Individual Digits: {' + '.join(map(str, digits))} = {digit_sum}")
    
    constant = 90
    base_score = digit_sum + d + constant
    print(f"  -> Logic: {digit_sum} (Sum) + {d} (Day) + {constant} (Fixed) = {base_score}")
    return base_score

# --- Main Execution ---
if __name__ == "__main__":
    print("--- STARTING NUMEROLOGY DEBUG ---")
    
    # Using your example: 05/04/1979
    day, month, year = 5, 4, 1979
    
    # 1. Debug Weekday
    wk_idx = debug_day_of_week(day, month, year)
    
    # 2. Debug Vibration (Chaldean Map)
    week_values = [1, 2, 9, 5, 3, 6, 8]
    vibe = week_values[wk_idx]
    print(f"\n[DEBUG: Weekday Vibration]")
    print(f"  -> Mapping Index {wk_idx} to Chaldean value: {vibe}")
    
    # 3. Debug Base Score
    base = debug_date_score(day, month, year)
    
    # 4. Final Total
    final = base + vibe
    print(f"\n[DEBUG: Final Assembly]")
    print(f"  -> {base} (Base) + {vibe} (Vibration) = {final}")
    
    print("\n" + "="*30)
    print(f" FINAL POWER SCORE: {final} ")
    print("="*30)