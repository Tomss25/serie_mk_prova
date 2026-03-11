import itertools

# --- MATEMATICA 3-TIER MODEL (Combinatoria) ---

def get_advanced_stats(weights, returns, annual_factor):
    weights = np.array(weights)
    port_series = returns.dot(weights)
    
    mean_ret = port_series.mean() * annual_factor
    volatility = port_series.std() * np.sqrt(annual_factor)
    sharpe = mean_ret / volatility if volatility != 0 else 0
    
    negative_returns = port_series[port_series < 0]
    downside_std = negative_returns.std() * np.sqrt(annual_factor)
    sortino = mean_ret / downside_std if downside_std != 0 else 0
    
    cumulative = (1 + port_series).cumprod()
    peak = cumulative.cummax()
    max_drawdown = ((cumulative - peak) / peak).min()
    
    return mean_ret, volatility, sharpe, sortino, max_drawdown

def get_avg_correlation(data, assets):
    if len(assets) < 2: return 1.0
    corr_matrix = data[list(assets)].corr()
    values = corr_matrix.values[np.triu_indices_from(corr_matrix, k=1)]
    return values.mean()

def optimize_subset_portfolio(returns, annual_factor, min_weight=0.0):
    n_assets = len(returns.columns)
    if n_assets * min_weight > 1.0: return None 
        
    def objective(w):
        ret = np.sum(returns.mean() * w) * annual_factor
        vol = np.sqrt(np.dot(w.T, np.dot(returns.cov() * annual_factor, w)))
        return -(ret / vol) if vol > 0 else 0

    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((min_weight, 1) for _ in range(n_assets))
    init_guess = [1./n_assets for _ in range(n_assets)]
    
    try:
        result = minimize(objective, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
        return result.x if result.success else None
    except: 
        return None

@st.cache_data(show_spinner=False)
def find_best_optimized_combination(df_returns, k, annual_factor, max_corr_threshold=1.0, min_w=0.0):
    assets = df_returns.columns.tolist()
    if len(assets) < k or k * min_w > 1.0: 
        return None, None, (0,0,0,0,0)
    
    best_sharpe = -np.inf
    best_combo, best_weights, best_full_stats = None, None, None

    for combo in itertools.combinations(assets, k):
        current_corr = get_avg_correlation(df_returns, combo)
        if current_corr <= max_corr_threshold:
            subset = df_returns[list(combo)]
            weights = optimize_subset_portfolio(subset, annual_factor, min_weight=min_w)
            
            if weights is not None:
                r, v, s, sort, mdd = get_advanced_stats(weights, subset, annual_factor)
                if s > best_sharpe:
                    best_sharpe = s
                    best_combo = combo
                    best_weights = weights
                    best_full_stats = (r, v, s, sort, mdd)
            
    return best_combo, best_weights, best_full_stats
