import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from core_engine import get_optimal_weights, get_cvar_weights, bootstrap_projection

st.header("⚙️ Strategic Portfolio Optimizer")

# --- SCELTA SORGENTE DATI ---
data_source = st.radio("Sorgente Dati:", ["Usa dati estratti dal Data Engine", "Carica CSV Esterno"], horizontal=True)

df = None
if data_source == "Usa dati estratti dal Data Engine":
    if st.session_state['shared_df'] is not None:
        df = st.session_state['shared_df']
        st.success(f"✅ Dati caricati in memoria ({df.shape[1]} asset).")
    else:
        st.warning("Nessun dato in memoria. Vai al Data Engine prima, oppure carica un CSV.")
else:
    uploaded_file = st.file_uploader("Carica CSV (Date index, Total Return)", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file, sep=';', decimal=',', index_col=0, parse_dates=True).ffill(limit=3).dropna()

if df is not None and not df.empty:
    with st.sidebar:
        st.subheader("Parametri Modello")
        rf = st.number_input("Risk Free Rate (%)", value=3.0) / 100
        min_w = st.slider("Min Weight", 0.0, 0.2, 0.0)
        max_w = st.slider("Max Weight", 0.1, 1.0, 0.4)
        run_opt = st.button("🧠 Esegui Ottimizzazione")

    if st.sidebar.button("🧠 Esegui Ottimizzazione", key="run_opt_main"):
        returns = df.pct_change().dropna()
        mu = returns.mean() * 252
        sigma = returns.cov() * 252
        
        with st.spinner("Elaborazione matematica..."):
            w_mk = get_optimal_weights(mu, sigma, min_w, max_w, rf)
            w_cvar = get_cvar_weights(returns.values, min_w, max_w, 0.05)
            
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Markowitz (Media-Varianza)")
            st.write(pd.DataFrame({"Asset": df.columns, "Peso %": np.round(w_mk*100, 2)}))
        with col2:
            st.subheader("CVaR (Difesa Cigni Neri)")
            st.write(pd.DataFrame({"Asset": df.columns, "Peso %": np.round(w_cvar*100, 2)}))
            
        st.markdown("---")
        st.subheader("🔮 Proiezione Futura Antifragile (Bootstrap Storico su Pesi CVaR)")
        
        proj_years = 5
        percentiles = bootstrap_projection(returns, w_cvar, proj_years)
        
        fig = go.Figure()
        x_axis = np.arange(len(percentiles[2]))
        fig.add_trace(go.Scatter(x=x_axis, y=percentiles[4], fill=None, mode='lines', line_color='rgba(100, 255, 218, 0.1)'))
        fig.add_trace(go.Scatter(x=x_axis, y=percentiles[0], fill='tonexty', mode='lines', line_color='rgba(239, 68, 68, 0.5)', name="Worst 5%"))
        fig.add_trace(go.Scatter(x=x_axis, y=percentiles[2], mode='lines', line_color='#64FFDA', name="Mediana"))
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        
        st.plotly_chart(fig, use_container_width=True)