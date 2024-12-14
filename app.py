## import libraries ##
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px

### UI Setup##
st.set_page_config(
     page_title="Calico Investor",
     page_icon=":money_with_wings:"
)
st.title('Calico 🐱 Investor App')
st.header('Welcome 🐱 Investor!')

st.markdown("""
**How to use this app:**
            
The Investor App aims to replicate the functionality of the various google sheets we currently use for accountability and tracking.
            
This includes unit price calculation and saving, recording buy-ins by investors and new transactions in the portfolio. It will also cover
all of our various investment interests, not just stocks, but also crypto and options.

            
We will also share links to more detailed reports on the performance of various business interests in the app.

Stay tuned for further upgrades!      
            
            """)