import re

def convert_whatsapp_to_word_html(input_filename="whatsapp_chat.txt", output_filename="Astrology_Notes_Cleaned.html"):
    target_pattern = re.compile(
        r'^\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*(?:[aApP][mM])?\s*-\s*P\s*V\s*SATYA\s*RAMESH\s*:\s*', 
        re.IGNORECASE
    )
    any_user_pattern = re.compile(r'^\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*(?:[aApP][mM])?\s*-\s*[^:]+:\s*')
    system_pattern = re.compile(r'^\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*(?:[aApP][mM])?\s*-\s*')
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
                if media_placeholder_pattern.search(line) and len(line.strip()) < 50:
                    continue

                target_match = target_pattern.match(line)
                if target_match:
                    if current_paragraph and is_target_user:
                        cleaned_paragraphs.append(current_paragraph.strip())
                    current_paragraph = line[target_match.end():]
                    is_target_user = True
                    continue

                any_user_match = any_user_pattern.match(line)
                if any_user_match:
                    if current_paragraph and is_target_user:
                        cleaned_paragraphs.append(current_paragraph.strip())
                    current_paragraph = ""
                    is_target_user = False  
                    continue
                
                sys_match = system_pattern.match(line)
                if sys_match:
                    if current_paragraph and is_target_user:
                        cleaned_paragraphs.append(current_paragraph.strip())
                    current_paragraph = ""
                    is_target_user = False  
                    continue
                
                if is_target_user and current_paragraph:
                    current_paragraph += "\n" + line
                elif is_target_user and not current_paragraph:
                    current_paragraph = line

            if current_paragraph and is_target_user:
                cleaned_paragraphs.append(current_paragraph.strip())
                
    except FileNotFoundError:
        print(f"Error: Could not find '{input_filename}'. Please check the filename.")
        return

    print(f"Formatting compact document (Found {len(cleaned_paragraphs)} message blocks)...")
    
    with open(output_filename, 'w', encoding='utf-8') as out:
        out.write('''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Vedic Astrology Cleaned Notes</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.5; color: #333; margin: 40px; background-color: #ffffff; }
        h1 { color: #8B4513; text-align: center; border-bottom: 2px solid #8B4513; padding-bottom: 10px; font-size: 22pt; font-weight: bold; margin-bottom: 30px; }
        h3 { color: #A0522D; font-size: 13pt; margin-top: 20px; margin-bottom: 8px; font-weight: bold; }
        p { text-align: justify; margin-bottom: 8px; font-size: 11pt; }
        .rule-divider { border: 0; border-top: 1px dashed #e2dcd5; margin: 15px 0; }
        ul { margin-bottom: 8px; padding-left: 20px; }
        li { margin-bottom: 4px; font-size: 11pt; list-style-type: square; }
    </style>
</head>
<body>
    <h1>వైదిక జ్యోతిష్య శాస్త్ర సూత్రాలు (Vedic Astrology Notes)</h1>
''')
        
        section_count = 1
        for para in cleaned_paragraphs:
            if not para:
                continue
            
            para = para.replace('**', '').replace('*', '')
            para = media_placeholder_pattern.sub('', para)
            
            lines = [l.strip() for l in para.split('\n') if l.strip()]
            if not lines:
                continue
                
            first_line = lines[0]
            
            # Use a simple dash line divider instead of heavy boxes to prevent artificial page splits
            if section_count > 1:
                out.write('<hr class="rule-divider" />\n')
            
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
                    
        out.write('</body>\n</html>')
    print(f"Done! Open '{output_filename}' in Microsoft Word.")

if __name__ == "__main__":
    convert_whatsapp_to_word_html()