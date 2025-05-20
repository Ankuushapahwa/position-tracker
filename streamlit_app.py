import streamlit as st
import pandas as pd
import yfinance as yf
import urllib.error

# === CACHED SYMBOL LOADING ===
@st.cache_data
def load_symbols():
    url = 'https://raw.githubusercontent.com/datasets/nse/master/data/nse-listed.csv'
    try:
        df_sym = pd.read_csv(url)
        return df_sym['Symbol'].dropna().tolist()
    except Exception as e:
        st.error(f"Failed to load symbol list: {e}")
        return []

# Initialize session state for positions
if 'positions' not in st.session_state:
    st.session_state.positions = []

st.title("NSE Position Tracking Dashboard")

# --- Input Form ---
with st.form(key='add_position'):
    col1, col2 = st.columns(2)

    with col1:
        symbols = load_symbols()
        if symbols:
            symbol = st.selectbox('Symbol', options=symbols)
        else:
            symbol = st.text_input('Symbol')
        position_type = st.selectbox('Position Type', ['Long', 'Short'])
        quantity = st.number_input('Quantity', min_value=1, value=1)

    with col2:
        entry_price = st.number_input('Entry Price', min_value=0.0, format="%.2f")
        stop_loss   = st.number_input('Stop Loss',    min_value=0.0, format="%.2f")
        target_price= st.number_input('Target Price', min_value=0.0, format="%.2f")

    # Submit button must be inside form
    submitted = st.form_submit_button('Add Position')
    if submitted:
        # Validate symbol
        if not symbol:
            st.warning("Please enter or select a symbol.")
        else:
            st.session_state.positions.append({
                'Symbol': symbol,
                'Type': position_type,
                'Qty': quantity,
                'Entry': entry_price,
                'SL': stop_loss,
                'Target': target_price
            })

# --- Fetch and Display Positions ---
if st.session_state.positions:
    df = pd.DataFrame(st.session_state.positions)
    live_prices, pl_amt, max_loss_amt, target_profit_amt = [], [], [], []

    for _, row in df.iterrows():
        try:
            ticker = yf.Ticker(row['Symbol'] + '.NS')
            price = ticker.info.get('regularMarketPrice', 0.0)
        except Exception:
            price = 0.0
        live_prices.append(price)

        if row['Type'] == 'Long':
            pl  = (price - row['Entry']) * row['Qty']
            risk= (row['Entry'] - row['SL']) * row['Qty']
            tgt = (row['Target'] - row['Entry']) * row['Qty']
        else:
            pl  = (row['Entry'] - price) * row['Qty']
            risk= (row['SL'] - row['Entry']) * row['Qty']
            tgt = (row['Entry'] - row['Target']) * row['Qty']

        pl_amt.append(pl)
        max_loss_amt.append(max(0, risk))
        target_profit_amt.append(max(0, tgt))

    df['Current Price']  = live_prices
    df['P/L']            = pl_amt
    df['Max Loss']       = max_loss_amt
    df['Target Profit']  = target_profit_amt

    # --- Summary Metrics ---
    total_pl     = sum(pl_amt)
    total_risk   = sum(max_loss_amt)
    total_target = sum(target_profit_amt)

    st.subheader('Portfolio Summary')
    m1, m2, m3 = st.columns(3)
    m1.metric("Total P/L", f"₹{total_pl:,.2f}")
    m2.metric("Total Risk (Max Loss)", f"₹{total_risk:,.2f}")
    m3.metric("Total Target Profit", f"₹{total_target:,.2f}")

    st.subheader('Open Positions')
    st.dataframe(df, use_container_width=True)
else:
    st.info('No positions added yet.')
