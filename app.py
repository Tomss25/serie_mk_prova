import streamlit as st

st.set_page_config(page_title="Institutional Quant Platform", layout="wide", page_icon="🏦")

# Stile CSS Navy Istituzionale
st.markdown("""
<style>
    :root {
        --navy-dark: #0A192F;
        --navy-light: #112240;
        --accent-blue: #64FFDA;
        --text-main: #E6F1FF;
    }
    .stApp { background-color: var(--navy-dark); color: var(--text-main); }
    section[data-testid="stSidebar"] { background-color: var(--navy-light); border-right: 1px solid #233554; }
    h1, h2, h3 { color: var(--text-main) !important; font-family: 'Helvetica Neue', sans-serif; font-weight: 700; letter-spacing: -0.5px;}
    div[data-testid="stMetric"], .kpi-card { background: var(--navy-light) !important; border: 1px solid #233554 !important; border-radius: 8px !important; }
    div.stButton > button { background-color: #1E3A8A; color: white; border-radius: 6px; font-weight: 600; border: 1px solid #3B82F6; }
    div.stButton > button:hover { background-color: #3B82F6; border-color: var(--accent-blue); }
    hr { border-color: #233554; }
</style>
""", unsafe_allow_html=True)

# Inizializza lo stato condiviso
if 'shared_df' not in st.session_state:
    st.session_state['shared_df'] = None

# Definizione navigazione
pages = {
    "Piattaforma Quantitativa": [
        st.Page("pages/1_Data_Engine.py", title="1. Serie Storiche & Analisi", icon="📊"),
        st.Page("pages/2_Portfolio_Optimizer.py", title="2. Ottimizzatore Strategico", icon="⚙️"),
        st.Page("pages/3_Methodology.py", title="3. Nota Metodologica", icon="📖")
    ]
}

pg = st.navigation(pages)
pg.run()