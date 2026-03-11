import pandas as pd
import numpy as np
import yfinance as yf
import mstarpy
from scipy.optimize import minimize
import itertools
import streamlit as st

# --- 1. DATA INGESTION ---
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_yahoo(ticker, start_dt):
    try:
        df = yf.download(ticker, start=start_dt, progress=False)
        if not df.empty:
            col = 'Adj Close' if 'Adj Close' in df.columns else 'Close'
            return df[col].squeeze().dropna()
    except: pass
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
    except: pass
    return None

def align_and_clean_data(series_dict):
    return pd.DataFrame(series_dict).ffill(limit=3).dropna(how='any')

# --- 2. STRATEGIC OPTIMIZER ---
def get_optimal_weights(mu, sigma, min_weight, max_weight, rf):
    n = len(mu)
    actual_max = max(max_weight, 1.0 / n + 0.01)
    bnds = tuple((min_weight, actual_max) for _ in range(n))
    cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    
    def neg_sharpe(w):
        vol = np.sqrt(np.dot(w.T, np.dot(sigma, w)))
        return -(np.sum(mu * w) - rf) / vol if vol > 0 else 1e6

    res = minimize(neg_sharpe, [1./n]*n, bounds=bnds, constraints=cons, method='SLSQP')
    return res.x if res.success else None

def get_cvar_weights(returns_matrix, min_w, max_w, alpha=0.05):
    n_scen, n_assets = returns_matrix.shape
    actual_max = max(max_w, 1.0 / n_assets + 0.01)
    
    def cvar_obj(params):
        w, gamma = params[:-1], params[-1]
        shortfall = np.maximum(-np.dot(returns_matrix, w) - gamma, 0)
        return gamma + np.sum(shortfall) / (alpha * n_scen)

    init_w = [1./n_assets] * n_assets
    init_g = -np.percentile(np.dot(returns_matrix, init_w), alpha * 100)
    
    bnds = tuple((min_w, actual_max) for _ in range(n_assets)) + ((None, None),)
    cons = ({'type': 'eq', 'fun': lambda x: np.sum(x[:-1]) - 1})

    res = minimize(cvar_obj, np.append(init_w, init_g), method='SLSQP', bounds=bnds, constraints=cons)
    return res.x[:-1] if res.success else None

def bootstrap_projection(returns_df, weights, years, num_sims=5000):
    port_returns = np.dot(returns_df.values, weights)
    days = int(252 * years)
    sim_ret = np.random.choice(port_returns, size=(days, num_sims), replace=True)
    sim_mat = np.zeros((days + 1, num_sims))
    sim_mat[0] = 100.0
    sim_mat[1:] = 100.0 * np.cumprod(1 + sim_ret, axis=0)
    return np.percentile(sim_mat, [5, 25, 50, 75, 95], axis=1)

# --- 3. TIER OPTIMIZER ---
def get_advanced_stats(weights, returns, annual_factor):
    port_series = returns.dot(np.array(weights))
    ret = port_series.mean() * annual_factor
    vol = port_series.std() * np.sqrt(annual_factor)
    sr = ret / vol if vol != 0 else 0
    down_std = port_series[port_series < 0].std() * np.sqrt(annual_factor)
    sortino = ret / down_std if down_std != 0 else 0
    cum = (1 + port_series).cumprod()
    mdd = ((cum - cum.cummax()) / cum.cummax()).min()
    return ret, vol, sr, sortino, mdd

def get_avg_correlation(data, assets):
    if len(assets) < 2: return 1.0
    corr = data[list(assets)].corr().values
    return corr[np.triu_indices_from(corr, k=1)].mean()

def optimize_subset_portfolio(returns, annual_factor, min_weight=0.0):
    n = len(returns.columns)
    if n * min_weight > 1.0: return None 
        
    def obj(w):
        vol = np.sqrt(np.dot(w.T, np.dot(returns.cov() * annual_factor, w)))
        return -(np.sum(returns.mean() * w) * annual_factor / vol) if vol > 0 else 0

    res = minimize(obj, [1./n]*n, method='SLSQP', bounds=tuple((min_weight, 1) for _ in range(n)), constraints={'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    return res.x if res.success else None

@st.cache_data(show_spinner=False)
def find_best_optimized_combination(df_returns, k, annual_factor, max_corr=1.0, min_w=0.0):
    assets = df_returns.columns.tolist()
    if len(assets) < k or k * min_w > 1.0: return None, None, (0,0,0,0,0)
    
    # SALVAVITA COMPUTAZIONALE
    if len(assets) > 15:
        sharpes = {a: get_advanced_stats([1], df_returns[[a]], annual_factor)[2] for a in assets}
        assets = sorted(sharpes, key=sharpes.get, reverse=True)[:15]

    best_s = -np.inf
    best_c, best_w, best_stats = None, None, None

    for combo in itertools.combinations(assets, k):
        if get_avg_correlation(df_returns, combo) <= max_corr:
            sub = df_returns[list(combo)]
            w = optimize_subset_portfolio(sub, annual_factor, min_w)
            if w is not None:
                stats = get_advanced_stats(w, sub, annual_factor)
                if stats[2] > best_s:
                    best_s, best_c, best_w, best_stats = stats[2], combo, w, stats
            
    return best_c, best_w, best_stats
