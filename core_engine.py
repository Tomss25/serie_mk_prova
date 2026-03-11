import pandas as pd
import numpy as np
import yfinance as yf
import mstarpy
from scipy.optimize import minimize
from sklearn.covariance import LedoitWolf
import streamlit as st

# --- DATA FETCHING (Cachata per non bruciare le API) ---
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_yahoo(ticker, start_dt):
    try:
        df = yf.download(ticker, start=start_dt, progress=False)
        if not df.empty:
            col = 'Adj Close' if 'Adj Close' in df.columns else 'Close'
            return df[col].squeeze().dropna()
    except Exception as e:
        print(f"YF Error on {ticker}: {e}")
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_morningstar(isin, start_dt, end_dt):
    try:
        fund = mstarpy.Funds(term=isin, country="it")
        history = fund.nav(start_date=start_dt, end_date=end_dt, frequency="daily")
        if history:
            df = pd.DataFrame(history)
            df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
            return df.set_index('date')['nav'].dropna()
    except Exception as e:
        print(f"MStar Error on {isin}: {e}")
    return None

def align_and_clean_data(series_dict):
    """Allinea le serie evitando corruzione da ffill infinito."""
    df = pd.DataFrame(series_dict)
    # Limita il forward fill a max 3 giorni (es. weekend/feste locali)
    df = df.ffill(limit=3).dropna(how='any')
    return df

# --- MATH OPTIMIZATION ---
def get_optimal_weights(mu, sigma, min_weight, max_weight, rf):
    num_assets = len(mu)
    actual_max_weight = max(max_weight, 1.0 / num_assets + 0.01)
    args = (mu, sigma, rf)
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((min_weight, actual_max_weight) for _ in range(num_assets))
    
    def neg_sharpe(w, mu, sigma, rf):
        ret = np.sum(mu * w)
        vol = np.sqrt(np.dot(w.T, np.dot(sigma, w)))
        return -(ret - rf) / vol if vol > 0 else 1e6

    res = minimize(neg_sharpe, [1./num_assets]*num_assets, args=args, bounds=bounds, constraints=constraints, method='SLSQP')
    return res.x if res.success else None

def get_cvar_weights(returns_matrix, min_weight, max_weight, alpha=0.05):
    num_scenarios, num_assets = returns_matrix.shape
    actual_max_weight = max(max_weight, 1.0 / num_assets + 0.01)
    
    def cvar_objective(params):
        w, gamma = params[:-1], params[-1]
        shortfall = np.maximum(-np.dot(returns_matrix, w) - gamma, 0)
        return gamma + np.sum(shortfall) / (alpha * num_scenarios)

    initial_w = [1./num_assets] * num_assets
    initial_gamma = -np.percentile(np.dot(returns_matrix, initial_w), alpha * 100)
    
    bounds = tuple((min_weight, actual_max_weight) for _ in range(num_assets)) + ((None, None),)
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x[:-1]) - 1})

    res = minimize(cvar_objective, np.append(initial_w, initial_gamma), method='SLSQP', bounds=bounds, constraints=constraints)
    return res.x[:-1] if res.success else None

def bootstrap_projection(returns_df, weights, years, num_sims=5000):
    """Sostituisce il Moto Browniano irreale. Usa il campionamento con re-immissione."""
    port_returns = np.dot(returns_df.values, weights)
    days = int(252 * years)
    # Campiona direttamente dai veri rendimenti giornalieri passati (code grasse incluse)
    simulated_returns = np.random.choice(port_returns, size=(days, num_sims), replace=True)
    
    sim_matrix = np.zeros((days + 1, num_sims))
    sim_matrix[0] = 100.0
    sim_matrix[1:] = 100.0 * np.cumprod(1 + simulated_returns, axis=0)
    
    return np.percentile(sim_matrix, [5, 25, 50, 75, 95], axis=1)