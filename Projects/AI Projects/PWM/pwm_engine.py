# pwm_engine.py
def compute_structural_weight(raw_val):
    # This formula lives in a completely separate file!
    factor = raw_val * 0.75
    adjusted_score = factor + 12
    return adjusted_score