import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
from core_engine import fetch_yahoo, fetch_morningstar, align_and_clean_data

st.header("📊 Asset Historical Data Engine")

with st.sidebar:
    raw_input = st.text_area("Tickers / ISIN (uno per riga)", value="SP500\nSWDA.MI\nGOLD", height=100)
    years = st.slider("Anni di profondità", 1, 20, 5)
    run_fetch = st.button("🚀 Estrai Dati")

ALIAS_MAP = {"SP500": "^GSPC", "NASDAQ": "^NDX", "GOLD": "GC=F", "BITCOIN": "BTC-USD"}

if run_fetch:
    tickers = [ALIAS_MAP.get(t.upper(), t.upper()) for t in re.findall(r"[\w\.\-\^\=]+", raw_input)]
    start_dt = datetime.now() - timedelta(days=years*365)
    
    all_series = {}
    with st.spinner("Connessione feed dati in corso..."):
        for t in tickers:
            s = fetch_yahoo(t, start_dt) or fetch_morningstar(t, start_dt, datetime.now())
            if s is not None:
                s.name = t
                all_series[t] = s
            else:
                st.error(f"❌ Fallimento feed per: {t}")
    
    if all_series:
        df_clean = align_and_clean_data(all_series)
        st.session_state['shared_df'] = df_clean 
        st.success(f"✅ Dati in memoria. {len(df_clean)} giorni operativi.")
        st.line_chart((df_clean / df_clean.iloc[0]) * 100)