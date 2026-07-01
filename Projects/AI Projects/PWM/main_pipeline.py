# main_pipeline.py
from pwm_engine import compute_structural_weight

input_signal = 80
print("Preparing to step across files...")

# 🔴 SET BREAKPOINT HERE (Line 7)
final_matrix_score = compute_structural_weight(input_signal)

print("Cross-file execution finished!")  # Your stop sign