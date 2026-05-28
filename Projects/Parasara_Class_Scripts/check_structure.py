import jhora
import os

print("=== PyJHora 4.8.5 Directory Structure ===")
jhora_path = os.path.dirname(jhora.__file__)
print(f"Location: {jhora_path}\n")

print("[Contents of jhora folder]:")
for item in os.listdir(jhora_path):
    item_path = os.path.join(jhora_path, item)
    if os.path.isdir(item_path):
        print(f" Directory: {item}/")
        # Print subdirectories to see where drik or computation files went
        try:
            sub_items = os.listdir(item_path)
            print(f"   ↳ Contains: {sub_items[:5]} ... (Total {len(sub_items)} items)")
        except:
            pass
    else:
        if item.endswith('.py'):
            print(f" File:      {item}")