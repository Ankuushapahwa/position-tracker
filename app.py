import streamlit as st
import pandas as pd
import yfinance as yf

# Initialize session state
if 'positions' not in st.session_state:
    st.session_state.positions = []

st.title("NSE Position Tracking Dashboard")

# --- Input Form ---
with st.form(key='add_position'):
    col1, col2 = st.columns(2)
    with col1:
        # Load and cache symbol list
        @st.cache_data
        def load_symbols():
            url = 'https://raw.githubusercontent.com/datasets/nse/master/data/nse-listed.csv'
            df_sym = pd.read_csv(url)
            return df_sym['Symbol'].tolist()

        symbols = load_symbols()
        symbol = st.selectbox('Symbol', options=symbols)
        position_type = st.selectbox('Position Type', ['Long', 'Short'])
        quantity = st.number_input('Quantity', min_value=1, value=1)
    with col2:
        entry_price = st.number_input('Entry Price', min_value=0.0, format="%.2f")
        stop_loss = st.number_input('Stop Loss', min_value=0.0, format="%.2f")
        target_price = st.number_input('Target Price', min_value=0.0, format="%.2f")

    submitted = st.form_submit_button('Add Position')
    if submitted:
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
    live_prices = []
    pl_amt = []
    max_loss_amt = []
    target_profit_amt = []

    for _, row in df.iterrows():
        ticker = yf.Ticker(row['Symbol'] + '.NS')
        price = ticker.info.get('regularMarketPrice', 0.0)
        live_prices.append(price)

        if row['Type'] == 'Long':
            pl = (price - row['Entry']) * row['Qty']
            max_loss = (row['Entry'] - row['SL']) * row['Qty']
            tgt_profit = (row['Target'] - row['Entry']) * row['Qty']
        else:
            pl = (row['Entry'] - price) * row['Qty']
            max_loss = (row['SL'] - row['Entry']) * row['Qty']
            tgt_profit = (row['Entry'] - row['Target']) * row['Qty']

        pl_amt.append(pl)
        max_loss_amt.append(max_loss)
        target_profit_amt.append(tgt_profit)

    df['Current Price'] = live_prices
    df['P/L'] = pl_amt
    df['Max Loss'] = max_loss_amt
    df['Target Profit'] = target_profit_amt

    # --- Summary Metrics ---
    total_pl = sum(pl_amt)
    total_risk = sum(max_loss_amt)
    total_target = sum(target_profit_amt)

    st.subheader('Portfolio Summary')
    m1, m2, m3 = st.columns(3)
    m1.metric(label="Total P/L", value=f"₹{total_pl:,.2f}")
    m2.metric(label="Total Risk (Max Loss)", value=f"₹{total_risk:,.2f}")
    m3.metric(label="Total Target Profit", value=f"₹{total_target:,.2f}")

    st.subheader('Open Positions')
    st.dataframe(df)
else:
    st.info('No positions added yet.')
