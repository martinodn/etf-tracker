import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from utils import finance, portfolio, watchlist

# Page config
st.set_page_config(page_title="ETF Tracker", page_icon="📈", layout="wide")

# Initialize session state for watchlist
if "watchlist" not in st.session_state:
    # Try to load from Google Sheets
    saved_watchlist = watchlist.load_watchlist()
    st.session_state["watchlist"] = saved_watchlist if saved_watchlist else []

# Sidebar - ISIN Search & Watchlist
with st.sidebar:
    st.header("🔍 Search ETF")
    isin_input = st.text_input("Enter ISIN or Name", placeholder="e.g. IE00B4L5Y983")
    
    if st.button("Search"):
        if isin_input:
            with st.spinner("Searching..."):
                results = finance.search_by_isin(isin_input)
                
                if results:
                    # API search worked, show results
                    st.session_state["search_results"] = results
                else:
                    # API failed or no results - try direct resolution
                    if isin_input not in st.session_state["watchlist"]:
                        st.session_state["watchlist"].append(isin_input)
                        watchlist.save_watchlist(st.session_state["watchlist"])
                        st.success(f"✅ Added '{isin_input}' to watchlist!")
                        st.info("Go to Dashboard to see the data.")
                        st.session_state["search_results"] = []
                    else:
                        st.warning("This ticker is already in your watchlist.")
                        st.session_state["search_results"] = []
        else:
            st.warning("Enter an ISIN or name.")

    if "search_results" in st.session_state and st.session_state["search_results"]:
        st.subheader("Results")
        for res in st.session_state["search_results"]:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{res['symbol']}**")
                st.caption(f"{res['longname']} ({res['exchange']})")
            with col2:
                if st.button("➕", key=f"add_{res['symbol']}"):
                    if res['symbol'] not in st.session_state["watchlist"]:
                        st.session_state["watchlist"].append(res['symbol'])
                        watchlist.save_watchlist(st.session_state["watchlist"])
                        st.success(f"Added {res['symbol']}")
                    else:
                        st.warning("Already in list")

    st.divider()
    st.header("📋 Watchlist")
    if st.session_state["watchlist"]:
        for ticker in st.session_state["watchlist"]:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(ticker)
            with col2:
                if st.button("❌", key=f"remove_{ticker}"):
                    st.session_state["watchlist"].remove(ticker)
                    watchlist.save_watchlist(st.session_state["watchlist"])
                    st.rerun()
    else:
        st.info("Your watchlist is empty.")

# Authentication
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def check_password():
    if st.session_state["password_input"] == st.secrets.get("APP_PASSWORD", "admin"):
        st.session_state["authenticated"] = True
        del st.session_state["password_input"]
    else:
        st.error("Password errata")

if not st.session_state["authenticated"]:
    st.title("🔒 Accesso Richiesto")
    st.text_input("Inserisci Password", type="password", key="password_input", on_change=check_password)
    st.stop()

# Main Content
st.title("📈 ETF Tracker & Portfolio")

tab1, tab2 = st.tabs(["💰 Portfolio", "📊 Dashboard"])

# --- TAB 1: PORTFOLIO ---
with tab1:
    st.header("Portfolio Management")
    
    # Add Transaction Form
    with st.expander("➕ Add Transaction"):
        with st.form("add_transaction_form"):
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                t_date = st.date_input("Date", datetime.today())
            with c2:
                t_isin = st.text_input("ISIN", placeholder="IE00B4L5Y983")
            with c3:
                t_ticker = st.text_input("Ticker", placeholder="e.g. SWDA.MI")
            with c4:
                t_price = st.number_input("Purchase Price", min_value=0.0, step=0.01, format="%.2f")
            with c5:
                t_qty = st.number_input("Quantity", min_value=0.0, step=0.01)
                
            submitted = st.form_submit_button("Save Transaction")
            
            if submitted:
                if t_ticker and t_qty > 0:
                    portfolio.add_transaction(t_date, t_isin, t_ticker, t_price, t_qty)
                    st.success("Transaction saved!")
                    # Add to watchlist if not present
                    if t_ticker not in st.session_state["watchlist"]:
                        st.session_state["watchlist"].append(t_ticker)
                else:
                    st.error("Enter all required data.")

    # Display Portfolio
    port_df = portfolio.load_portfolio()
    
    if not port_df.empty:
        # Fetch current data (prices and names) for all tickers in portfolio
        current_prices = {} 
        ticker_names = {}
        all_tickers = port_df['Ticker'].unique()
        
        for t in all_tickers:
             d = finance.get_etf_data(t)
             if d:
                 current_prices[t] = d['current_price']
                 ticker_names[t] = d['name']
             else:
                 ticker_names[t] = t # Fallback to ticker if no data

        # Prepare display dataframe with Name
        display_df = port_df.copy()
        display_df['Name'] = display_df['Ticker'].map(ticker_names).fillna(display_df['Ticker'])
        
        # Reorder columns: Date, Name, Ticker, ISIN, Price, Quantity
        cols = ['Date', 'Name', 'Ticker', 'ISIN', 'Price', 'Quantity']
        # Filter cols to ensure they exist (ISIN might be missing in old data)
        existing_cols = [c for c in cols if c in display_df.columns]
        display_df = display_df[existing_cols]

        st.subheader("Transaction History")
        st.dataframe(display_df, width='stretch')
        
        st.divider()

        # Comparative Chart
        st.subheader("📈 Comparative Performance")
        
        # Find the most recent purchase date
        try:
            # Ensure Date column is datetime
            port_df['Date'] = pd.to_datetime(port_df['Date'])
            last_purchase_date = port_df['Date'].max()
            
            st.caption(f"Performance comparison starting from the last purchase date: {last_purchase_date.strftime('%d %B %Y')}")
            
            # Fetch history
            all_tickers = port_df['Ticker'].unique().tolist()
            comp_data = finance.get_comparative_data(all_tickers, last_purchase_date)
            
            if not comp_data.empty:
                # Rename columns to use ETF Names
                comp_data = comp_data.rename(columns=ticker_names)
                
                fig = go.Figure()
                for column in comp_data.columns:
                    fig.add_trace(go.Scatter(
                        x=comp_data.index,
                        y=comp_data[column],
                        mode='lines',
                        name=column
                    ))
                
                fig.update_layout(
                    title="Relative Performance (%)",
                    xaxis_title="Date",
                    yaxis_title="Change (%)",
                    hovermode="x unified",
                    height=400,
                    margin=dict(l=0, r=0, t=30, b=0)
                )
                st.plotly_chart(fig, config={'responsive': True})
            else:
                st.warning("Not enough data to generate comparison chart.")
                
        except Exception as e:
            st.error(f"Error generating chart: {e}")

        st.divider()
        
        # Calculate Performance
        perf_df = portfolio.calculate_performance(port_df, current_prices)
        
        if not perf_df.empty:
            st.subheader("Portfolio Performance")
            
            # Overall Metrics
            total_invested = perf_df['Invested Value'].sum()
            total_value = perf_df['Current Value'].sum()
            total_gain = total_value - total_invested
            total_gain_pct = (total_gain / total_invested) * 100 if total_invested != 0 else 0
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Value", f"€ {total_value:,.2f}")
            m2.metric("Invested", f"€ {total_invested:,.2f}")
            m3.metric("Total Gain/Loss", f"€ {total_gain:,.2f}", f"{total_gain_pct:.2f}%")
            
            # Detailed Table
            st.dataframe(
                perf_df,
                width='stretch',
                column_config={
                    "Gain/Loss %": st.column_config.NumberColumn(
                        "Gain/Loss %",
                        format="%.2f%%"
                    ),
                    "Current Value": st.column_config.NumberColumn(
                        "Current Value",
                        format="€ %.2f"
                    ),
                     "Invested Value": st.column_config.NumberColumn(
                        "Invested",
                        format="€ %.2f"
                    )
                }
            )
    else:
        st.info("No transactions recorded.")

# --- TAB 2: DASHBOARD ---
with tab2:
    if not st.session_state["watchlist"]:
        st.info("Add ETFs to the watchlist from the sidebar to see data.")
    else:
        # Time range controls
        col_change, col_chart = st.columns(2)
        with col_change:
            change_period = st.selectbox(
                "% Change",
                options=["1d", "1mo", "3mo", "6mo", "1y"],
                format_func=lambda x: {
                    "1d": "Daily",
                    "1mo": "Monthly",
                    "3mo": "Quarterly",
                    "6mo": "Semi-Annual",
                    "1y": "Annual"
                }[x],
                index=0
            )
        with col_chart:
            chart_period = st.selectbox(
                "Chart Period",
                options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
                format_func=lambda x: {
                    "1mo": "1 Month",
                    "3mo": "3 Months",
                    "6mo": "6 Months",
                    "1y": "1 Year",
                    "2y": "2 Years",
                    "5y": "5 Years",
                    "max": "Max"
                }[x],
                index=3  # Default to 1y
            )
        
        st.divider()
        
        # Fetch data for all tickers in watchlist
        # We re-fetch here for the dashboard visualization
        
        for ticker in st.session_state["watchlist"]:
            data = finance.get_etf_data(ticker, period=chart_period, change_period=change_period)
            
            if data:
                # Update watchlist if symbol changed (e.g. SXR8 -> SXR8.DE)
                if data['symbol'] != ticker:
                    idx = st.session_state["watchlist"].index(ticker)
                    st.session_state["watchlist"][idx] = data['symbol']
                    st.rerun()
                
                # Wrap in expander (collapsed by default)
                with st.expander(f"📈 {data['name']} ({data['symbol']}) - {data['currency']} {data['current_price']:.2f}", expanded=False):
                    # Header with metrics
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        st.caption(f"Current price: {data['currency']} {data['current_price']:.2f}")
                    with c2:
                        period_label = {
                            "1d": "Daily",
                            "1mo": "Monthly",
                            "3mo": "Quarterly",
                            "6mo": "Semi-Annual",
                            "1y": "Annual"
                        }.get(change_period, "Change")
                        
                        st.metric(
                            label=f"{period_label} Change",
                            value=f"{data['change']:.2f}",
                            delta=f"{data['pct_change']:.2f}%"
                        )
                    
                    # Chart
                    hist = data['history']
                    if not hist.empty:
                        fig = go.Figure()
                        fig.add_trace(go.Candlestick(
                            x=hist.index,
                            open=hist['Open'],
                            high=hist['High'],
                            low=hist['Low'],
                            close=hist['Close'],
                            name='Price'
                        ))
                        fig.update_layout(
                            height=300, 
                            margin=dict(l=0, r=0, t=0, b=0),
                            xaxis_rangeslider_visible=False
                        )
                        st.plotly_chart(fig, config={'responsive': True})
                    else:
                        st.warning("Historical data not available.")
            else:
                st.error(f"Unable to fetch data for {ticker}")
