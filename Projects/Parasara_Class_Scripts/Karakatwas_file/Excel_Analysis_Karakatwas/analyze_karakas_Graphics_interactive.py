import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Setup Page Layout
st.set_page_config(layout="wide")

# Cache the data so the dashboard stays fast
@st.cache_data
def load_data():
    df = pd.read_csv('fixed_karakas_database.csv')
    # Domain Mapping Logic
    def get_domain(item):
        item = str(item).lower()
        mapping = {
            'Identity': ['body', 'health', 'vitality', 'head', 'face', 'self'],
            'Wealth': ['wealth', 'money', 'speech', 'family', 'savings', 'food'],
            'Skills': ['courage', 'writing', 'siblings', 'communication', 'effort', 'hobby'],
            'Home': ['property', 'vehicle', 'mother', 'comfort', 'education', 'house'],
            'Progeny': ['child', 'creativity', 'intellect', 'romance', 'wisdom', 'past life'],
            'Conflict': ['debt', 'enemy', 'illness', 'disease', 'competition', 'service'],
            'Partnership': ['marriage', 'spouse', 'partner', 'contract', 'wife', 'husband'],
            'Transformation': ['longevity', 'obstacle', 'research', 'inheritance', 'sudden'],
            'Dharma': ['guru', 'religion', 'father', 'travel', 'luck', 'dharma'],
            'Career': ['career', 'profession', 'job', 'honor', 'fame', 'boss', 'ambition']
        }
        for dom, keys in mapping.items():
            if any(k in item for k in keys): return dom
        return 'General'
    df['Domain'] = df['Item'].apply(get_domain)
    return df

df = load_data()

st.title("Vedic Parasara Research Lab")

# --- GLOBAL FILTERS ---
st.sidebar.header("Data Filter")
selected_karaka = st.sidebar.multiselect("Filter by Karaka", options=df['Karaka'].unique())
if selected_karaka:
    df = df[df['Karaka'].isin(selected_karaka)]

# --- ANALYTICAL METHODS ---
method = st.sidebar.selectbox("Select Research Method", [
    "01_Domain_Pie_Chart", "02_Affliction_Heatmap", "03_Influence_Sunburst",
    "04_Risk_Ranking_Bar", "05_Item_Variety_Treemap", "06_Domain_Distribution_Radar",
    "07_Density_Matrix", "08_Affliction_Violin_Plot", "09_Concept_Relationship_Sankey",
    "10_Planetary_Influence_Bubble"
])

if method == "01_Domain_Pie_Chart":
    fig = px.pie(df, names='Domain', title="Distribution of Life Domains")
    st.plotly_chart(fig, use_container_width=True)

elif method == "02_Affliction_Heatmap":
    pivot = pd.crosstab(df['Karaka'], df['Is_Afflicted'])
    fig = px.imshow(pivot, title="Affliction Intensity per Planet", color_continuous_scale='RdBu')
    st.plotly_chart(fig, use_container_width=True)

elif method == "03_Influence_Sunburst":
    fig = px.sunburst(df, path=['Karaka', 'Domain', 'Item'], title="Influence Hierarchy")
    st.plotly_chart(fig, use_container_width=True)

elif method == "04_Risk_Ranking_Bar":
    stats = df.groupby('Karaka')['Is_Afflicted'].mean().reset_index()
    fig = px.bar(stats, x='Karaka', y='Is_Afflicted', title="Affliction Probability per Planet")
    st.plotly_chart(fig, use_container_width=True)

elif method == "05_Item_Variety_Treemap":
    fig = px.treemap(df, path=['Karaka', 'Item'], title="Depth of Karaka Representation")
    st.plotly_chart(fig, use_container_width=True)

elif method == "06_Domain_Distribution_Radar":
    radar_data = pd.crosstab(df['Karaka'], df['Domain'])
    st.line_chart(radar_data)

elif method == "07_Density_Matrix":
    matrix = pd.crosstab(df['Karaka'], df['Domain'])
    fig = px.imshow(matrix, title="Domain-Planet Density Matrix", color_continuous_scale='Viridis')
    st.plotly_chart(fig, use_container_width=True)

elif method == "08_Affliction_Violin_Plot":
    fig = px.violin(df, x='Karaka', y='Is_Afflicted', title="Affliction Distribution")
    st.plotly_chart(fig, use_container_width=True)

elif method == "09_Concept_Relationship_Sankey":
    df_sankey = df.groupby(['Karaka', 'Domain']).size().reset_index(name='value')
    df_sankey.columns = ['source', 'target', 'value']
    fig = go.Figure(data=[go.Sankey(
        node = dict(pad = 15, thickness = 20, label = list(pd.concat([df_sankey['source'], df_sankey['target']]).unique())),
        link = dict(
            source = [list(pd.concat([df_sankey['source'], df_sankey['target']]).unique()).index(s) for s in df_sankey['source']],
            target = [list(pd.concat([df_sankey['source'], df_sankey['target']]).unique()).index(t) for t in df_sankey['target']],
            value = df_sankey['value']
        ))])
    st.plotly_chart(fig, use_container_width=True)

elif method == "10_Planetary_Influence_Bubble":
    bubble_data = df.groupby('Karaka').size().reset_index(name='count')
    fig = px.scatter(bubble_data, x='Karaka', y='count', size='count', title="Planetary Data Gravity")
    st.plotly_chart(fig, use_container_width=True)