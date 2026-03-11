import streamlit as st

st.header("📖 Nota Metodologica Istituzionale")

st.markdown("""
### 1. Data Integrity & Alignment (Data Engine)
Le estrazioni raw da feed eterogenei (Yahoo, Morningstar) soffrono di desincronizzazione del calendario di trading. 
Invece di forzare l'allineamento con un forward-fill infinito (che genera correlazioni fasulle e abbatte artificialmente la volatilità), l'engine applica un limite restrittivo ai giorni riportati e scarta le distorsioni. 

### 2. Illusione Gaussiana & CVaR (Ottimizzatore)
I modelli Media-Varianza classici (Markowitz) presumono rendimenti distribuiti normalmente e penalizzano i guadagni esplosivi come se fossero un rischio. 
L'algoritmo **Conditional Value at Risk (CVaR)** ignora la volatilità media giornaliera e si concentra sull'isolamento del *Tail Risk* (il 5% peggiore delle casistiche storiche), ottimizzando il portafoglio per sopravvivere ai Cigni Neri finanziari.

### 3. Simulazione di Scenari tramite Bootstrap Storico
Evitando di ricadere nella trappola di simulare i prezzi futuri tramite la funzione normale standard, la proiezione utilizza il campionamento Bootstrap con reimmissione. In questo modo gli shock storici, l'asimmetria e l'autocorrelazione intrinseca nei dati non vengono normalizzati, restituendo uno stress-test quantitativamente brutale ma realistico.
""")