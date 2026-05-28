import re

def filter_group_chat_by_people(input_filename="whatsapp_group_chat.txt", output_filename="Filtered_Group_Notes.html"):
    
    # =========================================================================
    # EDIT THIS LIST: Put the exact WhatsApp names of the people you want to keep
    # =========================================================================
    TARGET_PEOPLE = ["P V SATYARAMESH", "Koteswar", "Hari anna"] 
    
    # Regex to capture the timestamp and the sender's name dynamically
    # Group 1 captures the date/time info, Group 2 captures the exact Sender Name
    whatsapp_msg_pattern = re.compile(r'^(\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*(?:[aApP][mM])?\s*-\s*)([^:]+):\s*')
    system_pattern = re.compile(r'^\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*(?:[aApP][mM])?\s*-\s*')

    cleaned_paragraphs = []
    current_paragraph = ""
    keep_current_message = False

    print(f"Reading and filtering group chat from '{input_filename}'...")
    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            for line in f:
                # Check if this line is a new message from a person
                match = whatsapp_msg_pattern.match(line)
                
                if match:
                    # Save the previous message if we were tracking one and it belonged to a target person
                    if keep_current_message and current_paragraph.strip():
                        cleaned_paragraphs.append(current_paragraph.strip())
                    
                    sender_name = match.group(2).strip()
                    
                    # Check if the sender is in our approved list
                    if sender_name in TARGET_PEOPLE:
                        keep_current_message = True
                        # Strip out the metadata and store the text, labeling who said it
                        current_paragraph = f"[{sender_name}]: " + line[match.end():]
                    else:
                        keep_current_message = False
                        current_paragraph = ""
                    continue
                
                # Check if it's a system message (skip these entirely)
                if system_pattern.match(line):
                    if keep_current_message and current_paragraph.strip():
                        cleaned_paragraphs.append(current_paragraph.strip())
                    keep_current_message = False
                    current_paragraph = ""
                    continue
                
                # If it's a multi-line message continuation line
                if keep_current_message:
                    current_paragraph += "\n" + line

            # Catch the very last message in the file
            if keep_current_message and current_paragraph.strip():
                cleaned_paragraphs.append(current_paragraph.strip())
                
    except FileNotFoundError:
        print(f"Error: Could not find '{input_filename}'. Please check the filename.")
        return

    print(f"Filtering complete. Found messages matching your target list.")
    print("Generating beautifully formatted document...")

    # Write out the clean HTML file
    with open(output_filename, 'w', encoding='utf-8') as out:
        out.write('''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Filtered Group Chat Notes</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; margin: 40px; background-color: #fbf9f6; }
        h1 { color: #2c3e50; text-align: center; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; font-size: 22pt; font-weight: bold; }
        h4 { color: #d35400; font-size: 11pt; margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 1px; }
        p { text-align: justify; margin-bottom: 10px; font-size: 11pt; }
        .msg-box { background: #ffffff; padding: 18px; border-radius: 6px; margin-bottom: 15px; border: 1px solid #e2dcd5; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        ul { margin-bottom: 10px; padding-left: 20px; }
        li { margin-bottom: 5px; font-size: 11pt; }
    </style>
</head>
<body>
    <h1>వైదిక జ్యోతిష్య సమూహ గమనికలు (Filtered Group Chat Notes)</h1>
''')
        
        for para in cleaned_paragraphs:
            if not para:
                continue
            
            # Clean up formatting artifacts
            para = para.replace('**', '').replace('*', '')
            
            # Extract the sender tag we injected earlier e.g., "[Sender Name]:"
            parts = para.split(']: ', 1)
            if len(parts) == 2:
                sender_header = parts[0].replace('[', '')
                message_body = parts[1]
            else:
                sender_header = "Unknown"
                message_body = para
                
            out.write('<div class="msg-box">\n')
            out.write(f'    <h4>✍️ Sender: {sender_header}</h4>\n')
            
            lines = [l.strip() for l in message_body.split('\n') if l.strip()]
            for sub_line in lines:
                if sub_line.startswith('-') or sub_line.startswith('•'):
                    clean_li = sub_line.lstrip('-• ').strip()
                    out.write(f'    <ul><li>{clean_li}</li></ul>\n')
                else:
                    out.write(f'    <p>{sub_line}</p>\n')
                    
            out.write('</div>\n\n')
            
        out.write('''</body>
</html>''')
    print(f"Success! Open '{output_filename}' in Word to see the compiled notes.")

if __name__ == "__main__":
    filter_group_chat_by_people()