import os
import hashlib
import pickle
import backtrader as bt
import backtrader.indicators as btind
import yfinance as yf
import datetime as dt
import math
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Function to simulate backtesting
def run_backtesting(portfolio, duration, budget):
    st.write("### Backtesting Results")
    st.write(f"Portfolio: {', '.join(portfolio)}")
    st.write(f"Duration: {duration} years")
    st.write(f"Budget by stock: ${budget:,.2f}")

    # Simulate charts for each stock
    for stock in portfolio:
        fig, ax = plt.subplots()
        ax.plot(range(10), [i * duration for i in range(10)], label=f"Performance of {stock}")
        ax.set_title(f"Chart for {stock}")
        ax.legend()
        st.pyplot(fig)

# Main layout
st.set_page_config(page_title="Luca's Strategy Backtesting")

# Titolo Centrale
st.title("Welcome to the Luca's Strategy Backtesting")

# Sidebar panel
st.sidebar.header("Backtest Parameters")

# Funzione per caricare i ticker da file CSV in una cartella
@st.cache_data
def load_tickers_from_folder(folder_path):
    ticker_list = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(folder_path, filename)
            try:
                data = pd.read_csv(file_path)
                if "Ticker" in data.columns:
                    ticker_list.extend(data["Ticker"].dropna().tolist())
            except Exception as e:
                st.error(f"Error loading file {filename}: {e}")
    return sorted(set(ticker_list))  # Rimuove duplicati e ordina i ticker

# Specifica il percorso della cartella con i file CSV
tickers_folder = "tickers"

# Carica tutti i ticker
all_tickers = load_tickers_from_folder(tickers_folder)

# Selezione multiselect nel sidebar
portfolio = st.sidebar.multiselect(
    "Select portfolio stocks:",
    options=all_tickers,
    default=all_tickers[:2]  # Seleziona i primi 5 come default (opzionale)
)

# Parameter 2: Duration
duration = st.sidebar.slider("Select duration (years):", min_value=-10, max_value=-1, value=-2)

# Parameter 3: Budget
budget = st.sidebar.number_input(
    "Enter total budget:",
    min_value=0.0, value=1000.0, step=100.0, format="%.2f"
)

# Parameter 4: Take profit
take_profit_percent = st.sidebar.slider(
    "Select Take Profit (%)",
    min_value=1,
    max_value=100,
    value=20,  # Valore di default
    step=1
)

# --- firo start backtrader ---
#
# Get Date from Yahoo Finance
def get_data_from_yahoo(stock, days):
    print(f"Scaricamento dei dati direttamente da Yahoo per {stock} nei passati {days} giorni...")
    start_date = dt.datetime.now() - dt.timedelta(days=days)
    end_date = dt.datetime.now()
    
    # Fetch data from Yahoo Finance
    # df = yf.download(stock, start=start_date, end=end_date)
    df = fetch_data_with_cache(stock, start_date, end_date, cache_dir="cache")

    # Check if the DataFrame is empty
    if df.empty:
        raise ValueError(f"No data found for ticker {stock} between {start_date} and {end_date}")

    # Flatten multi-level columns by dropping the 'Ticker' level
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)  # Remove the second level (Ticker)

    # Reset the index and rename 'Date' to 'datetime'
    df.reset_index(inplace=True)
    df.rename(columns={'Date': 'datetime'}, inplace=True)
    df['datetime'] = pd.to_datetime(df['datetime'])  # Ensure datetime format is correct

    # Set 'datetime' as the index
    df.set_index('datetime', inplace=True)

    # Convert to Backtrader data format
    data = bt.feeds.PandasData(
        dataname=df,
        datetime=None,  # Backtrader will automatically pick the index as datetime
        open='Open',
        high='High',
        low='Low',
        close='Close',
        volume='Volume',
        openinterest=None  # No open interest
    )
    return data

# Cache managment by stock and dates
def fetch_data_with_cache(stock, start_date, end_date, cache_dir="cache"):
    # Converti le date in stringhe e prendi solo la parte della data (prima dell'orario)
    start_date_str = str(start_date).split(' ')[0]  # Solo la data, senza orario
    end_date_str = str(end_date).split(' ')[0]  # Solo la data, senza orario

    # Genera una chiave unica per la cache basata sui parametri
    cache_key = f"{stock}_{start_date_str}_{end_date_str}"
    # print(f"Cache key: {cache_key}")  # Aggiunto per il debug

    # Crea un percorso univoco per il file di cache usando l'hash MD5 della chiave
    cache_file = os.path.join(cache_dir, hashlib.md5(cache_key.encode()).hexdigest() + ".pkl")

    # print(f"Cache file path: {cache_file}")  # Aggiunto per il debug

    # Verifica se il file di cache esiste
    if os.path.exists(cache_file):
        # print(f"Cache found for {stock} ({start_date_str} to {end_date_str}), loading data...")
        with open(cache_file, "rb") as f:
            return pickle.load(f)

    # Altrimenti, scarica i dati da Yahoo Finance
    # print(f"Fetching data from Yahoo Finance for {stock} ({start_date_str} to {end_date_str})")
    df = yf.download(stock, start=start_date, end=end_date)

    # Salva i dati nella cache
    with open(cache_file, "wb") as f:
        pickle.dump(df, f)

    return df

# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ("take_profit_percent", 20),  # Percentuale di profitto (default 20% secondo Luca)
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        # print('%s, %s' % (dt.isoformat(), txt))
        # st.write('%s, %s' % (dt.isoformat(), txt))
        self.logs = pd.concat([self.logs, pd.DataFrame({"Date": [dt.isoformat()], "Log": [txt]})], ignore_index=True)

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # Initialize DataFrame to collect logs
        self.logs = pd.DataFrame(columns=["Date", "Log"])

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        self.ma7 = btind.SMA(self.data.close, period=7, plotname='7-day MA')
        self.ma14 = btind.SMA(self.data.close, period=14, plotname='14-day MA')
        self.ma38 = btind.SMA(self.data.close, period=38, plotname='38-day MA')
        
        self.crossover = btind.CrossOver(self.ma7, self.ma14, self.ma38)
        self.take_profit_percent = take_profit_percent

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Share: %.2f, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.size,
                     order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Share: %.2f, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.size,
                          order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            
            # IF SMA crossed go for BUY
            if (self.crossover < 0):

                # BUY, BUY, BUY!!! (with default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Calucalte ORDERE dimension
                dollars_to_invest = self.broker.cash
                self.size = math.floor(dollars_to_invest / self.data.close[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy(size=self.size)

        else:

            # Already in the market ... we might sell
            #if (self.crossover < 0):
            
            if self.dataclose[0] >= (self.buyprice * ((1 + (self.take_profit_percent/100)))):

                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell(size=self.size)

# Run Testing Simulation
def run_backtrading(stock, days, budget, take_profit_percent):

    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    # cerebro.addstrategy(TestStrategy)
    cerebro.addstrategy(TestStrategy, take_profit_percent=take_profit_percent)

    # Add the Data Feed to Cerebro
    cerebro.adddata(get_data_from_yahoo(stock, days))

    # Set our desired cash start
    cerebro.broker.setcash(budget)

    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.005)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # st.write('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    strategies = cerebro.run()
    test_strategy_instance = strategies[0]

    # Retrieve strategy logs
    logs = test_strategy_instance.logs

    # Print out the final result
    print('---> Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # st.write('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    return cerebro.broker.getvalue(), logs

# Run (call from __main__ or extrnal UI)
def run(stocks, years, budget_stock, take_profit_percent):
    days = -years * 365
    tabs = st.tabs(portfolio)
    #for stock in stocks:
    data_chart = []
    for i, stock in enumerate(stocks):
        with tabs[i]:
            # print(f"Running backtesting for: {stock}")
            # st.write(f"Running backtesting for: **{stock}**")
            #st.markdown(f"Running backtesting for: **{stock}**")
            #with st.expander(f"See backtesting details for {stock}"):
            final_budget, logs = run_backtrading(stock, days, budget_stock, take_profit_percent)
            profit_loss = final_budget - budget
            perc_profit_loss = profit_loss / budget*100
            st.markdown(f"Completed backtesting with Initial Portfolio Value **{budget:.2f}** Final Portfolio Value **{final_budget:.2f}** and Profit/Loss **{profit_loss:.2f}** (**{perc_profit_loss:.2f}%**)")
            st.dataframe(logs, use_container_width=True)
            #print(f"Completed backtesting for: {stock} with Profit/Loss {profit_loss:.2f} \n")
            # st.divider()
            data_chart.append({'stock': stock, 'profit_loss': profit_loss})
    df = pd.DataFrame(data_chart)
    df.set_index('stock', inplace=True) 
    st.bar_chart(df['profit_loss'])
    return profit_loss
# -- firo end backtrader ---

# Automatically run backtesting when parameters change
if portfolio and budget > 0:
    run(portfolio, duration, budget, take_profit_percent)
