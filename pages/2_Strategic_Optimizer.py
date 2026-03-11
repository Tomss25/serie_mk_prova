import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from core_engine import get_optimal_weights, get_cvar_weights, bootstrap_projection

st.header("⚖️ Strategic Optimizer")

df = st.session_state.get('shared_df')
if df is None:
    st.info("Carica i dati dal Data Engine per iniziare.")
    st.stop()

with st.sidebar:
    rf = st.number_input("Risk Free Rate (%)", value=3.0) / 100
    min_w = st.slider("Min Weight", 0.0, 0.2, 0.0)
    max_w = st.slider("Max Weight", 0.1, 1.0, 0.4)

returns = df.pct_change().dropna()
mu = returns.mean() * 252
sigma = returns.cov() * 252

with st.spinner("Ottimizzazione..."):
    w_mk = get_optimal_weights(mu, sigma, min_w, max_w, rf)
    w_cvar = get_cvar_weights(returns.values, min_w, max_w, 0.05)
    
tab1, tab2 = st.tabs(["📊 Allocazioni Comparative", "🔮 Simulazione CVaR (Bootstrap)"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Markowitz")
        st.dataframe(pd.DataFrame({"Asset": df.columns, "Peso %": np.round(w_mk*100, 2)}).set_index("Asset"))
    with c2:
        st.subheader("Min-CVaR (Tail Risk)")
        st.dataframe(pd.DataFrame({"Asset": df.columns, "Peso %": np.round(w_cvar*100, 2)}).set_index("Asset"))

with tab2:
    st.markdown("**Simulazione di Scenari OOS (Out-Of-Sample):** Campionamento Bootstrap con reimmissione.")
    percentiles = bootstrap_projection(returns, w_cvar, years=5)
    
    fig = go.Figure()
    x = np.arange(len(percentiles[2]))
    fig.add_trace(go.Scatter(x=x, y=percentiles[4], fill=None, mode='lines', line_color='rgba(26, 115, 232, 0.1)', showlegend=False))
    fig.add_trace(go.Scatter(x=x, y=percentiles[0], fill='tonexty', mode='lines', line_color='rgba(217, 48, 37, 0.5)', name="Worst 5%"))
    fig.add_trace(go.Scatter(x=x, y=percentiles[2], mode='lines', line_color='#1A73E8', name="Mediana"))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)
