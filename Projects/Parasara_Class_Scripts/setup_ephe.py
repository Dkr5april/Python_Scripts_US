import os
import shutil
import sys

def automate_ephe_copy():
    print("=== PYJHORA EPHEMERIS INSTALLATION SYSTEM ===")
    
    # 1. Dynamically target the exact site-packages installation
    try:
        import jhora
        jhora_dir = os.path.dirname(jhora.__file__)
        target_ephe_dir = os.path.join(jhora_dir, "data", "ephe")
        print(f"[Detected] Active JHora package directory:\n  ↳ {jhora_dir}")
    except ImportError:
        print("[Error] PyJHora does not seem to be accessible in this Python environment.")
        return

    # 2. Ask you where your downloaded GitHub source repository folder sits
    print("\n[Action Needed]")
    source_input = input("Paste the absolute path to your downloaded/extracted 'ephe' folder:\n> ").strip()
    
    # Clean up formatting strings if copied with quotes
    source_ephe_dir = source_input.replace('"', '').replace("'", "")

    if not os.path.exists(source_ephe_dir):
        print(f"\n[Error] The source path you provided does not exist:\n  ↳ {source_ephe_dir}")
        print("Please check the folder name and make sure it contains files like 'seas_18.se1'.")
        return

    # 3. Double check that we are pointing at the right files
    source_files = os.listdir(source_ephe_dir)
    se1_files = [f for f in source_files if f.endswith('.se1')]
    
    if not se1_files:
        print(f"\n[Warning] The folder source doesn't contain any Swiss Ephemeris (.se1) files.")
        confirm = input("Are you absolutely sure this is the right 'ephe' directory? (yes/no): ").lower().strip()
        if confirm != 'yes':
            return

    # 4. Perform the secure automated copy
    print("\n[Processing] Migrating data files...")
    try:
        # Clear out existing empty directory or placeholder files completely
        if os.path.exists(target_ephe_dir):
            if os.path.isdir(target_ephe_dir):
                shutil.rmtree(target_ephe_dir)
            else:
                os.remove(target_ephe_dir)
        
        # Copy entire folder structure seamlessly
        shutil.copytree(source_ephe_dir, target_ephe_dir)
        print("\n" + "="*60)
        print("[SUCCESS] The full ephe folder has been cloned into place!")
        print(f"Destination: {target_ephe_dir}")
        print(f"Total files moved: {len(os.listdir(target_ephe_dir))}")
        print("="*60)
        
    except Exception as e:
        print(f"\n[Error] File system transfer failed: {e}")
        print("Tip: If permissions are locked, try running your Command Prompt as Administrator.")

if __name__ == "__main__":
    automate_ephe_copy()