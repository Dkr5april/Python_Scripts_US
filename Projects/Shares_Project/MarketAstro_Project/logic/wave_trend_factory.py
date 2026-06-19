"""
wave_trend_factory.py
Decoupled module for evaluating and generating X & Y structural wave trends, 
enforcing strict planet counting, fallbacks, and ascendant purges.
"""

def generate_wave_trends(data, analyze_market_trends_func, X, Y, x_chain_raw, y_chain_raw):
    """
    Evaluates raw analyzer results and guarantees the presence of structural trajectories
    for both X and Y paths according to custom fallback definitions.
    """
    # 1. Safely filter or isolate input data if needed by your underlying analyzer
    wave_safe_data = {k: v for k, v in data.items() if k not in ["Asc", "Lagna"]}
    
    # 2. Get initial trends from your core math module
    trend_nodes = analyze_market_trends_func(wave_safe_data)
    if not isinstance(trend_nodes, list):
        trend_nodes = []

    # 3. Clean and normalize existing nodes (remove any accidental blanks or Asc references)
    cleaned_nodes = []
    for node in trend_nodes:
        lbl = str(node.get('label', '')).strip()
        if lbl in ["", "Asc", "Lagna"]:
            continue
        cleaned_nodes.append(node)

    # 4. Check presence of X and Y trends using clean string matching
    x_trend_exists = any(X in str(n.get('label', '')) for n in cleaned_nodes)
    y_trend_exists = any(Y in str(n.get('label', '')) for n in cleaned_nodes)

    # 5. GUARANTEED X FALLBACK TRAJECTORY (Mo -> X if no sub-agents exist)
    if not x_trend_exists and not x_chain_raw and X in data and X != "N/A":
        x_house = data[X].get('house', '-')
        x_status = data[X].get('status', 'DIR')
        x_dist = abs(data["Mo"]["lon"] - data[X]["lon"]) % 360
        
        trend_direction = "BULLISH" if x_status == "DIR" else "BEARISH"
        trend_color = "#50fa7b" if trend_direction == "BULLISH" else "#ff5555"
        
        cleaned_nodes.insert(0, {
            'label': f"Mo -> {X}",
            'trend': trend_direction,
            'color': trend_color,
            'p_text': f"Direct Root Trajectory ({X})",
            'house': x_house,
            'h_text': "Direct Structural Connection",
            'dist': x_dist,
            'graph_type': 'line'
        })

    # 6. GUARANTEED Y FALLBACK TRAJECTORY (Mo -> Y if no sub-agents exist)
    if not y_trend_exists and not y_chain_raw and Y in data and Y != "N/A":
        y_house = data[Y].get('house', '-')
        y_status = data[Y].get('status', 'DIR')
        y_dist = abs(data["Mo"]["lon"] - data[Y]["lon"]) % 360
        
        trend_direction = "BULLISH" if y_status == "DIR" else "BEARISH"
        trend_color = "#50fa7b" if trend_direction == "BULLISH" else "#ff5555"
        
        cleaned_nodes.append({
            'label': f"Mo -> {Y}",
            'trend': trend_direction,
            'color': trend_color,
            'p_text': f"Direct Root Trajectory ({Y})",
            'house': y_house,
            'h_text': "Direct Structural Connection",
            'dist': y_dist,
            'graph_type': 'line'
        })

    return cleaned_nodes


def build_trend_html_blocks(trend_nodes):
    """
    Transforms uniform trend dictionaries into styled dashboard HTML cards.
    """
    html_output = ""
    if not trend_nodes:
        return "<div style='color:#6272a4;'>No Active Waves Found</div>"
        
    for node in trend_nodes:
        html_output += f"""
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
    return html_output