TLDR: Interactive backtesting framework for trading strategies using Streamlit, Backtrader, and Yahoo Finance. Implements Luca's Strategy with data caching, moving averages, and crossover techniques for actionable insights.

# Luca's Backtesting Strategy  

This repository contains the implementation of **Luca's Strategy**, a backtesting framework designed to evaluate trading strategies using historical stock data. The application is built with **Streamlit** for an interactive user interface, **Backtrader** for simulation and strategy development, and **Yahoo Finance** for data retrieval. The repository demonstrates how to integrate data caching, moving averages, and a crossover strategy to provide actionable insights for trading decisions.  

## File Overview  

### `firo_ui.py`  
This file acts as the user interface and core logic of the system, enabling users to:  
- Select a portfolio of stocks.  
- Define backtesting parameters, such as duration, budget, and take-profit percentage.  
- Visualize stock performance and backtesting results.  
- Execute *Luca's Strategy*, a custom trading strategy built on moving average crossovers, with configurable parameters like take-profit levels.  

### `requirements.txt`  
This file contains the list of dependencies required to run the application.  

## About Luca's Strategy  

The strategy utilizes a combination of moving averages (7-day, 14-day, and 38-day) and crossovers to identify optimal buy and sell signals.  
- **Buy Signal**: Triggered when a short-term moving average crosses above a longer-term moving average, indicating an uptrend.  
- **Sell Signal**: Positions are exited upon reaching the defined take-profit percentage.  

The logic is implemented within a Backtrader-compatible strategy class, `TestStrategy`.  

## How to Run the Application  

1. Install the required dependencies listed in `requirements.txt`:  
   ```bash
   pip install -r requirements.txt
