import dash
from dash import dcc, html, dash_table, Input, Output, State
import plotly.graph_objects as go
import swisseph as swe
from datetime import datetime

# --- 1. ENGINE (Sidereal Lahiri) ---
def get_astrology_data(date_str, time_str):
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")
        jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        
        # All 9 Planets
        planets_map = {
            "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, 
            "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, 
            "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE
        }
        
        signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
                 "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        
        res = []
        for name, pid in planets_map.items():
            pos, _ = swe.calc_ut(jd, pid, flag)
            l = pos[0]
            res.append({
                "planet": name, 
                "abs_lon": l, 
                "sign": signs[int(l/30)], 
                "deg": f"{round(l%30,1)}°"
            })
            if name == "Rahu":
                klon = (l + 180) % 360
                res.append({
                    "planet": "Ketu", 
                    "abs_lon": klon, 
                    "sign": signs[int(klon/30)], 
                    "deg": f"{round(klon%30,1)}°"
                })
        return res
    except Exception as e:
        print(f"Data Error: {e}")
        return []

# --- 2. LAYOUT ---
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H2("PROFESSIONAL NAADI-WESTERN DASHBOARD", style={'textAlign': 'center', 'fontFamily': 'Arial'}),
    
    # Inputs Section
    html.Div([
        html.Div([
            html.B("Natal (DD/MM/YYYY): "),
            dcc.Input(id='n-date', value='15/05/1990', style={'width':'100px'}),
            dcc.Input(id='n-time', value='10:30', style={'width':'60px'})
        ], style={'display':'inline-block', 'padding':'10px'}),
        
        html.Div([
            html.B("Transit (DD/MM/YYYY): "),
            dcc.Input(id='t-date', value='23/01/2026', style={'width':'100px'}),
            dcc.Input(id='t-time', value='20:30', style={'width':'60px'})
        ], style={'display':'inline-block', 'padding':'10px'}),
        
        html.Button('UPDATE DASHBOARD', id='btn', n_clicks=0, 
                    style={'backgroundColor': '#1f3b63', 'color': 'white', 'fontWeight': 'bold', 'padding': '5px 15px'})
    ], style={'textAlign':'center', 'background':'#f8f9fa', 'borderBottom': '2px solid #ddd'}),

    # Main Visual Row
    html.Div([
        # Left: Natal Table
        html.Div([
            html.H4("Natal Positions", style={'textAlign': 'center', 'margin': '5px'}),
            dash_table.DataTable(
                id='n-table', 
                columns=[{"name": i.capitalize(), "id": i} for i in ["planet", "sign", "deg"]],
                style_cell={'fontSize':'11px', 'textAlign': 'center'},
                style_header={'backgroundColor': '#1f3b63', 'color': 'white'}
            )
        ], style={'width': '20%', 'padding': '10px'}),

        # Center: Polar Chart
        html.Div([
            dcc.Graph(id='chart', style={'height': '700px'})
        ], style={'width': '60%'}),

        # Right: Aspects Table
        html.Div([
            html.H4("Western Aspects", style={'textAlign': 'center', 'margin': '5px'}),
            dash_table.DataTable(
                id='a-table', 
                columns=[{"name": i, "id": i} for i in ["Natal", "Transit", "Nature"]],
                style_cell={'fontSize':'11px', 'textAlign': 'center'},
                style_header={'backgroundColor': '#c83349', 'color': 'white'},
                style_data_conditional=[
                    {'if': {'filter_query': '{Nature} eq "Support"'}, 'color': 'green', 'fontWeight': 'bold'},
                    {'if': {'filter_query': '{Nature} eq "Stress"'}, 'color': 'red', 'fontWeight': 'bold'}
                ]
            )
        ], style={'width': '20%', 'padding': '10px'})
    ], style={'display': 'flex', 'alignItems': 'flex-start', 'justifyContent': 'center'})
])

# --- 3. CALLBACK ---
@app.callback(
    [Output('chart', 'figure'), Output('n-table', 'data'), Output('a-table', 'data')],
    [Input('btn', 'n_clicks')],
    [State('n-date', 'value'), State('n-time', 'value'), State('t-date', 'value'), State('t-time', 'value')]
)
def update_dashboard(n_clicks, n_date, n_time, t_date, t_time):
    natal = get_astrology_data(n_date, n_time)
    trans = get_astrology_data(t_date, t_time)
    
    if not natal or not trans:
        return go.Figure(), [], []

    aspects = []
    for n_p in natal:
        for t_p in trans:
            diff = abs(n_p['abs_lon'] - t_p['abs_lon'])
            if diff > 180: diff = 360 - diff
            if 88 <= diff <= 92: 
                aspects.append({"Natal": n_p['planet'], "Transit": t_p['planet'], "Nature": "Stress", "color": "red"})
            elif 118 <= diff <= 122: 
                aspects.append({"Natal": n_p['planet'], "Transit": t_p['planet'], "Nature": "Support", "color": "green"})

    fig = go.Figure()
    
    # 1. Natal Planets (Inner) - Staggered radii to avoid overlapping text
    fig.add_trace(go.Scatterpolar(
        r=[(0.75 if i % 2 == 0 else 0.85) for i in range(len(natal))],
        theta=[p['abs_lon'] for p in natal], 
        text=[p['planet'] for p in natal], 
        mode="markers+text", 
        name="Natal",
        marker=dict(size=12, color="#1f3b63", line=dict(color="white", width=2)),
        textposition="top center"
    ))
    
    # 2. Transit Planets (Outer)
    fig.add_trace(go.Scatterpolar(
        r=[(1.15 if i % 2 == 0 else 1.25) for i in range(len(trans))],
        theta=[p['abs_lon'] for p in trans], 
        text=[p['planet'] for p in trans], 
        mode="markers+text", 
        name="Transit",
        marker=dict(size=12, color="#c83349", line=dict(color="black", width=1)),
        textposition="top center"
    ))

    # 3. Aspect Lines
    for asp in aspects:
        n_p = next(p for p in natal if p['planet'] == asp['Natal'])
        t_p = next(p for p in trans if p['planet'] == asp['Transit'])
        fig.add_trace(go.Scatterpolar(
            r=[0.85, 1.15],
            theta=[n_p['abs_lon'], t_p['abs_lon']],
            mode="lines",
            line=dict(color=asp['color'], width=2, dash='dot'),
            showlegend=False,
            hoverinfo='skip'
        ))

    # --- THE CRITICAL VISUAL FIX ---
    fig.update_layout(
        polar=dict(
            angularaxis=dict(
                rotation=90,           # Forces Aries (0°) to the TOP
                direction="clockwise", # Standard Astrology direction
                tickmode="array",
                tickvals=[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330],
                ticktext=["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"],
                gridcolor="#e5e5e5"
            ),
            radialaxis=dict(visible=False, range=[0, 1.4])
        ),
        margin=dict(l=50, r=50, t=50, b=50),
        paper_bgcolor="white",
        plot_bgcolor="white"
    )

    return fig, natal, aspects

if __name__ == "__main__":
    app.run(debug=True)