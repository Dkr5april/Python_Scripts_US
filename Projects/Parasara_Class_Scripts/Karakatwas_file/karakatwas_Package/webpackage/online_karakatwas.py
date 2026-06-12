import streamlit as st
import json
import re

# పేజీ సెటప్
st.set_page_config(page_title="Vedic Astrology Engine", layout="wide")

# డేటా లోడ్ చేయడం
def load_data():
    # 1. ప్రస్తుత పైథాన్ ఫైల్ ఉన్న ఫోల్డర్ పాత్‌ను కనుగొనండి
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. ఆ ఫోల్డర్ లోపల 'karakatwas.json' ఫైల్ పాత్‌ను తయారు చేయండి
    json_path = os.path.join(script_dir, 'karakatwas.json')
    
    # డీబగ్గింగ్ కోసం మాత్రమే (యాప్‌లో కనిపిస్తుంది)
    # st.write(f"Looking for file at: {json_path}")
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Error: ఫైల్ ఇక్కడ దొరకలేదు: {json_path}")
        st.write("ఈ ఫోల్డర్‌లో ఉన్న ఫైల్స్ ఇవి:", os.listdir(script_dir))
        return None

# లాంగ్వేజ్ ఎక్స్‌ట్రాక్షన్ లాజిక్
def extract_lang(text, lang):
    text = str(text)
    if lang == "Telugu":
        parts = text.split(',')
        telugu_parts = []
        for part in parts:
            match = re.search(r'\((.*?)\)', part)
            if match:
                telugu_parts.append(match.group(1).strip())
            else:
                telugu_pattern = re.compile(r'[\u0C00-\u0C7F]+')
                t = "".join(telugu_pattern.findall(part))
                if t: telugu_parts.append(t.strip())
        return ", ".join(telugu_parts)
    return re.sub(r'\s*\(.*?\)', '', text).strip()

# మెయిన్ యాప్
def main():
    st.title("Vedic Astrology Engine - Full Edition")
    
    data = load_data()
    if not data:
        return

    # Sidebar: Control Panel
    with st.sidebar:
        st.header("Control Panel")
        lang = st.radio("Language", ["English", "Telugu"])
        
        selected_items = {}
        for cat in ["rasi_karakatwas", "bhava_karakatwas", "graha_karakatwas", "nakshatra_karakatwas"]:
            if cat in data:
                st.subheader(cat.upper().replace("_", " "))
                for item in data[cat].keys():
                    if st.checkbox(item, key=f"{cat}_{item}"):
                        if cat not in selected_items: selected_items[cat] = []
                        selected_items[cat].append(item)
        
        execute = st.button("EXECUTE")

    # Main Area: Display
    if execute:
        for cat, items in selected_items.items():
            for item in items:
                st.divider()
                st.markdown(f"### >>> {item.upper()} <<<")
                data_obj = data[cat][item]
                
                for k, v in data_obj.items():
                    display_key = k.upper().replace("_", " ")
                    st.markdown(f"**{display_key}:**")
                    
                    if isinstance(v, dict):
                        for dk, dv in v.items():
                            st.write(f"- **{dk.upper()}**: {extract_lang(dv, lang)}")
                    elif isinstance(v, list):
                        for val in v:
                            st.write(f"- {extract_lang(val, lang)}")
                    else:
                        st.write(extract_lang(v, lang))

if __name__ == "__main__":
    main()