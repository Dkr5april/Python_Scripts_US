import re

def filter_person_messages(input_filename="whatsapp_chat.txt", output_filename="Filtered_Messages.txt", target_person="P V SATYARAMESH"):
    # Regex matching pattern for metadata: "15/04/26, 7:54 am - P V SATYARAMESH: "
    # Note: ([^:]+) captures the sender's name so we can check it
    whatsapp_pattern = re.compile(r'^\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*(?:[aApP][mM])?\s*-\s*([^:]+):\s*')
    system_pattern = re.compile(r'^\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*(?:[aApP][mM])?\s*-\s*')

    filtered_messages = []
    current_message = ""
    is_target_sender = False

    print(f"Reading {input_filename} and filtering for {target_person}...")
    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            for line in f:
                # Check for a new message from a person
                match = whatsapp_pattern.match(line)
                if match:
                    # If we were previously tracking a valid message, save it
                    if current_message and is_target_sender:
                        filtered_messages.append(current_message.strip())
                    
                    # Check if the sender matches our target person
                    sender_name = match.group(1).strip()
                    if sender_name.lower() == target_person.lower():
                        is_target_sender = True
                        current_message = line[match.end():]  # Capture text right after the name
                    else:
                        is_target_sender = False
                        current_message = ""
                    continue
                
                # Check for a system message (encryption alerts, group details)
                sys_match = system_pattern.match(line)
                if sys_match:
                    if current_message and is_target_sender:
                        filtered_messages.append(current_message.strip())
                    is_target_sender = False
                    current_message = ""
                    continue
                
                # Handle multi-line message continuation
                if is_target_sender and current_message:
                    current_message += "\n" + line
                elif is_target_sender and not current_message:
                    current_message = line

            # Catch the last message if it belongs to the target person
            if current_message and is_target_sender:
                filtered_messages.append(current_message.strip())
                
    except FileNotFoundError:
        print(f"Error: Could not find '{input_filename}'. Please check the filename.")
        return

    print(f"Writing filtered messages to {output_filename}...")
    
    # Save the filtered output to a clean text file
    with open(output_filename, 'w', encoding='utf-8') as out:
        for msg in filtered_messages:
            if msg:
                # Optional: Cleans markdown asterisks if desired
                clean_msg = msg.replace('**', '').replace('*', '')
                out.write(clean_msg + "\n\n" + "-"*40 + "\n\n")  # Separates messages cleanly
                
    print(f"Done! Clean text file saved as '{output_filename}'.")

if __name__ == "__main__":
    # You can change the target_person name to whoever you need to isolate
    filter_person_messages(
        input_filename="whatsapp_chat.txt", 
        output_filename="Astrology_Notes_Cleaned.txt", 
        target_person="P V SATYARAMESH"
    )