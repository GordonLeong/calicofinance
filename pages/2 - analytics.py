## import libraries ##
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import db
### UI Setup##
st.set_page_config(
     page_title="Project Kaizen",
     page_icon="🐱🐾",
)
st.title('Investment Analytics')

st.header("Portfolio Summary")
pf_last_update_date = db.get_portfolio_update_date()
pf_total_value = db.get_total_portfolio_value()
st.write(f"_Summary as of {pf_last_update_date}_")
st.write(f"**Total Portfolio Value** ${pf_total_value:,.2f}")

ticker_list = db.get_ticker_list()
st.markdown(
    """
    <style>
    .section {
        background-color: black;
        padding: 10px;
        margin: 10px 0;
    }
     .section h2 {
        color: white;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.container():
    st.markdown('<div class="section"><h2>Market Data</h2></div>', unsafe_allow_html=True)
    if st.button("Refresh Market Prices!", help = "Fetches latest EOD closing price and calculates summary statistics"):
          success = db.update_market_prices(ticker_list)
          if success:
               st.success("Market prices updated successfully!")
          else:
               st.error("Error updating market prices")
    if st.button("Refresh Cost Values", help = "Update cost values"):
          success = db.update_cost_values()

          if success:
               st.success("Cost values updated successfully!")
          else:
               st.error("Error updating cost values")
with st.container():
    st.markdown('<div class="section"><h2>Portfolio</h2></div>', unsafe_allow_html=True)

    if st.button("Show Table", help = "Portfolio data table"):
          pf_data = []
          for ticker in ticker_list:
               equity_data = db.get_equity_data(ticker)
               market_price_formatted = "${:,.2f}".format(equity_data['market_price'])
               market_value_formatted = "${:,.2f}".format(equity_data['market_value'])
               cost_value_formatted = "${:,.2f}".format(equity_data['cost_value'])
               concentration_formatted = "{:.2f}%".format(equity_data['concentration'])

               pf_data.append({
                    'Ticker': ticker,
                    'Market Price': market_price_formatted,
                    'Market Value' : market_value_formatted,
                    'Concentration': concentration_formatted,
                    'Cost Value': cost_value_formatted
               })
          columns = ['Ticker', 'Market Price', 'Market Value', 'Concentration', 'Cost Value']
          df = pd.DataFrame(pf_data, columns = columns)
          st.table(df)

    if st.button("Concentration Pie Chart", help="Portfolio Pie chart"):
          pf_data = []
          for ticker in ticker_list:
               equity_data = db.get_equity_data(ticker)
               concentration = equity_data['concentration']
               pf_data.append({
                    'Ticker': ticker,
                    'Concentration': concentration
               })

          df = pd.DataFrame(pf_data)
          fig = px.pie(df, values='Concentration', names='Ticker', title='Concentration by Ticker')
          st.plotly_chart(fig)


    if st.button("Show P&L", help="Portfolio data chart"):
          pf_data = []
          for ticker in ticker_list:
               equity_data = db.get_equity_data(ticker)
               market_value = equity_data['market_value']
               cost_value = equity_data['cost_value']
               profit_loss = market_value - cost_value

               pf_data.append({
                    'Ticker': ticker,
                    'Market Value': market_value,
                    'Cost Value': cost_value,
                    'Profit/Loss': profit_loss
               })

          df = pd.DataFrame(pf_data)
          fig = px.bar(df, x = 'Ticker', y = ['Cost Value','Market Value'],
                         title = 'Portfolio P&L',
                         labels = {'value': 'Value'},
                         hover_name = 'Ticker', barmode='group')
          fig.update_layout(legend=dict(title="Legend"))


          fig.update_traces(customdata=df['Profit/Loss'].map('${:,.2f}'.format), hovertemplate='%{y:$,.2f} Profit/Loss: %{customdata}')
          st.plotly_chart(fig)
     




##########################################################

with st.container():
    st.markdown('<div class="section"><h2>Simple Chart</h2></div>', unsafe_allow_html=True)
    ticker_symbol = st.text_input("Enter a ticker symbol")
    selected_period = st.selectbox("Select period", ["1d","5d","1mo","3mo","6mo","1y"])
    period_names = { 
          "1d": "1 day",
          "5d": "5 days",
          "1mo":"1 month",
          "3mo": "3 months",
          "6mo": "6 months",
          "1y": "1 year"
     }
    formatted_Df = pd.DataFrame()


     ## Test Functions ##

     ##Fetch Yahoo Finance Data ##
    if st.button("Show Table"):
          try:
               tickerData = yf.Ticker(ticker_symbol)
               ticker_Df = tickerData.history(period=selected_period)

               if not ticker_Df.empty:
                         modified_Df = ticker_Df.reset_index()
                         modified_Df['Date']= modified_Df['Date'].dt.strftime('%d %b %Y')
                         modified_Df.rename(columns={'Close': 'Price (USD)'}, inplace = True)
                         modified_Df['Price (USD)'] = modified_Df['Price (USD)'].apply(lambda x: f"${x:.2f}")
                         formatted_Df = modified_Df[['Date','Price (USD)']]
                         st.table(formatted_Df)
               else:
                    st.warning("Invalid Symbol, try again")

          except Exception as e:
               st.error(f"An error occurred: {e}")

     ## Generate Chart ##
    if st.button ("Generate Chart"):
          try:
               tickerData = yf.Ticker(ticker_symbol)
               ticker_Df = tickerData.history(period=selected_period)
               full_period_name = period_names.get(selected_period, selected_period)
               title = f'{ticker_symbol} Price History for Last {full_period_name}'
               if not ticker_Df.empty:
                         modified_Df = ticker_Df.reset_index()
                         modified_Df['Date']= modified_Df['Date'].dt.strftime('%d %b %Y')
                         modified_Df.rename(columns={'Close': 'Price (USD)'}, inplace = True)
                         modified_Df['Price (USD)'] = modified_Df['Price (USD)'].apply(lambda x: f"${x:.2f}")
                         formatted_Df = modified_Df[['Date','Price (USD)']]
                         fig = px.line(formatted_Df, x = 'Date', y= 'Price (USD)', title = title)
                         fig.update_xaxes(tickangle=45)

                         st.plotly_chart(fig)
               else:
                    st.warning("Error")
          except Exception as e:
               st.error(f"An error occurred: {e}")
          
         