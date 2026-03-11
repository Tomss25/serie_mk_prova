import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta
import plotly.express as px
from core_engine import fetch_yahoo, fetch_morningstar, align_and_clean_data

st.header("📊 Asset Historical Data Engine")
st.markdown("Estrazione, allineamento e pulizia dati multi-sorgente.")

ALIAS_MAP = {"SP500": "^GSPC", "NASDAQ": "^NDX", "GOLD": "GC=F", "BITCOIN": "BTC-USD"}

with st.sidebar:
    st.subheader("Configurazione Estrazione")
    raw_input = st.text_area("Tickers / ISIN (uno per riga)", value="SP500\nSWDA.MI\nGOLD", height=100)
    years = st.slider("Anni di profondità", 1, 20, 5)
    run_fetch = st.button("🚀 Estrai Dati")

if run_fetch:
    tickers = [ALIAS_MAP.get(t.upper(), t.upper()) for t in re.findall(r"[\w\.\-\^\=]+", raw_input)]
    start_dt = datetime.now() - timedelta(days=years*365)
    end_dt = datetime.now()
    
    all_series = {}
    with st.spinner("Connessione ai feed dati in corso..."):
        for t in tickers:
            s = fetch_yahoo(t, start_dt)
            if s is None:
                s = fetch_morningstar(t, start_dt, end_dt)
            if s is not None:
                s.name = t
                all_series[t] = s
            else:
                st.error(f"❌ Fallimento feed per: {t}. Controllare ticker/ISIN.")
    
    if all_series:
        df_clean = align_and_clean_data(all_series)
        st.session_state['shared_df'] = df_clean # SALVATAGGIO IN SESSIONE
        st.success(f"✅ Dati allineati con successo. {len(df_clean)} giorni operativi netti trovati.")
        
        st.line_chart((df_clean / df_clean.iloc[0]) * 100)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("📥 Scarica CSV", df_clean.to_csv(sep=";", decimal=",").encode('utf-8'), "dati_storici.csv", "text/csv")
        with col2:
            st.info("👉 Vai alla pagina 'Ottimizzatore' per usare questi dati direttamente.")