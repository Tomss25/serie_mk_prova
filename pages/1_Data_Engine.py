import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
from core_engine import fetch_yahoo, fetch_morningstar, align_and_clean_data

st.header("📊 1. Serie storiche")
st.markdown("Aggregatore dati. Carica una lista locale, estrai da API, o combina entrambi. I dati verranno allineati per l'ottimizzazione.")

with st.sidebar:
    st.markdown("### 📥 Dati Custom (CSV)")
    uploaded_file = st.file_uploader("Carica le tue serie (Indice=Data)", type=["csv"])
    
    st.markdown("### 🌐 Estrazione API")
    raw_input = st.text_area("Tickers / ISIN (uno per riga)", value="SP500\nSWDA.MI", height=80)
    years = st.slider("Anni di profondità", 1, 20, 5)
    
    st.markdown("### ⚙️ Output")
    freq_options = {"Giornaliero": "B", "Settimanale": "W-FRI", "Mensile": "ME", "Annuale": "YE"}
    selected_freq_label = st.selectbox("Frequenza Dati", list(freq_options.keys()))
    selected_freq_code = freq_options[selected_freq_label]
    
    run_fetch = st.button("🚀 Processa e Allinea Dati")

ALIAS_MAP = {"SP500": "^GSPC", "NASDAQ": "^NDX", "GOLD": "GC=F", "BITCOIN": "BTC-USD"}

if run_fetch:
    all_series = {}
    error_flag = False
    
    with st.spinner("Acquisizione e fusione dati in corso..."):
        
        # 1. GESTIONE FILE LOCALE CARICATO
        if uploaded_file is not None:
            try:
                # Legge il CSV, suppone che la prima colonna sia la data
                custom_df = pd.read_csv(uploaded_file, sep=None, engine='python', index_col=0, parse_dates=True, dayfirst=True)
                # Forza i dati a numerici, ignorando eventuali stringhe spurie
                for col in custom_df.columns:
                    custom_df[col] = pd.to_numeric(custom_df[col].astype(str).str.replace(',', '.'), errors='coerce')
                
                # Aggiunge le colonne del file locale al dizionario delle serie
                for col in custom_df.columns:
                    series = custom_df[col].dropna()
                    if not series.empty:
                        all_series[col] = series
                st.toast(f"Caricate {len(custom_df.columns)} serie dal file locale.")
            except Exception as e:
                st.error(f"Errore nella lettura del file CSV: {e}")
                error_flag = True

        # 2. GESTIONE ESTRAZIONE API
        tickers = [ALIAS_MAP.get(t.upper(), t.upper()) for t in re.findall(r"[\w\.\-\^\=]+", raw_input)]
        if tickers:
            start_dt = datetime.now() - timedelta(days=years*365)
            for t in tickers:
                s = fetch_yahoo(t, start_dt)
                if s is None or s.empty:
                    s = fetch_morningstar(t, start_dt, datetime.now())
                
                if s is not None and not s.empty:
                    s.name = t
                    all_series[t] = s
                else:
                    st.error(f"❌ Fallimento feed API per: {t}")
                    error_flag = True

    # 3. ALLINEAMENTO E SALVATAGGIO IN SESSIONE
    if all_series:
        df_clean = align_and_clean_data(all_series)
        
        if selected_freq_code != "B":
            df_clean = df_clean.resample(selected_freq_code).last().dropna(how='all')
            
        st.session_state['shared_df'] = df_clean 
        st.success(f"✅ Dati fusi e allineati in memoria ({selected_freq_label}). {len(df_clean)} periodi estratti.")
        
        st.line_chart((df_clean / df_clean.iloc[0]) * 100)
        
        c1, c2 = st.columns(2)
        with c1: 
            st.download_button(
                "📥 Scarica CSV Allineato", 
                df_clean.to_csv(sep=";", decimal=",").encode('utf-8'), 
                f"dati_master_{selected_freq_label}.csv", 
                "text/csv"
            )
        with c2: 
            st.info("👉 Ora puoi navigare negli ottimizzatori. I dati sono pronti.")
    elif not error_flag:
        st.warning("Nessun dato fornito. Carica un CSV o inserisci dei Ticker.")
