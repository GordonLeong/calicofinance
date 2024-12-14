### Import libraries###
import firebase_admin
import pyrebase
from firebase_admin import credentials, firestore
import yfinance as yf
from datetime import datetime


## user authentication ##
firebaseConfig= {
  'apiKey': "AIzaSyDRw_gTfwFpPzJLv0QDXS7Y7kXwuA5fdY8",
  'authDomain': "finance-app-69eb2.firebaseapp.com",
  'projectId': "finance-app-69eb2",
  'storageBucket': "finance-app-69eb2.appspot.com",
  'messagingSenderId': "522135228658",
  'appId': "1:522135228658:web:d7c4353d2696424b66c06b",
  'databaseURL':"https://dummy.firebaseio.com",
  'measurementId':"G-YEMSC6ZES7"
  }

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

### database interaction ##
try:
    firebase_admin.get_app()
except ValueError:
    cred = credentials.Certificate("/Users/taeyeonist/Documents/Coding Projects/finance-app/firestore-key.json")
    firebase_admin.initialize_app(cred)


db = firestore.client()

def add_transaction(ticker, txn_type, qty, cost_price, txn_date):
    equity_ref = db.collection('equities').document(ticker)
    txn = {
        'txn_type': txn_type,
        'qty': qty,
        'cost_price': cost_price,
        'txn_date': txn_date
    }
    equity_ref.collection('transactions').add(txn)


def update_ticker(ticker, txn_type, qty, cost_price):
    ticker_ref = db.collection('equities').document(ticker)
    ticker_snapshot = ticker_ref.get()

    if ticker_snapshot.exists:
        current_data = ticker_snapshot.to_dict()
        current_qty = current_data.get('qty_held',0)
        current_cost = current_data.get('avg_cost',0)

    #calculate the new qty and cost
        if txn_type == 'Buy':
            new_qty = current_qty + qty
            new_cost = calculate_average(current_cost, current_qty, qty, cost_price)
        
        elif txn_type == 'Sell':
            new_qty = current_qty - qty
            new_cost = current_cost

            if new_qty <= 0:
                new_qty = 0
                new_cost = 0

        ticker_ref.update({
            'qty_held': new_qty,
            'avg_cost': new_cost
        })
    else:
        if txn_type == 'Buy':
            new_qty = qty
            new_cost = cost_price

            ticker_ref.set({
                'qty_held': new_qty,
                'avg_cost': new_cost
                    })
            return True, "Success"
        
        elif txn_type == 'Sell':
        
            return False, f"Unable to sell {qty} of {ticker}"

##helper function to calculate weighted average cost ##

def calculate_average(prev_avg, prev_qty, qty, cost_price):
    return (prev_avg * prev_qty + qty * cost_price)/(prev_qty + qty)


##bulk upload function ##
def bulk_upload_transactions(df):
    df = df.dropna(subset=['Ticker', 'TransactionType', 'Quantity', 'CostPrice', 'TransactionDate'])
    batch = db.batch()
    ticker_updates = {}

    for index, row in df.iterrows():
        #extracting transaction data from each row
        ticker = row['Ticker']
        print("Ticker:", ticker, "Type:", type(ticker))
        txn_type = row['TransactionType']
        print("TransactionType:", txn_type, "Type:", type(txn_type))
        qty = row['Quantity']
        print("qty:", qty, "Type:", type(qty))
        cost_price = row['CostPrice']
        print("price:", cost_price, "Type:", type(cost_price))
        txn_date = str(row['TransactionDate'])
        print("txn_date:", txn_date, "Type:", type(txn_date))

        #reference to the current ticker's document
        ticker_ref = db.collection('equities').document(ticker)

        if ticker not in ticker_updates:
            ticker_updates[ticker] = {'avg_cost':0, 'qty_held':0}


        if 'fetched' not in ticker_updates[ticker]:
        #fetch current stats for the ticker
            ticker_doc = ticker_ref.get()
            if ticker_doc.exists:
                current_stats = ticker_doc.to_dict()
                prev_avg = current_stats.get('avg_cost',0)
                prev_qty = current_stats.get('qty_held',0)
            ticker_updates[ticker]['fetched'] = True
        
        #Process transaction and update ticker stats
        prev_avg = ticker_updates[ticker]['avg_cost']
        prev_qty = ticker_updates[ticker]['qty_held']


        ## Calculate the new average and new qty based on the transaction type
        if txn_type.lower() == 'buy':
            new_qty = prev_qty + qty
            new_avg = calculate_average(prev_avg, prev_qty, qty, cost_price)
            ticker_updates[ticker].update({'avg_cost':new_avg,'qty_held': new_qty})
        
        elif txn_type.lower() == 'sell':
            new_qty = max(prev_qty - qty, 0)  # ensure quantity does not turn negative
            ticker_updates[ticker].update({'qty_held': new_qty})

        transaction_data ={
            'txn_date': txn_date,
            'cost_price': cost_price,
            'qty': qty,
            'txn_type': txn_type,
            #'ticker': ticker
        }

        transaction_ref = ticker_ref.collection('transactions').document()
        batch.set(transaction_ref, transaction_data)
    batch.commit()

    #Update ticker document with new stats
    for ticker, updates in ticker_updates.items():
        ticker_ref = db.collection('equities').document(ticker)
        ticker_ref.set({'avg_cost': updates['avg_cost'],'qty_held':updates['qty_held']}, merge = True)







####
def get_all_transactions():
    equities_ref = db.collection('equities')
    equities = equities_ref.get()

    all_transactions = []
    for equity in equities:
        transactions_ref = equities_ref.document(equity.id).collection('transactions')
        transactions = transactions_ref.get()
        for transaction in transactions:
            transaction_data = transaction.to_dict()
            transaction_data['ticker'] = equity.id
            all_transactions.append(transaction_data)
    
    return all_transactions


def get_ticker_list():
    equities_ref = db.collection('equities')
    equities = equities_ref.get()
    tickers = [equity.id for equity in equities]
    return tickers


def update_market_prices(ticker_list):
    try:
        for ticker in ticker_list:
            print(ticker_list)
            ticker_data = yf.Ticker(ticker)
            latest_data = ticker_data.history(period="1d")
            if not latest_data.empty:
                latest_price = latest_data['Close'].iloc[0]
                current_date = datetime.now().date().strftime("%Y-%m-%d")
                update_date = firestore.SERVER_TIMESTAMP
                equity_ref = db.collection('equities').document(ticker)
                equity_ref.update({
                    'market_price': latest_price,
                    'updated_at': update_date
                })

                qty = equity_ref.get().to_dict().get('qty_held')
                if qty is not None:
                    market_value = latest_price * qty
                    equity_ref.update({
                        'market_value': market_value
                    })

        portfolio_ref = db.collection('portfolio').document('update_date')
        portfolio_ref.set({'portfolio_update_date': current_date}, merge = True)


        return True



    except Exception as e:
        print(f"Error updating market prices: {str(e)}")
        return False

def get_portfolio_update_date():
     portfolio_ref = db.collection('portfolio').document('update_date')
     portfolio_data = portfolio_ref.get().to_dict()
     portfolio_update_date = portfolio_data.get('portfolio_update_date')
     return portfolio_update_date

def get_equity_data(ticker):
    try:
        equity_ref = db.collection('equities').document(ticker)
        equity_data = equity_ref.get().to_dict()

        if equity_data:
            return equity_data
        else:
            return None
    except Exception as e:
        print(f"Error getting equity data for {ticker}: {str(e)}")
        return None
    

def get_transactions_for_tickers(ticker_list, start_date, end_date):
    all_transactions = []
    collection_ref = db.collection('equities')
    # if tickers were not selected, fetch all tickers
    if not ticker_list:
        ticker_list = get_ticker_list() #fetch all tickers from Firestore

    for ticker in ticker_list:
        #loop over each ticker in the ticker_list and pull the transactions in the associated subcollection
        transactions_ref = collection_ref.document(ticker).collection('transactions')
        #build the firestore query
        query = transactions_ref
        #if selected, add date filters to the query
        if start_date and end_date:
            query = query.where('txn_date', '>=', start_date.strftime("%Y-%m-%d"))\
                         .where('txn_date', '<=', end_date.strftime("%Y-%m-%d"))
        #execute query
        transactions = query.get()
        for transaction in transactions:
            transaction_data = transaction.to_dict()
            transaction_data['ticker'] = ticker #add the ticker name
            all_transactions.append(transaction_data)

    return all_transactions






    # for ticker in ticker_list:
    #     transactions_ref = db.collection('equities').document(ticker).collection('transactions')
    #     transactions = transactions_ref.where('txn_date', '>=', start_date.strftime("%Y-%m-%d"))\
    #         .where('txn_date','<=', end_date.strftime("%Y-%m-%d")).get()
    #     for transaction in transactions:
    #         transaction_data = transaction.to_dict()
    #         transaction_data['ticker'] = ticker
    #         all_transactions.append(transaction_data)

    # return all_transactions
    
                            