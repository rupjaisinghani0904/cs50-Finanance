# cs50-Finanance
A finance webapp that allows you to buy and sell shares of stock.

Implemented a website via which users can "buy" and "sell" stocks, a la the below. C$50 Finance Background

A web app via which you can manage portfolios of stocks. Not only will this tool allow you to check real stocks' actual prices and portfolios' values, it will also let you buy (okay, "buy") and sell (okay, "sell") stocks by querying IEX for stocks' prices.

Let’s turn our attention now to the app’s distribution code! Distribution Downloading

$ wget http://cdn.cs50.net/2018/x/psets/7/finance/finance.zip $ unzip finance.zip $ rm finance.zip $ cd finance $ ls application.py helpers.py static/ finance.db requirements.txt templates/

Running

Start Flask’s built-in web server (within finance/):

flask run

Visit the URL outputted by flask to see the distribution code in action. You won’t be able to log in or register, though, just yet!

Uses SQL database to store log-in and user balance.
