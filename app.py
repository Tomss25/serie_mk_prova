import streamlit as st

st.set_page_config(page_title="Institutional Quant Platform", layout="wide", page_icon="🏦")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Roboto:wght@400;500&display=swap');
    
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; color: #202124; background-color: #F8F9FA; }
    .stApp { background-color: #F8F9FA; }
    
    /* MODIFICA: Sidebar Blu Leggero come richiesto */
    [data-testid="stSidebar"] { background-color: #E8F0FE !important; border-right: 1px solid #DADCE0; }
    
    h1, h2, h3, h4 { font-family: 'Google Sans', sans-serif !important; color: #202124 !important; font-weight: 400; letter-spacing: -0.2px; }
    [data-testid="stMetric"], .kpi-card { background-color: #FFFFFF !important; border: 1px solid #DADCE0 !important; border-radius: 8px !important; padding: 16px !important; box-shadow: none !important; }
    [data-testid="stMetricValue"] { color: #202124 !important; font-family: 'Google Sans', sans-serif; font-weight: 400; }
    [data-testid="stMetricLabel"] { color: #5F6368 !important; font-size: 0.85rem !important; font-weight: 500; }
    div.stButton > button, div.stDownloadButton > button { background-color: #FFFFFF !important; color: #1A73E8 !important; border: 1px solid #DADCE0 !important; border-radius: 18px !important; font-family: 'Google Sans', sans-serif; font-weight: 500 !important; padding: 4px 16px !important; transition: all 0.2s ease; }
    div.stButton > button:hover, div.stDownloadButton > button:hover { background-color: #F4F8FE !important; border-color: #1A73E8 !important; color: #174EA6 !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; border-bottom: 1px solid #DADCE0; background-color: transparent; }
    .stTabs [data-baseweb="tab"] { color: #5F6368 !important; padding-bottom: 12px; font-family: 'Google Sans', sans-serif; font-weight: 500; border: none !important; background-color: transparent !important; }
    .stTabs [aria-selected="true"] { color: #1A73E8 !important; border-bottom: 3px solid #1A73E8 !important; }
    [data-testid="stDataFrame"], .stTable { border: 1px solid #DADCE0 !important; border-radius: 8px !important; background-color: #FFFFFF !important; }
    thead tr th { background-color: #F8F9FA !important; color: #5F6368 !important; border-bottom: 1px solid #DADCE0 !important; }
    tbody tr td { color: #202124 !important; border-bottom: 1px solid #F1F3F4 !important; }
</style>
""", unsafe_allow_html=True)

if 'shared_df' not in st.session_state:
    st.session_state['shared_df'] = None

# MODIFICA: Rinominato brutalmente le pagine secondo le tue specifiche
pages = {
    "Piattaforma Quantitativa": [
        st.Page("pages/1_Data_Engine.py", title="1. Serie storiche", icon="📊"),
        st.Page("pages/2_Strategic_Optimizer.py", title="2. ottimizzazione mark", icon="⚖️"),
        st.Page("pages/3_Tier_Optimizer.py", title="3. three lines opt", icon="🎯"),
        st.Page("pages/4_Methodology.py", title="4. Metodologia", icon="📖")
    ]
}

pg = st.navigation(pages)
pg.run()
