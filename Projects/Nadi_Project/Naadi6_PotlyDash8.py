import dash
from dash import dcc, html, dash_table, Input, Output, State
import plotly.graph_objects as go
import swisseph as swe
from datetime import datetime
from geopy.geocoders import Nominatim

# --- 1. ENGINE ---
geolocator = Nominatim(user_agent="naadi_transit_pro")

def get_coords(city_name):
    try:
        location = geolocator.geocode(city_name)
        return (location.latitude, location.longitude) if location else (None, None)
    except: return None, None

def get_astrology_data(date_str, time_str, lat, lon):
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")
        jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        
        planets_map = {"Sun":0, "Moon":1, "Mars":4, "Mercury":2, "Jupiter":5, "Venus":3, "Saturn":6, "Rahu":swe.MEAN_NODE}
        signs = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
        benefics = ["Jupiter", "Venus", "Mercury", "Moon"]
        
        res = []
        for name, pid in planets_map.items():
            pos, _ = swe.calc_ut(jd, pid, flag)
            l = pos[0]
            nature = "Good" if name in benefics else "Bad"
            res.append({"planet": name, "abs_lon": l, "sign": signs[int(l/30)], "deg": round(l % 30, 1), "nature": nature})
            if name == "Rahu":
                klon = (l + 180) % 360
                res.append({"planet": "Ketu", "abs_lon": klon, "sign": signs[int(klon/30)], "deg": round(klon % 30, 1), "nature": "Bad"})
        return res
    except: return []

# --- 2. LAYOUT ---
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H2("TRANSIT-NATAL NAADI ANALYSIS", style={'textAlign': 'center', 'color': '#1a2a6c'}),
    
    html.Div([
        html.Div([
            html.B("Natal City: "), dcc.Input(id='n-city', value="Machilipatnam", style={'width':'120px'}),
            dcc.Input(id='n-date', value='15/05/1990', style={'width':'85px'}),
            dcc.Input(id='n-time', value='10:30', style={'width':'55px'})
        ], style={'display':'inline-block', 'padding':'10px'}),

        html.Div([
            html.B("Transit City: "), dcc.Input(id='t-city', value="Sidney, Nebraska", style={'width':'120px'}),
            dcc.Input(id='t-date', value='24/01/2026', style={'width':'85px'}),
            dcc.Input(id='t-time', value='07:30', style={'width':'55px'})
        ], style={'display':'inline-block', 'padding':'10px'}),

        html.Div([
            dcc.Checklist(id='deg-toggle', options=[{'label': ' Degrees', 'value': 'ON'}], value=['ON'], style={'display':'inline-block'}),
            dcc.RadioItems(id='aspect-mode', 
                           options=[{'label': ' Vedic Transit Drishti', 'value': 'VEDIC'}, {'label': ' Western Orb', 'value': 'WESTERN'}], 
                           value='VEDIC', style={'display':'inline-block', 'marginLeft':'20px', 'fontWeight':'bold'})
        ], style={'display':'inline-block', 'backgroundColor':'#f0f4f8', 'padding':'5px 15px', 'borderRadius':'10px'}),
        
        html.Button('REFRESH', id='btn', n_clicks=0, style={'marginLeft':'20px', 'backgroundColor':'#1a2a6c', 'color':'white'})
    ], style={'textAlign':'center', 'background':'#f8f9fa', 'padding':'15px'}),

    html.Div([
        html.Div([html.H4("Birth Planets"), dash_table.DataTable(id='n-table', style_cell={'fontSize':'11px'})], style={'width':'20%','padding':'10px'}),
        html.Div([dcc.Graph(id='chart', style={'height':'750px'})], style={'width':'60%'}),
        html.Div([html.H4(id='side-title'), dash_table.DataTable(id='side-table', style_cell={'fontSize':'11px'})], style={'width':'20%','padding':'10px'})
    ], style={'display':'flex'})
])

# --- 3. CALLBACK ---
@app.callback(
    [Output('chart', 'figure'), Output('n-table', 'data'), Output('side-table', 'data'), 
     Output('side-table', 'columns'), Output('side-title', 'children')],
    [Input('btn', 'n_clicks'), Input('deg-toggle', 'value'), Input('aspect-mode', 'value')],
    [State('n-city', 'value'), State('n-date', 'value'), State('n-time', 'value'),
     State('t-city', 'value'), State('t-date', 'value'), State('t-time', 'value')]
)
def update_dashboard(n_clicks, deg_toggle, mode, n_city, n_d, n_t, t_city, t_d, t_t):
    n_lat, n_lon = get_coords(n_city)
    t_lat, t_lon = get_coords(t_city)
    if n_lat is None: n_lat, n_lon = 16.1176, 80.9314
    if t_lat is None: t_lat, t_lon = 41.14, -102.97

    natal = get_astrology_data(n_d, n_t, n_lat, n_lon)
    trans = get_astrology_data(t_d, t_t, t_lat, t_lon)
    
    fig = go.Figure()
    show_deg = 'ON' in deg_toggle
    table_data, table_cols, title = [], [], ""

    if mode == 'VEDIC':
        title = "Vedic Transit Influence"
        table_cols = [{"name": i, "id": i} for i in ["Transit_Planet", "Hits_Natal_Sign", "Nature"]]
        signs = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
        
        for tp in trans:
            tp_idx = int(tp['abs_lon']/30)
            # Drishti rules
            asp_idxs = [(tp_idx + 6) % 12] # 7th aspect
            if tp['planet'] == "Mars": asp_idxs += [(tp_idx + 3) % 12, (tp_idx + 7) % 12]
            elif tp['planet'] == "Jupiter": asp_idxs += [(tp_idx + 4) % 12, (tp_idx + 8) % 12]
            elif tp['planet'] == "Saturn": asp_idxs += [(tp_idx + 2) % 12, (tp_idx + 9) % 12]
            elif tp['planet'] in ["Rahu", "Ketu"]: asp_idxs += [(tp_idx + 4) % 12, (tp_idx + 8) % 12]
            
            color = "green" if tp['nature'] == "Good" else "red"
            
            for idx in asp_idxs:
                target_sign = signs[idx]
                # Check if a natal planet is in that sign
                impacted = [np['planet'] for np in natal if np['sign'] == target_sign]
                if impacted:
                    hit_label = f"{target_sign} ({', '.join(impacted)})"
                    table_data.append({"Transit_Planet": tp['planet'], "Hits_Natal_Sign": hit_label, "Nature": tp['nature']})
                    # Draw Line from Outer Transit Planet to Inner Natal Planet
                    for np in natal:
                        if np['sign'] == target_sign:
                            fig.add_trace(go.Scatterpolar(r=[1.2, 0.8], theta=[tp['abs_lon'], np['abs_lon']], 
                                         mode="lines", line=dict(color=color, width=2, dash='solid'), opacity=0.4, showlegend=False))

    else: # WESTERN remains degree-to-degree
        title = "Western Degree Aspects"
        table_cols = [{"name": i, "id": i} for i in ["Natal", "Transit", "Impact"]]
        for n_p in natal:
            for t_p in trans:
                diff = abs(n_p['abs_lon'] - t_p['abs_lon'])
                if diff > 180: diff = 360 - diff
                if 88 <= diff <= 92:
                    table_data.append({"Natal": n_p['planet'], "Transit": n_p['planet'], "Impact": "Stressful"})
                    fig.add_trace(go.Scatterpolar(r=[0.8, 1.2], theta=[n_p['abs_lon'], t_p['abs_lon']], mode="lines", line=dict(color="red", width=2), showlegend=False))
                elif 118 <= diff <= 122:
                    table_data.append({"Natal": n_p['planet'], "Transit": t_p['planet'], "Impact": "Harmonious"})
                    fig.add_trace(go.Scatterpolar(r=[0.8, 1.2], theta=[n_p['abs_lon'], t_p['abs_lon']], mode="lines", line=dict(color="green", width=2), showlegend=False))

    # Planets
    for data, r_val, name, color in [(natal, 0.8, "Birth", "#1a2a6c"), (trans, 1.2, "Transit", "#b21f1f")]:
        labels = [f"{p['planet']}<br>{p['deg']}°" if show_deg else p['planet'] for p in data]
        fig.add_trace(go.Scatterpolar(r=[r_val]*len(data), theta=[p['abs_lon'] for p in data], 
                                     text=labels, mode="markers+text", name=name, marker=dict(color=color, size=12)))

    fig.update_layout(polar=dict(angularaxis=dict(rotation=90, direction="clockwise",
                      tickvals=[i*30 for i in range(12)], ticktext=["Ari","Tau","Gem","Can","Leo","Vir","Lib","Sco","Sag","Cap","Aqu","Pis"])),
                      margin=dict(l=40, r=40, t=40, b=40))
    
    return fig, natal, table_data, table_cols, title

if __name__ == "__main__":
    app.run(debug=True)