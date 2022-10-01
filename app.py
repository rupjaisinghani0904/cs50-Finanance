import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    user_id = session["user_id"]
    stocks = db.execute("SELECT symbol, name, price, SUM(shares) as total_shares FROM transactions WHERE user_id = ? GROUP BY name", user_id)
    balance = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]

    total = balance

    for stock in stocks:
        total += stock["price"] * stock["total_shares"]

    return render_template("index.html", stocks=stocks, balance=balance, usd=usd, total=total)



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("input is blank")

        symbol = request.form.get("symbol").upper()
        stock = lookup(symbol)
        shares = request.form.get("shares")

        if not stock:
            return apology("stock not found")

        if not shares.isdigit():
            return apology("you cannot buy partial shares")

        if int(shares) < 1:
            return apology("invalid number of shares")

        user_id = session["user_id"]
        stock_price = stock["price"]
        balance = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]
        stock_name = stock["name"]
        total_price = int(shares) * stock_price

        if balance < total_price:
            return apology("insufficient balance")

        db.execute("UPDATE users SET cash = ? WHERE id = ?", balance - total_price, user_id)
        db.execute("INSERT INTO transactions (user_id, name, shares, price, type, symbol) values (?, ?, ?, ?, ?, ?)",
        user_id, stock_name, int(shares), stock_price, 'buy', symbol)

        return redirect('/')
    else:
        return render_template("buy.html")



@app.route("/history")
@login_required
def history():
    user_id = session["user_id"]
    transactions = db.execute("SELECT symbol, shares, price, type, time FROM transactions WHERE user_id = ?", user_id)
    return render_template("history.html", usd=usd, transactions=transactions)




@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        stock = lookup(symbol)

        if not stock:
            return apology("stock not found")

        return render_template('quoted.html', stock=stock, usd=usd)

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if not request.form.get("username"):
            return apology("invalid username")

        if len(rows) != 0:
            return apology("username taken")

        elif not request.form.get("password") or not request.form.get("confirmation"):
            return apology("password can't be empty")

        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("passwords must match")

        register = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)",
        username = request.form.get("username"), hash = generate_password_hash(request.form.get("password")))

        session["user_id"] = register

        return redirect("/")

    else:
        return render_template("register.html")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    user_id = session["user_id"]
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))
        stock_name = lookup(symbol)["name"]


        if shares < 1:
            return apology("invalid number of shares inputed")

        shares_owned = db.execute("SELECT SUM(shares) as shares FROM transactions WHERE user_id = ? AND name = ?", user_id, stock_name)[0]["shares"]
        if shares > shares_owned:
            return apology("you don't have sufficient shares")

        stock_price = lookup(symbol)["price"]
        balance = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]
        db.execute("UPDATE users SET cash = ? WHERE id = ?", balance + stock_price * shares, user_id)
        db.execute("INSERT INTO transactions (user_id, name, shares, price, type, symbol) values (?, ?, ?, ?, ?, ?)",
        user_id, stock_name, -shares, stock_price, 'sell', symbol)

        return redirect('/')

    else:
        symbols = db.execute("SELECT symbol FROM transactions WHERE user_id = ? GROUP BY symbol", user_id)
        return render_template("sell.html", symbols=symbols)



@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    if request.method == "POST":
        user_id = session["user_id"]
        rows = db.execute("SELECT * FROM users WHERE id = ?", user_id)

        if not check_password_hash(rows[0]["hash"], request.form.get("old_password")):
            return apology("current password is incorrect")

        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")

        if not new_password == confirmation:
            return apology("passwords must match")

        db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(new_password), user_id)

        return redirect("/")

    else:
        return render_template("password.html")