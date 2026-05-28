import os
import sys

print("--- DIAGNOSTIC SCRIPT STARTING ---")

try:
    # 1. Check printing and the environment
    current_dir = os.getcwd()
    print(f"DEBUG 1: Python path: {sys.executable}")
    print(f"DEBUG 2: Current Working Directory (CWD) is: {current_dir}")
    
    # 2. Attempt to write a simple file to the CWD
    output_path = os.path.join(current_dir, 'diagnostic_test_output.txt')
    
    with open(output_path, 'w') as f:
        f.write("This file was successfully created by the diagnostic script.\n")
        f.write(f"CWD: {current_dir}")
        
    print(f"DEBUG 3: Successfully wrote a test file to: {output_path}")
    
except Exception as e:
    print("\n" + "!" * 50)
    print(f"!!! CRITICAL DIAGNOSTIC ERROR !!!")
    print(f"Root Cause: {e}")
    print("!!! FAILED TO EXECUTE OR WRITE FILE !!!")
    print("!" * 50)

print("--- DIAGNOSTIC SCRIPT FINISHED ---")