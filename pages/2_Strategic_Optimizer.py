import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from core_engine import get_optimal_weights, get_cvar_weights, bootstrap_projection

st.header("⚖️ 2. ottimizzazione mark")
st.markdown("Dashboard comparativa: Media-Varianza Classica (Markowitz) vs Ottimizzazione Antifragile (Min-CVaR Tail Risk).")

df = st.session_state.get('shared_df')
if df is None:
    st.warning("⚠️ Nessun dato in memoria. Torna alla pagina '1. Serie storiche' ed estrai un dataset per iniziare.")
    st.stop()

with st.sidebar:
    st.markdown("### ⚙️ Parametri Modello")
    rf = st.number_input("Risk Free Rate (%)", value=3.0, step=0.1) / 100
    min_w = st.slider("Peso Minimo per Asset", 0.0, 0.2, 0.0, step=0.01)
    max_w = st.slider("Peso Massimo per Asset", 0.1, 1.0, 0.4, step=0.05)
    st.info("I vincoli si applicano simultaneamente a entrambi i motori di ottimizzazione.")

returns = df.pct_change().dropna()
mu = returns.mean() * 252
sigma = returns.cov() * 252

with st.spinner("Calcolo matrici di covarianza e ottimizzazione code in corso..."):
    w_mk = get_optimal_weights(mu, sigma, min_w, max_w, rf)
    w_cvar = get_cvar_weights(returns.values, min_w, max_w, 0.05)
    
tab1, tab2 = st.tabs(["📊 Allocazioni Comparative", "🔮 Simulazione CVaR (Bootstrap)"])

with tab1:
    st.markdown("#### Matrice dei Pesi Ottimali")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("**Media-Varianza (Markowitz)**")
        df_mk = pd.DataFrame({"Asset": df.columns, "Peso": w_mk}).sort_values(by="Peso", ascending=False)
        st.dataframe(
            df_mk.style.format({"Peso": "{:.2%}"}).background_gradient(cmap="Blues", subset=["Peso"]),
            use_container_width=True, hide_index=True
        )
        
    with c2:
        st.markdown("**Min-CVaR (Tail Risk Defense)**")
        df_cvar = pd.DataFrame({"Asset": df.columns, "Peso": w_cvar}).sort_values(by="Peso", ascending=False)
        st.dataframe(
            df_cvar.style.format({"Peso": "{:.2%}"}).background_gradient(cmap="Greens", subset=["Peso"]),
            use_container_width=True, hide_index=True
        )

with tab2:
    st.markdown("#### Analisi Out-Of-Sample del Portafoglio CVaR")
    st.caption("Proiezione a 5 anni tramite campionamento Bootstrap con reimmissione. Rispetta la non-normalità storica dei rendimenti.")
    
    percentiles = bootstrap_projection(returns, w_cvar, years=5)
    
    # Layout grafico "Light & Crisp"
    fig = go.Figure()
    x = np.arange(len(percentiles[2]))
    
    # Banda 5%-95% (Grigio leggero/Azzurro)
    fig.add_trace(go.Scatter(x=x, y=percentiles[4], fill=None, mode='lines', line_color='rgba(26, 115, 232, 0.0)', showlegend=False))
    fig.add_trace(go.Scatter(x=x, y=percentiles[0], fill='tonexty', mode='lines', line_color='rgba(217, 48, 37, 0.1)', name="Worst 5% / Best 95%"))
    
    # Linee principali
    fig.add_trace(go.Scatter(x=x, y=percentiles[0], mode='lines', line=dict(color='#D93025', width=2, dash='dot'), name="Pessimo (P05)"))
    fig.add_trace(go.Scatter(x=x, y=percentiles[2], mode='lines', line=dict(color='#1A73E8', width=3), name="Mediana (P50)"))
    
    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis_title="Valore Capitale (Base 100)",
        xaxis_title="Giorni di Trading Futuri"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Metriche riassuntive
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("Valore Atteso (P50)", f"{percentiles[2][-1]:.1f}", delta="Scenario Base")
    col_kpi2.metric("Worst Case (P05)", f"{percentiles[0][-1]:.1f}", delta="Rischio Estremo", delta_color="inverse")
    col_kpi3.metric("Best Case (P95)", f"{percentiles[4][-1]:.1f}", delta="Scenario Ottimistico")
