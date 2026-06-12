import os

def find_tk_in_files(directory):
    # మీరు వెతకాల్సిన పదం
    search_term = "tk."
    
    # వెతకకూడని ఫోల్డర్లు (ఉదా: .git లేదా __pycache__)
    exclude_dirs = {'.git', '__pycache__', 'venv'}

    print(f"'{search_term}' కోసం వెతకడం మొదలైంది...\n")

    for root, dirs, files in os.walk(directory):
        # ఎక్స్‌క్లూడ్ చేయాల్సిన ఫోల్డర్లను వదిలేయడానికి
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith(".py"):  # కేవలం పైథాన్ ఫైల్స్ మాత్రమే
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            if search_term in line:
                                print(f"Found in: {file_path} (Line {i+1})")
                                print(f"  -> {line.strip()}\n")
                except Exception as e:
                    print(f"Could not read {file_path}: {e}")

if __name__ == "__main__":
    # మీ ప్రస్తుత ఫోల్డర్ నుండి వెతకడం మొదలుపెడుతుంది
    current_directory = os.getcwd()
    find_tk_in_files(current_directory)
    print("వెతకడం పూర్తయింది.")