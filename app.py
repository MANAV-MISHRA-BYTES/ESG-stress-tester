import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px

st.set_page_config(page_title="ESG Stress Tester", layout="wide")

def get_stock_data(tickers):
    if not tickers:
        return pd.DataFrame()
    data = yf.download(tickers, period="1y")['Close']
    if data.empty:
        return pd.DataFrame()
    current_prices = data.iloc[-1]
    return current_prices

def generate_mock_esg(tickers):
    np.random.seed(42)
    data = {
        'Ticker': tickers,
        'E_Score': np.random.randint(30, 95, len(tickers)),
        'S_Score': np.random.randint(30, 95, len(tickers)),
        'G_Score': np.random.randint(30, 95, len(tickers))
    }
    return pd.DataFrame(data).set_index('Ticker')

def calculate_stress(portfolio, esg_data, scenario, severity):
    stressed_portfolio = portfolio.copy()
    
    impact_factor = 0
    target_score = ''

    if scenario == 'Climate Policy Shock (E)':
        target_score = 'E_Score'
        impact_factor = 0.15 * severity 
    elif scenario == 'Labor Strike / Social Unrest (S)':
        target_score = 'S_Score'
        impact_factor = 0.10 * severity
    elif scenario == 'Governance Scandal (G)':
        target_score = 'G_Score'
        impact_factor = 0.20 * severity

    for ticker in stressed_portfolio.index:
        score = esg_data.loc[ticker, target_score]
        risk_exposure = 1 - (score / 100)
        shock = impact_factor * risk_exposure
        stressed_portfolio[ticker] = stressed_portfolio[ticker] * (1 - shock)
    
    return stressed_portfolio

st.title("ESG Portfolio Stress Tester")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Configuration")
    default_tickers = "AAPL, MSFT, TSLA, AMZN, GOOGL"
    ticker_input = st.text_area("Enter Tickers (comma separated)", default_tickers)
    investment = st.number_input("Total Investment ($)", value=100000)
    
    tickers = [t.strip().upper() for t in ticker_input.split(',') if t.strip()]
    
    st.subheader("Stress Scenario")
    scenario_type = st.selectbox("Select Scenario", [
        "Climate Policy Shock (E)",
        "Labor Strike / Social Unrest (S)",
        "Governance Scandal (G)"
    ])
    severity = st.slider("Shock Severity (1=Mild, 5=Extreme)", 1, 5, 3)

if tickers:
    prices = get_stock_data(tickers)
    
    if not prices.empty:
        esg_data = generate_mock_esg(tickers)
        
        weights = np.ones(len(tickers)) / len(tickers)
        shares = (investment * weights) / prices
        base_values = shares * prices
        
        stressed_values = calculate_stress(base_values, esg_data, scenario_type, severity)
        
        total_base = base_values.sum()
        total_stressed = stressed_values.sum()
        loss = total_base - total_stressed
        loss_pct = (loss / total_base) * 100

        with col2:
            st.metric(label="Projected Portfolio Value", value=f"${total_stressed:,.2f}", delta=f"-${loss:,.2f} (-{loss_pct:.2f}%)")
            
            df_display = pd.DataFrame({
                'Current Price': prices,
                'E Score': esg_data['E_Score'],
                'S Score': esg_data['S_Score'],
                'G Score': esg_data['G_Score'],
                'Base Value': base_values,
                'Stressed Value': stressed_values
            })
            st.dataframe(df_display.style.format("{:.2f}"))

            chart_data = pd.DataFrame({
                'Condition': ['Baseline', 'Stressed'],
                'Value': [total_base, total_stressed]
            })
            fig = px.bar(chart_data, x='Condition', y='Value', color='Condition', 
                         color_discrete_map={'Baseline': '#00CC96', 'Stressed': '#EF553B'},
                         title=f"Portfolio Impact: {scenario_type}")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Could not fetch data. Check tickers.")
