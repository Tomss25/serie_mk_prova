import streamlit as st
st.header("📖 Nota Metodologica")
st.markdown("""
### 1. Data Integrity & Alignment
L'engine applica un limite restrittivo al forward-fill (3 giorni) ed elimina le distorsioni tipiche delle festività geograficamente disallineate per preservare la volatilità reale.

### 2. Paradosso di Markowitz e Difesa CVaR
A differenza della Media-Varianza che penalizza i guadagni asimmetrici, l'algoritmo **CVaR** isola il 5% peggiore delle casistiche per costruire un portafoglio antifragile. La simulazione avviene tramite Bootstrap OOS, non con un fallace Moto Browniano.

### 3. Tier Optimizer: Lotta alla Forza Bruta e al Lookahead Bias
Il calcolo combinatorio $O(N^k)$ viene arginato da un filtro Greedy che agisce su listini maggiori di 15 asset. I grafici storici di questa sezione sono dichiaratamente *In-Sample*, proteggendo l'analista dall'illusione cognitiva del Lookahead Bias.
""")
