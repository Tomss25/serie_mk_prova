import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
from core_engine import fetch_yahoo, fetch_morningstar, align_and_clean_data

st.header("📊 Asset Historical Data Engine")
st.markdown("Estrazione, allineamento e pulizia dati multi-sorgente. I dati estratti qui alimenteranno gli ottimizzatori.")

with st.sidebar:
    st.subheader("Configurazione Estrazione")
    raw_input = st.text_area("Tickers / ISIN (uno per riga)", value="SP500\nSWDA.MI\nGOLD", height=100)
    years = st.slider("Anni di profondità", 1, 20, 5)
    
    # REINTRODOTTA LA FREQUENZA (con mapping corretto per Pandas)
    freq_options = {"Giornaliero": "B", "Settimanale": "W-FRI", "Mensile": "ME", "Annuale": "YE"}
    selected_freq_label = st.selectbox("Frequenza Dati", list(freq_options.keys()))
    selected_freq_code = freq_options[selected_freq_label]
    
    run_fetch = st.button("🚀 Estrai Dati")

ALIAS_MAP = {"SP500": "^GSPC", "NASDAQ": "^NDX", "GOLD": "GC=F", "BITCOIN": "BTC-USD"}

if run_fetch:
    tickers = [ALIAS_MAP.get(t.upper(), t.upper()) for t in re.findall(r"[\w\.\-\^\=]+", raw_input)]
    start_dt = datetime.now() - timedelta(days=years*365)
    
    all_series = {}
    with st.spinner("Connessione feed dati in corso..."):
        for t in tickers:
            # FIX DEL CRASH: Controllo esplicito su None e su DataFrame vuoti, niente "or"
            s = fetch_yahoo(t, start_dt)
            if s is None or s.empty:
                s = fetch_morningstar(t, start_dt, datetime.now())
            
            if s is not None and not s.empty:
                s.name = t
                all_series[t] = s
            else:
                st.error(f"❌ Fallimento feed per: {t}. Controllare ticker/ISIN o riprovare.")
    
    if all_series:
        df_clean = align_and_clean_data(all_series)
        
        # APPLICAZIONE DELLA FREQUENZA
        if selected_freq_code != "B":
            df_clean = df_clean.resample(selected_freq_code).last().dropna(how='all')
            
        st.session_state['shared_df'] = df_clean 
        st.success(f"✅ Dati in memoria ({selected_freq_label}). {len(df_clean)} periodi operativi estratti.")
        
        st.line_chart((df_clean / df_clean.iloc[0]) * 100)
        
        c1, c2 = st.columns(2)
        with c1: 
            st.download_button(
                "📥 Scarica CSV", 
                df_clean.to_csv(sep=";", decimal=",").encode('utf-8'), 
                f"dati_storici_{selected_freq_label}.csv", 
                "text/csv"
            )
        with c2: 
            st.info("👉 Naviga nel menu laterale per usare l'Ottimizzatore sui dati appena estratti.")
