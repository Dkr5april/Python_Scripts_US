import re

def convert_whatsapp_to_word_html(input_filename="whatsapp_chat.txt", output_filename="Astrology_Notes_Cleaned.html"):
    # Regex matching pattern for metadata: "15/04/26, 7:54 am - P V SATYARAMESH: "
    whatsapp_pattern = re.compile(r'^\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*(?:[aApP][mM])?\s*-\s*[^:]+:\s*')
    system_pattern = re.compile(r'^\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*(?:[aApP][mM])?\s*-\s*')

    cleaned_paragraphs = []
    current_paragraph = ""

    print(f"Reading {input_filename}...")
    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            for line in f:
                # Check for a new message from a person
                match = whatsapp_pattern.match(line)
                if match:
                    if current_paragraph:
                        cleaned_paragraphs.append(current_paragraph.strip())
                    current_paragraph = line[match.end():]
                    continue
                
                # Check for a system message (encryption alerts, group details)
                sys_match = system_pattern.match(line)
                if sys_match:
                    if current_paragraph:
                        cleaned_paragraphs.append(current_paragraph.strip())
                    current_paragraph = ""
                    continue
                
                # Handle paragraph continuation lines
                if current_paragraph:
                    current_paragraph += "\n" + line
                else:
                    current_paragraph = line

            if current_paragraph:
                cleaned_paragraphs.append(current_paragraph.strip())
    except FileNotFoundError:
        print(f"Error: Could not find '{input_filename}'. Please check the filename.")
        return

    print("Formatting and building clean document...")
    # Generating clean HTML structural output that Word interprets flawlessly
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
            
            # Drop redundant markdown asterisks from the text
            para = para.replace('**', '').replace('*', '')
            lines = [l.strip() for l in para.split('\n') if l.strip()]
            if not lines:
                continue
                
            first_line = lines[0]
            out.write('<div class="section-box">\n')
            
            # Automatically assign header if first line looks like a title element
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
    print(f"Done! Open '{output_filename}' in Microsoft Word to view your beautifully formatted text.")

if __name__ == "__main__":
    convert_whatsapp_to_word_html()