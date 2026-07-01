import streamlit as st
import os
from engine import CompatibilityEngine
from ephemeris_logic import AstroEngine

# 1. Setup Engines
@st.cache_resource
def get_engine():
    # 'base_dir' is the root folder where your scripts and JSONs live
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return CompatibilityEngine(base_dir)

# Initialize Engines
calc_engine = AstroEngine()
engine = get_engine()

st.title("✨ Marriage Compatibility Matcher")

# 2. Automated Birth Calculation Tool
with st.expander("⚙️ Auto-Calculate Birth Details (Use for accurate stars/rasi)"):
    col_a, col_b = st.columns(2)
    with col_a:
        dob = st.date_input("Birth Date")
        tob = st.time_input("Birth Time (HH:MM)")
    with col_b:
        lat = st.number_input("Latitude", value=16.1176)
        lon = st.number_input("Longitude", value=80.9314)
    
    target = st.radio("Calculate for:", ["Boy", "Girl"])
    if st.button("Perform Calculation"):
        data = calc_engine.calculate_birth_data(dob.year, dob.month, dob.day, tob.hour, tob.minute, lat, lon)
        st.session_state[f'{target.lower()}_rasi'] = data['rasi']
        st.session_state[f'{target.lower()}_star'] = data['moon_star']
        st.session_state[f'{target.lower()}_house'] = data['mars_house']
        st.success(f"Calculated {target}: {data['rasi'].upper()} / {data['moon_star'].upper()}")

# 3. UI Input Forms
col1, col2 = st.columns(2)
planets = ["sun", "moon", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]

with col1:
    st.subheader("👦 Boy Profile")
    b_rasi = st.selectbox("Rasi", ["mesha", "vrishabha", "mithuna", "karkataka", "simha", "kanya", "tula", "vrischika", "dhanur", "makara", "kumbha", "meena"], index=0, key="boy_rasi")
    b_star = st.selectbox("Star", ["aswini", "bharani", "krithika", "rohini", "mrigasira", "arudra", "punarvasu", "pushyami", "aslesha", "makha", "pubba", "uttara", "hastha", "chitta", "swathi", "visakha", "anuradha", "jyestha", "moola", "p.ashadha", "u.ashadha", "sravana", "dhanistha", "satabhisha", "p.bhadra", "u.bhadra", "revathi"], key="boy_star")
    b_house = st.number_input("Mars House (1-12)", 1, 12, value=st.session_state.get('boy_house', 1), key="boy_house_val")
    b_conj = st.multiselect("Planets conjoined with Mars", planets, key="boy_conj")

with col2:
    st.subheader("👧 Girl Profile")
    g_rasi = st.selectbox("Rasi", ["mesha", "vrishabha", "mithuna", "karkataka", "simha", "kanya", "tula", "vrischika", "dhanur", "makara", "kumbha", "meena"], index=0, key="girl_rasi")
    g_star = st.selectbox("Star", ["aswini", "bharani", "krithika", "rohini", "mrigasira", "arudra", "punarvasu", "pushyami", "aslesha", "makha", "pubba", "uttara", "hastha", "chitta", "swathi", "visakha", "anuradha", "jyestha", "moola", "p.ashadha", "u.ashadha", "sravana", "dhanistha", "satabhisha", "p.bhadra", "u.bhadra", "revathi"], key="girl_star")
    g_house = st.number_input("Mars House (1-12)", 1, 12, value=st.session_state.get('girl_house', 1), key="girl_house_val")
    g_conj = st.multiselect("Planets conjoined with Mars", planets, key="girl_conj")

# 4. Result Processing
if st.button("Check Compatibility", use_container_width=True):
    rasi_ok = engine.check_rasi_compatibility(b_rasi, g_rasi)
    rajju_ok = engine.check_rajju_dosha(b_star, g_star)
    tara_ok = engine.check_tara_balam(b_star, g_star)
    
    b_kuja = engine.check_kuja_dosha({'house': b_house, 'lagna': b_rasi, 'conjoined': b_conj})
    g_kuja = engine.check_kuja_dosha({'house': g_house, 'lagna': g_rasi, 'conjoined': g_conj})
    
    st.divider()
    st.write("### Compatibility Results")
    st.write(f"Rasi Match: {'✅' if rasi_ok else '❌'}")
    st.write(f"Rajju Dosha: {'✅ Clear' if rajju_ok else '❌ Detected'}")
    st.write(f"Tara Balam: {'✅ Favorable' if tara_ok else '❌ Avoid (3, 5, 7)'}")
    
    if b_kuja or g_kuja:
        st.warning(f"⚠️ Kuja Dosha: Boy={'Active' if b_kuja else 'Clear'}, Girl={'Active' if g_kuja else 'Clear'}")
    else:
        st.success("✅ No Kuja Dosha detected")