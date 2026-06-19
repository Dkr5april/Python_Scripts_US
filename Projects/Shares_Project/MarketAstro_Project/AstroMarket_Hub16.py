import os
import sys
import urllib.parse
from datetime import datetime, timedelta

# 1. Get the current directory of this specific script file
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Tell Python to look inside this folder for modules like 'engine' and 'logic'
if current_dir not in sys.path:
    sys.path.append(current_dir)

# ==========================================================
# CORE DASHBOARD DEPENDENCIES
# ==========================================================
import streamlit as st

# Core Backend Framework Modules
import config
from engine.astro_engine import AstroEngine
from engine.market_dasa import get_market_dasa_levels
from logic.rules_processor import evaluate_market_rules

# Import the Wave Trend Analyser
from logic.market_trend_analyzer import analyze_market_trends, create_compact_trend_chart

# 1. Page Configuration
st.set_page_config(page_title="KP Astro Market Dashboard", layout="wide")

# 2. Initialize Backend Engine Instance
@st.cache_resource
def load_engine():
    return AstroEngine()

astro = load_engine()

# # 3. Handle Session State Controls (Forces initialization to Mumbai IST Date)
if "view_date" not in st.session_state:
    # Calculate the current time in India (UTC + 5:30) by shifting the server's UTC time directly
    utc_now = datetime.utcnow()
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    
    # Set the initial view date to Mumbai's current date, hardcoding market opening hours to 9:30 AM
    st.session_state.view_date = ist_now.replace(hour=9, minute=30, second=0, microsecond=0)

if "lat" not in st.session_state or "lon" not in st.session_state:
    st.session_state.lat = 18.5800
    st.session_state.lon = 72.5000
    st.session_state.location_name = "Mumbai (Bombay)"

# 4. Sidebar Controller Panel
st.sidebar.header("⏱️ Control Panel")

location_options = ["Mumbai (Bombay)", "Default (Machilipatnam)"]
try:
    current_idx = location_options.index(st.session_state.location_name)
except (ValueError, AttributeError):
    current_idx = 0

location_option = st.sidebar.selectbox(
    "Select Location",
    options=location_options,
    index=current_idx
)

# Sync coordinate overrides seamlessly on modification
if location_option != st.session_state.location_name:
    st.session_state.location_name = location_option
    if location_option == "Mumbai (Bombay)":
        st.session_state.lat = 18.5800
        st.session_state.lon = 72.5000
    else:
        st.session_state.lat = 16.1176
        st.session_state.lon = 80.9314
    st.rerun()

new_date = st.sidebar.date_input("Pick Date", value=st.session_state.view_date.date())
new_time = st.sidebar.time_input("Pick Time", value=st.session_state.view_date.time())
st.session_state.view_date = datetime.combine(new_date, new_time)

st.sidebar.subheader("Quick Navigation")
col_b1, col_b2 = st.sidebar.columns(2)
with col_b1:
    if st.button("⬅️ -5 Mins"):
        st.session_state.view_date -= timedelta(minutes=5)
        st.rerun()
    if st.button("⬅️ -1 Day"):
        st.session_state.view_date -= timedelta(days=1)
        st.rerun()
with col_b2:
    if st.button("+5 Mins ➡️"):
        st.session_state.view_date += timedelta(minutes=5)
        st.rerun()
    if st.button("+1 Day ➡️"):
        st.session_state.view_date += timedelta(days=1)
        st.rerun()

# --- SCREEN TOGGLE FEATURE ---
st.sidebar.markdown("---")
st.sidebar.subheader("🖥️ View View Mode")
view_mode = st.sidebar.radio(
    "Select Screen Content",
    options=["Standard Dashboard", "KP Rules Detailed Screen"],
    index=0
)

# 5. Connect Dynamic UI Coordinates to Astro Engine Contexts
astro.lat = st.session_state.lat
astro.lon = st.session_state.lon

if hasattr(config, 'LATITUDE'): config.LATITUDE = st.session_state.lat
if hasattr(config, 'LONGITUDE'): config.LONGITUDE = st.session_state.lon

view_date = st.session_state.view_date

# Fetch Calculations Snapshot Data Match tracking main.py pipeline
data = astro.get_full_snapshot(view_date)
logic = evaluate_market_rules(data, view_date)

m_lon = data["Mo"]["lon"]
m_lord = data["Mo"]["lord"]
dasa = get_market_dasa_levels(view_date, m_lon, m_lord)

# Parse underlying chains out of evaluate_market_rules execution scope safely
X = data["Mo"]["lord"]
Y = data[X]["lord"] if X in data else "N/A"

# CRITICAL FILTER: Explicitly exclude 'Asc' and 'Lagna' from stellar chains for the wave engines
x_chain = [p for p, d in data.items() if d["lord"] == X and p not in ["Mo", X, "Asc", "Lagna"]]
y_chain = [p for p, d in data.items() if d["lord"] == Y and p not in [X, Y, "Asc", "Lagna"]]

# ==========================================================
# DYNAMIC ASTROLOGICAL WAVE TRENDS CALCULATOR
# ==========================================================
# Filter snapshot copy to protect wave trend processing from seeing Ascendant anomalies
wave_safe_data = {k: v for k, v in data.items() if k not in ["Asc", "Lagna"]}
trend_nodes = analyze_market_trends(wave_safe_data)
trend_html_blocks = ""

if trend_nodes:
    for node in trend_nodes:
        # Extra layer of security ensuring Ascendant waves never output dynamically
        if node.get('label', '') in ["Asc", "Lagna"]:
            continue
        trend_html_blocks += f"""
        <div style="border: 1px solid #38444d; padding: 12px; border-radius: 4px; background-color: #0c0f12; margin-bottom: 10px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 4px;">
                <span style="color:#ffffff; font-weight:bold; font-size:14px;">{node['label']}</span>
                <span style="color:{node['color']}; font-weight:bold; font-size:13px; text-transform:uppercase;">{node['trend']}</span>
            </div>
            <div style="color:#8b949e; font-size:12px;">
                Planet Impact: <span style="color:#ffb86c; font-weight:bold;">{node['p_text']}</span> | House Trend: <span style="color:#8be9fd; font-weight:bold;">House {node['house']} ({node['h_text']})</span>
            </div>
            <div style="color:#6272a4; font-size:11px; margin-top:2px;">
                Calculated Distance Offset: {node['dist']:.4f}°
            </div>
        </div>
        """

# 6. Star Lord Color Highlighting Layout Map
palette = ["#ff5555", "#50fa7b", "#f1fa8c", "#bd93f9", "#ff79c6", "#8be9fd", "#ffb86c", "#ff6e6e", "#6272a4"]
unique_lords = list(set([details.get("lord") for details in data.values() if details.get("lord")]))
lord_color_map = {lord: palette[i % len(palette)] for i, lord in enumerate(unique_lords)}

lord_counts = {}
for details in data.values():
    l = details.get("lord")
    if l: lord_counts[l] = lord_counts.get(l, 0) + 1

# 7. Format Outputs & Build HTML Table
dasa_text = " > ".join(dasa) if isinstance(dasa, list) else str(dasa)

table_rows = ""
entity_order = ["Asc", "Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke", "Ur", "Ne", "Pl"]
available_keys = list(data.keys())

execution_order = []
for ent in entity_order:
    if ent in available_keys:
        execution_order.append(ent)
    elif ent == "Asc" and "Lagna" in available_keys:
        execution_order.append("Lagna")

for remaining in available_keys:
    if remaining not in execution_order and remaining not in ["Lagna", "Asc"]:
        execution_order.append(remaining)

for entity in execution_order:
    details = data[entity]
    
    if entity in ["Lagna", "Asc"]:
        ent_color = "#ff79c6"
    elif entity in ["Ur", "Ne", "Pl"]:
        ent_color = "#8be9fd"
    else:
        ent_color = "#ffffff"
        
    status_str = details.get("status", "DIR")
    status_color = "#ff5555" if status_str == "RETRO" else "#50fa7b"
    
    raw_lon = details.get('lon', 0.0)
    sign_relative_deg = raw_lon % 30
    house_num = details.get('house', '1' if entity in ["Lagna", "Asc"] else '-')
    
    star_name = details.get('star', 'N/A')
    lord_name = details.get('lord', 'N/A')
    
    star_display_color = "#ffffff"
    if lord_counts.get(lord_name, 0) > 1 and entity not in ["Lagna", "Asc"]:
        star_display_color = lord_color_map.get(lord_name, "#ffffff")
        
    table_rows += f"""
    <tr style="border-bottom: 1px solid #21262d;">
        <td style="padding:6px; color:{ent_color}; font-weight:bold;">{entity}</td>
        <td style="padding:6px; color:{star_display_color};">{star_name} ({lord_name})</td>
        <td style="padding:8px; color:#ffffff; font-weight:bold; text-align:center;">{house_num}</td>
        <td style="padding:6px; color:#ffffff; text-align:center;">{details.get('pada', '-')}</td>
        <td style="padding:6px; color:#ffffff;">{sign_relative_deg:.4f}°</td>
        <td style="padding:6px; color:{status_color}; font-weight:bold;">{status_str}</td>
    </tr>
    """

# ==========================================================
# 8. STRICT PARSING FOR KP RULES & SPECIFIC X/Y CHAINS ONLY
# ==========================================================
rules_rows = ""

def add_rule_line(label, value):
    global rules_rows
    text = str(value).strip()
    upper = text.upper()

    if "PASS" in upper:
        color = "#50fa7b"
        display = "PASS"
    elif "FAIL" in upper:
        color = "#ff5555"
        display = "FAIL"
    else:
        color = "#f1fa8c"
        display = text

    rules_rows += f"""
    <div class="rule-line">
        <span style="color:white;">{label.strip()}:</span>
        <span style="color:{color}; font-weight:bold;">{display}</span>
    </div>
    """

for key, value in logic.items():
    key_text = str(key).strip()
    key_upper = key_text.upper()

    is_valid_rule = key_upper.startswith(("R1", "R2", "R3", "R4", "R5"))
    is_clean_chain_item = (
        (key_upper.startswith("X") or key_upper.startswith("Y")) 
        and any(char.isdigit() for char in key_upper)
    )

    if is_valid_rule or is_clean_chain_item:
        if isinstance(value, (list, dict)):
            for item in (value if isinstance(value, list) else value.items()):
                txt = str(item)
                if ":" in txt:
                    add_rule_line(txt.split(":")[0], txt.split(":")[-1])
                else:
                    add_rule_line(key_text, txt)
        else:
            if ":" in str(value):
                add_rule_line(str(value).split(":")[0], str(value).split(":")[-1])
            else:
                add_rule_line(key_text, value)
        continue

    if key_upper in ["RULE_RESULTS", "RULES", "RESULTS"]:
        if isinstance(value, list):
            for item in value:
                txt = str(item)
                if txt.strip() and ":" in txt:
                    add_rule_line(txt.split(":")[0], txt.split(":")[-1])
        else:
            lines = str(value).split("\n")
            for line in lines:
                if ":" in line:
                    add_rule_line(line.split(":")[0], line.split(":")[-1])

# ==========================================================
# 9. HTML LAYOUT CONTROLLERS WITH NATIVE X-Y TREND INJECTION
# ==========================================================
x_chain_val = ", ".join(x_chain) if x_chain else "None"
y_chain_val = ", ".join(y_chain) if y_chain else "None"

if view_mode == "KP Rules Detailed Screen":
    dashboard_grid_content = f"""
    <div style="width: 100%;">
        <div class="box-container" style="padding: 20px;">
            <div class="box-title" style="font-size: 1.1rem; margin-bottom: 20px;">KP Trading Rules (Detailed View)</div>
            <div class="rule-header">
                X: {logic.get('X', X)} | Y: {logic.get('Y', Y)}
            </div>
            <div style="margin-top: 15px;">
                {rules_rows}
            </div>
            <div style="margin-top: 25px; border-top: 1px dashed #30363d; padding-top: 15px;">
                <div class="box-title">X & Y Dynamic Wave Trends</div>
                {trend_html_blocks if trend_html_blocks else "<div style='color:#6272a4;'>No Active Structural Waves Found</div>"}
            </div>
            <div style="margin-top: 30px; border-top: 1px solid #38444d; padding-top: 15px;">
                <div style="color: #8b949e; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 10px; font-weight: bold;">Chain Depths Reference:</div>
                <div class="chain-box-container">
                    <span class="chain-item">X-Chain: <span style='color:#bd93f9; font-weight:bold;'>{x_chain_val}</span></span>
                    <span class="chain-item">Y-Chain: <span style='color:#bd93f9; font-weight:bold;'>{y_chain_val}</span></span>
                </div>
            </div>
        </div>
    </div>
    """
else:
    dashboard_grid_content = f"""
    <div class="dashboard-grid">
        <div class="box-container table-scroll-container">
            <div class="box-title">Sidereal Celestial Metrics (Lahiri)</div>
            <table>
                <tr style="border-bottom: 2px solid #38444d; color:#ff79c6; font-weight:bold;">
                    <th style="padding:6px;">Entity</th>
                    <th style="padding:6px;">Star (Lord)</th>
                    <th style="padding:6px; text-align:center;">House</th>
                    <th style="padding:6px; text-align:center;">Pada</th>
                    <th style="padding:6px;">Deg</th>
                    <th style="padding:6px;">Status</th>
                </tr>
                {table_rows}
            </table>
        </div>
        <div class="sidebar-widgets-stack">
            <div class="box-container">
                <div class="box-title">6-Hour Market Dasa</div>
                <div style="color:#8be9fd; font-weight:bold; margin-bottom:6px; font-size:0.8rem;">Maha &gt; Antar &gt; Pratyantar:</div>
                <div class="dasa-highlight-text">{dasa_text}</div>
            </div>
            <div class="box-container">
                <div class="box-title">X & Y Structural Wave Trends</div>
                {trend_html_blocks if trend_html_blocks else "<div style='color:#6272a4;'>No Active Waves Found</div>"}
            </div>
            <div class="box-container">
                <div class="box-title">KP Trading Rules</div>
                <div class="rule-header">X: {logic.get('X', X)} | Y: {logic.get('Y', Y)}</div>
                {rules_rows}
            </div>
            <div class="box-container">
                <div class="box-title">Stellar Chain Depth</div>
                <div style="margin-bottom:6px;">X-Chain: <span style='color:#bd93f9; font-weight:bold;'>{x_chain_val}</span></div>
                <div>Y-Chain: <span style='color:#bd93f9; font-weight:bold;'>{y_chain_val}</span></div>
            </div>
        </div>
    </div>
    """

complete_html_page = f"""
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            background-color: #0c0f12;
            color: #ffffff;
            font-family: 'Courier New', Courier, monospace;
            margin: 0;
            padding: 8px;
            font-size: 14px;
        }}
        .header-banner {{
            background-color: #161b22;
            padding: 10px;
            border-radius: 4px;
            border: 1px solid #38444d;
            margin-bottom: 12px;
            font-size: 0.95rem;
            line-height: 1.4;
        }}
        .dashboard-grid {{
            display: grid;
            grid-template-columns: 1.3fr 0.7fr;
            gap: 12px;
        }}
        .sidebar-widgets-stack {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        .box-container {{
            border: 1px solid #38444d;
            border-radius: 4px;
            padding: 12px;
            background-color: #000000;
        }}
        .table-scroll-container {{
            overflow-x: auto;
        }}
        .box-title {{
            color: #8b949e;
            border-bottom: 1px dashed #30363d;
            padding-bottom: 6px;
            margin-bottom: 10px;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.9rem;
        }}
        .rule-line {{
            margin-bottom: 10px;
            font-size: 0.95rem;
        }}
        .rule-header {{
            margin-bottom: 12px; 
            color:#ffb86c; 
            font-size: 1rem; 
            font-weight: bold;
        }}
        .dasa-highlight-text {{
            color: #ff79c6;
            font-size: 1.1rem;
            font-weight: bold;
            letter-spacing: 0.5px;
        }}
        .chain-box-container {{
            display: flex;
            flex-direction: row;
            gap: 20px;
        }}

        @media (max-width: 768px) {{
            body {{
                font-size: 12px;
                padding: 4px;
            }}
            .header-banner {{
                font-size: 0.8rem;
                padding: 8px;
            }}
            .dashboard-grid {{
                grid-template-columns: 1fr;
                gap: 10px;
            }}
            table {{
                font-size: 0.78rem;
            }}
            .rule-line {{
                font-size: 0.85rem;
            }}
            .rule-header {{
                font-size: 0.9rem;
            }}
            .dasa-highlight-text {{
                font-size: 0.95rem;
            }}
            .chain-box-container {{
                flex-direction: column;
                gap: 6px;
            }}
        }}
    </style>
</head>
<body>
    <div class="header-banner">
        <span style="color:#ff79c6; font-weight:bold;">TARGET:</span> {view_date.strftime('%Y-%m-%d %H:%M:%S')}<br class="mobile-break"> 
        <span style="color:#f1fa8c; font-weight:bold;">LOCATION:</span> {st.session_state.location_name.upper()}
    </div>
    {dashboard_grid_content}
</body>
</html>
"""

# ==========================================================
# 10. IFRAME COMPONENT RENDER CANVAS
# ==========================================================
encoded_html = urllib.parse.quote(complete_html_page)

st.iframe(
    f"data:text/html;charset=utf-8,{encoded_html}",
    height=950,
    width="stretch"
)

# ==========================================================
# SIDEBAR RENDERING FOR PLOTLY SPARKLINE GRAPHS
# ==========================================================
if trend_nodes:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📈 Trend Sparklines")
    for node in trend_nodes:
        # Final safety catch against sidebar graph rendering for Ascendant
        if node.get('label', '') in ["Asc", "Lagna"]:
            continue
        fig = create_compact_trend_chart(node["graph_type"], node["color"])
        
        st.sidebar.plotly_chart(
            fig, 
            width="stretch", 
            key=f"trend_graph_{node['label']}_{node['house']}_{node['dist']:.2f}"
        )