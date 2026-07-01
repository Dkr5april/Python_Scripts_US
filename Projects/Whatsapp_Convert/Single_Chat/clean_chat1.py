import re

def convert_whatsapp_to_word_html(input_filename="whatsapp_chat.txt", output_filename="Astrology_Notes_Cleaned.html"):
    # Match ONLY PV Satya Ramesh's messages
    target_pattern = re.compile(
        r'^\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*(?:[aApP][mM])?\s*-\s*P\s*V\s*SATYA\s*RAMESH\s*:\s*', 
        re.IGNORECASE
    )
    
    # General pattern to catch WHEN a new message starts from ANYONE ELSE
    any_user_pattern = re.compile(r'^\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*(?:[aApP][mM])?\s*-\s*[^:]+:\s*')
    system_pattern = re.compile(r'^\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*(?:[aApP][mM])?\s*-\s*')

    # Regex to catch various WhatsApp media/image text placeholders
    # This filters out <Media omitted>, [Image], (file attached), etc.
    media_placeholder_pattern = re.compile(
        r'(<Media\s*omitted>|\[.*?image.*?\]|\[.*?video.*?\]|\[.*?sticker.*?\]|\(.*?attached.*\))', 
        re.IGNORECASE
    )

    cleaned_paragraphs = []
    current_paragraph = ""
    is_target_user = False  

    print(f"Reading {input_filename}...")
    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            for line in f:
                # Skip the line entirely if it only contains a WhatsApp media placeholder
                if media_placeholder_pattern.search(line) and len(line.strip()) < 50:
                    continue

                # Check if it's a message from PV Satya Ramesh
                target_match = target_pattern.match(line)
                if target_match:
                    if current_paragraph and is_target_user:
                        cleaned_paragraphs.append(current_paragraph.strip())
                    
                    current_paragraph = line[target_match.end():]
                    is_target_user = True
                    continue

                # Check if it's a message from a DIFFERENT user
                any_user_match = any_user_pattern.match(line)
                if any_user_match:
                    if current_paragraph and is_target_user:
                        cleaned_paragraphs.append(current_paragraph.strip())
                    
                    current_paragraph = ""
                    is_target_user = False  
                    continue
                
                # Check for a system message
                sys_match = system_pattern.match(line)
                if sys_match:
                    if current_paragraph and is_target_user:
                        cleaned_paragraphs.append(current_paragraph.strip())
                    
                    current_paragraph = ""
                    is_target_user = False  
                    continue
                
                # Handle multi-line message continuations
                if is_target_user and current_paragraph:
                    current_paragraph += "\n" + line
                elif is_target_user and not current_paragraph:
                    current_paragraph = line

            # Append the last paragraph if it belongs to him
            if current_paragraph and is_target_user:
                cleaned_paragraphs.append(current_paragraph.strip())
                
    except FileNotFoundError:
        print(f"Error: Could not find '{input_filename}'. Please check the filename.")
        return

    print(f"Formatting and building clean document (Found {len(cleaned_paragraphs)} message blocks)...")
    
    with open(output_filename, 'w', encoding='utf-8') as out:
        out.write('''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Vedic Astrology Cleaned Notes</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; margin: 40px; background-color: #fcfbfa; }
        h1 { color: #8B4513; text-align: center; border-bottom: 2px solid #8B4513; padding-bottom: 10px; font-size: 24pt; font-weight: bold; }
        h3 { color: #A0522D; font-size: 15pt; margin-top: 30px; border-left: 5px solid #A0522D; padding-left: 12px; margin-bottom: 15px; }
        p { text-align: justify; margin-bottom: 12px; font-size: 11pt; text-indent: 10px; }
        .section-box { background: #ffffff; padding: 22px; border-radius: 6px; margin-bottom: 25px; border: 1px solid #e2dcd5; }
        ul { margin-bottom: 12px; padding-left: 20px; }
        li { margin-bottom: 6px; font-size: 11pt; list-style-type: square; }
    </style>
</head>
<body>
    <h1>వైదిక జ్యోతిష్య శాస్త్ర సూత్రాలు (Vedic Astrology Notes)</h1>
''')
        
        section_count = 1
        for para in cleaned_paragraphs:
            if not para:
                continue
            
            # Clean up residual markers
            para = para.replace('**', '').replace('*', '')
            
            # Inline clean up if a media tag sneaked into a multi-line paragraph
            para = media_placeholder_pattern.sub('', para)
            
            lines = [l.strip() for l in para.split('\n') if l.strip()]
            if not lines:
                continue
                
            first_line = lines[0]
            out.write('<div class="section-box">\n')
            
            if len(first_line) < 90 and any(char in first_line for char in [':', '–', '-', '(', 'Classification', 'Notes']):
                out.write(f'    <h3>{section_count}. {first_line}</h3>\n')
                section_count += 1
                remaining_lines = lines[1:]
            else:
                out.write(f'    <h3>{section_count}. జ్యోతిష్య సూత్రం (Astrology Principle)</h3>\n')
                section_count += 1
                remaining_lines = lines
                
            for sub_line in remaining_lines:
                if sub_line.startswith('-') or sub_line.startswith('•'):
                    clean_li = sub_line.lstrip('-• ').strip()
                    out.write(f'    <ul><li>{clean_li}</li></ul>\n')
                else:
                    out.write(f'    <p>{sub_line}</p>\n')
                    
            out.write('</div>\n\n')
            
        out.write('</body>\n</html>')
    print(f"Done! Open '{output_filename}' in Microsoft Word.")

if __name__ == "__main__":
    convert_whatsapp_to_word_html()