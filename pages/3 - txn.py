import streamlit as st
import db
import pandas as pd
from datetime import datetime, timedelta
st.title('Transaction Management')
# col1, col2 = st.columns(2)
# with col1:
#     add_trasaction = st.button('Add Transactions')

# with col2:
#     txn_history = st.button('Transaction History')

# if add_trasaction:
st.header('Add Single Transaction')
## transaction functions##
ticker = st.text_input("Ticker", help = 'enter ticker symbol')
txn_type = st.selectbox("Transaction Type",["Buy","Sell"], help = 'buy or sell transactions only')
qty = st.number_input("Quantity", min_value = 0, help = 'enter transaction quantity')
cost_price = st.number_input("Txn Price", min_value = 0, help = 'enter txn price')
txn_date = st.date_input('Transaction Date')

if st.button('Submit'):
    txn_date_str = txn_date.isoformat()
    db.add_transaction(ticker, txn_type, qty, cost_price, txn_date_str)
    db.update_ticker(ticker, txn_type,qty, cost_price)
    st.success('Added transaction successfully')

st.markdown('---')

st.header('Upload CSV')
uploaded_file = st.file_uploader("Upload Transactions CSV", type = "csv", help ="CSV files only!")
if st.button('Upload File'):
    if uploaded_file is not None:
        df_transactions = pd.read_csv(uploaded_file, dtype={'Date': str})
        db.bulk_upload_transactions(df_transactions)
        st.success("Upload success!")
        st.session_state.file_uploader = None
    else:
        st.error('Please upload a file!')
    
st.markdown('---')



st.header('Transaction History')
#date range filter
# default_end_date = datetime.today()
# default_start_date = default_end_date - timedelta(days=7)
# start_date, end_date = st.date_input("Select date range", [default_start_date,default_end_date])
date_range = st.date_input("Select date range",[])

if len(date_range) == 2:
    start_date, end_date = date_range
elif len(date_range) == 1:
    start_date = end_date = date_range[0]
else:
    start_date = datetime(2020,1,1)
    end_date = datetime.today()

ticker_list = db.get_ticker_list()
selected_tickers = st.multiselect("Select Ticker Symbols", ticker_list)

if st.button('Fetch Transactions'):
    transactions_data = db.get_transactions_for_tickers(selected_tickers, start_date, end_date)
    df_transactions = pd.DataFrame(transactions_data)
    st.dataframe(df_transactions)

else:
    st.write("Select a date range and or tickers to view transaction history")

