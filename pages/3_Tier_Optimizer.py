import streamlit as st
import pandas as pd
import io
import plotly.express as px
import re
from core_engine import get_advanced_stats, get_avg_correlation, find_best_optimized_combination

st.header("🎯 3. three lines opt")
st.markdown("Motore combinatorio intelligente. Genera i portafogli ottimali per singola asset class, coppia e terzetto.")

def clean_name(name): return re.sub(r'\s*\(.*\)', '', str(name)).strip()
def format_comp(assets, weights):
    return " + ".join([f"{clean_name(a)} ({w*100:.0f}%)" for a, w in sorted(zip(assets, weights), key=lambda x: x[1], reverse=True) if w > 0.001])

df = st.session_state.get('shared_df')
if df is None:
    st.warning("⚠️ Nessun dato in memoria. Usa il Data Engine per caricare le serie storiche.")
    st.stop()

with st.sidebar:
    st.markdown("### ⚙️ Filtri Combinatori")
    days_diff = (df.index[1] - df.index[0]).days
    default_freq = 12 if days_diff >= 28 else (52 if days_diff >= 5 else 252)
    annual_factor = st.selectbox("Frequenza Dati (Annualization Factor)", [252, 52, 12], index=[252, 52, 12].index(default_freq))
    
    max_corr = st.slider("Max Correlazione Interna Ammessa", 0.0, 1.0, 1.0, 0.05)
    min_w = st.slider("Peso Minimo Asset (%)", 0, 33, 10, 1) / 100.0
    
    st.markdown("### 🎯 Selezione")
    manual_ph = st.empty()

assets = df.columns.tolist()
returns = df.pct_change().dropna()

if len(assets) > 15:
    st.info("ℹ️ Il listino supera i 15 asset. Pre-filtro computazionale Greedy attivato per preservare la stabilità del server.")

with st.spinner('Ricerca algoritmica delle migliori combinazioni in corso...'):
    sharpes = {a: get_advanced_stats([1], returns[[a]], annual_factor)[2] for a in assets}
    best_single = max(sharpes, key=sharpes.get)
    
    manual_asset = manual_ph.selectbox("Forza Asset in Linea 1", assets, index=assets.index(best_single) if best_single in assets else 0)
    l1_stats = get_advanced_stats([1], returns[[manual_asset]], annual_factor)
    
    p_a, p_w, p_s = find_best_optimized_combination(returns, 2, annual_factor, max_corr, min_w)
    t_a, t_w, t_s = find_best_optimized_combination(returns, 3, annual_factor, max_corr, min_w)

tab1, tab2, tab3 = st.tabs(["📋 DASHBOARD RISULTATI", "🔗 MATRICE CORRELAZIONE", "📈 IN-SAMPLE EQUITY"])

with tab1:
    st.markdown("#### Riepilogo Allocazioni Ottimali")
    data = []
    def m_row(lbl, a, w, c, s):
        if not a: return None
        return {"Strategia": lbl, "Allocazione": format_comp(a, w) if isinstance(a, tuple) else f"{clean_name(a)} (100%)", 
                "Correlazione": f"{c:.2f}" if isinstance(c, float) else "N/A", "Rend. Annuo": f"{s[0]*100:.1f}%", 
                "Max DD": f"{s[4]*100:.1f}%", "Sharpe": f"{s[2]:.2f}", "Volatilità": f"{s[1]*100:.1f}%"}
    
    data.append(m_row("LINEA 1 (Best Single)", manual_asset, [1], 1.0, l1_stats))
    if p_a: data.append(m_row("LINEA 2 (Best Pair)", p_a, p_w, get_avg_correlation(df, p_a), p_s))
    if t_a: data.append(m_row("LINEA 3 (Best Triplet)", t_a, t_w, get_avg_correlation(df, t_a), t_s))

    df_rep = pd.DataFrame([r for r in data if r])
    st.dataframe(df_rep, hide_index=True, use_container_width=True)

    c_btn1, c_btn2 = st.columns([4, 1])
    with c_btn2:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer: df_rep.to_excel(writer, index=False)
        st.download_button("📥 Esporta in Excel", data=buffer.getvalue(), file_name="Report_Tier.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

with tab2:
    st.markdown("#### Analisi Correlazione incrociata")
    u = list(set([manual_asset] + list(p_a or []) + list(t_a or [])))
    
    # Layout chiaro e pulito
    fig_corr = px.imshow(
        returns[u].corr(), text_auto=".2f", 
        color_continuous_scale='RdBu_r', zmin=-1, zmax=1,
        template='plotly_white'
    )
    fig_corr.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_corr, use_container_width=True)

with tab3:
    st.error("⚠️ **Bias Cognitivo (In-Sample):** L'equity line sottostante applica pesi calcolati a posteriori sull'intero periodo storico. Non usare come simulatore di rendimento futuro.")
    
    cdf = pd.DataFrame(index=returns.index)
    cdf[f"L1: {clean_name(manual_asset)}"] = (1 + returns[manual_asset]).cumprod() * 100
    if p_a: cdf["L2: Pair"] = (1 + returns[list(p_a)].dot(p_w)).cumprod() * 100
    if t_a: cdf["L3: Triplet"] = (1 + returns[list(t_a)].dot(t_w)).cumprod() * 100
    
    # Grafico moderno, sfondo bianco, linee nitide
    fig_eq = px.line(cdf, template='plotly_white', color_discrete_sequence=['#5F6368', '#1A73E8', '#34A853'])
    fig_eq.update_layout(
        yaxis_title="Valore Netto (Base 100)", 
        xaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None),
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig_eq, use_container_width=True)
