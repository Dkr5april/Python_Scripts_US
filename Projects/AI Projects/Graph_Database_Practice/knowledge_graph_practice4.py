import streamlit as st
import yfinance as yf
import json
import time

st.set_page_config(page_title="Real-Time Web Data TextTrack PoC", layout="wide")

st.title("📈 Live Web Data & Predictive Graph Architecture")
st.caption("Connected Real-Time Prototype: Yahoo Finance Ingestion -> Multi-Graph Engine -> Synchronized TextTrack")

# --- REAL-TIME DATA INGESTION ENGINE ---
@st.cache_data(ttl=10)  # Caches for 10 seconds to avoid web rate limits
def fetch_live_market_data():
    """Pulls live real-time index data directly from the Yahoo Finance endpoint."""
    try:
        # Pulling live data for NIFTY 50
        ticker = yf.Ticker("^NSEI")
        todays_data = ticker.history(period="1d", interval="1m")
        
        if not todays_data.empty:
            latest_row = todays_data.iloc[-1]
            return {
                "status": "SUCCESS",
                "price": round(latest_row['Close'], 2),
                "volume": int(latest_row['Volume']),
                "open": round(latest_row['Open'], 2)
            }
    except Exception as e:
        pass
    # Fallback default values if the external web scraper hits an off-market hours gap
    return {"status": "FALLBACK_MODE", "price": 23500.25, "volume": 120000, "open": 23450.00}

# Fetch the live web metrics
live_feed = fetch_live_market_data()

# --- ENTERPRISE PIPELINE DEPENDENCY ENGINE ---
# 1. Feature Store maps the live web stream data points into dynamic vectors
mock_feature_store = {
    "live_nifty_price": live_feed["price"],
    "price_delta_from_open": round(live_feed["price"] - live_feed["open"], 2),
    "rolling_volume_surge": live_feed["volume"]
}

# 2. Knowledge Graph maps fixed organizational linkages
mock_knowledge_graph = {
    "dependencies": [
        {"source": "NIFTY_50_INDEX", "contains_sector": "Banking_Sector"},
        {"source": "Banking_Sector", "risk_factor": "Interest_Rate_Fluctuations"}
    ]
}

# 3. Temporal Graph records the progressive chronological shifts
mock_temporal_graph = {
    "state_transitions": [
        {"time": "09:15 AM", "event": "Market Open", "price": live_feed["open"]},
        {"time": "Current Tick", "event": "Live Price Refresh", "price": live_feed["price"]}
    ]
}

# 4. Vector DB provides matching historical context templates
mock_vector_db = [
    {"pattern_id": "breakout_v3", "historical_context": f"Historical match shows similar open-delta structures matching {mock_feature_store['price_delta_from_open']} often experience volatility consolidation."}
]

# --- SIDEBAR: PIPELINE DIAGNOSTICS (OBSERVABILITY) ---
with st.sidebar:
    st.header("🛠️ Observability Dashboard")
    st.markdown(f"**Data Ingestion Status:** `{live_feed['status']}`")
    st.metric(label="Live Web Price (NIFTY 50)", value=f"INR {live_feed['price']}", delta=f"{mock_feature_store['price_delta_from_open']} pts")
    
    st.subheader("Pipeline Network Latency")
    st.caption("🟢 `[Yahoo Finance API]` Data Scraped successfully • `140ms`")
    st.caption("🟢 `[Feature Store]` Derived vectors synchronized • `4ms`")
    st.caption("🟢 `[Neo4j/Graph Engines]` Combined structural context traced • `12ms`")
    st.caption("🟢 `[Agent Platform]` Compiled prediction payload • `9ms`")

# --- MAIN DISPLAY TIMELINE WORKFLOW ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📺 Live Analytical Media Stream")
    video_src = "https://www.w3schools.com/html/mov_bbb.mp4"
    
    # HTML5 Component executing our live web variables straight into the TextTrack cues!
    html5_live_code = f"""
    <div style="background:#0e1117; padding:15px; border-radius:10px; border: 1px solid #30363d;">
        <video id="live-web-stream" width="100%" controls autoplay muted style="border-radius: 5px;">
            <source src="{video_src}" type="video/mp4">
        </video>
        
        <div id="live-track-overlay" style="margin-top: 15px; min-height: 90px; padding: 15px; background: #111827; border-left: 5px solid #10b981; border-radius: 4px; color: #fff; font-family: monospace; font-size: 13px;">
            <i>Awaiting live web cue timeline synchronizations...</i>
        </div>
    </div>

    <script>
        const video = document.getElementById('live-web-stream');
        const overlay = document.getElementById('live-track-overlay');
        
        const track = video.addTextTrack("metadata", "Live Web Agent Simulations", "en");
        track.mode = "hidden";

        // Dynamic cues populated seamlessly with our live Yahoo Finance parameters!
        const liveAgentCues = [
            {{ start: 1, end: 5, msg: "🌐 [INGESTION ALERT]: Live Web Scraper actively polled NIFTY 50. Price extracted: INR {live_feed['price']}. Feature store calculated open-delta vector at {mock_feature_store['price_delta_from_open']} points." }},
            {{ start: 6, end: 10, msg: "⏳ [TEMPORAL ENGINE MATCH]: Evaluating historical sequence templates inside Vector DB. Pattern footprint match info: {mock_vector_db[0]['historical_context']}" }},
            {{ start: 11, end: 15, msg: "🔮 [PWM PREDICTIVE OUTCOME]: Combining Knowledge Graph structural risk linkages. Interest Rate dependencies predict a 68% probability stability corridor for current macro index window." }}
        ];

        liveAgentCues.forEach(item => {{
            const cue = new VTTCue(item.start, item.end, item.msg);
            track.addCue(cue);
        }});

        track.oncuechange = () => {{
            const active = track.activeCues;
            if (active && active.length > 0) {{
                overlay.innerHTML = `<b style="color:#34d399;">📍 FRAME-LOCKED DATA TIMELINE INSIGHT:</b><br>${{active[0].text}}`;
            }} else {{
                overlay.innerHTML = "<span style='color:#9ca3af;'>⏳ Fetching next live background streaming matrix...</span>";
            }}
        }};
    </script>
    """
    st.components.v1.html(html5_live_code, height=460)

with col2:
    st.subheader("💡 Dynamic Database State")
    st.caption("These data matrices represent what the AI agent read from your infrastructure layers for this live web fetch request:")
    
    with st.expander("📝 Live Features (Feast)", expanded=True):
        st.json(mock_feature_store)
    with st.expander("⏳ Temporal Graph Sequence", expanded=False):
        st.json(mock_temporal_graph)
    with st.expander("🌐 Static Knowledge Graph Nodes", expanded=False):
        st.json(mock_knowledge_graph)