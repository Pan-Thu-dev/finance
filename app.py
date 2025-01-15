from decimal import Decimal
from flask import render_template, request, redirect, session
import requests
from flask import Flask, render_template, request, session, redirect
import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


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
    """Show portfolio of stocks"""

    try:
        # Fetch user's shares grouped by symbol
        portfolio = db.execute(
            "SELECT symbol, COUNT(symbol) AS share_count FROM shares WHERE user_id = ? GROUP BY symbol",
            session["user_id"]
        )

        total_balance = 0

        for share in portfolio:
            stock_data = lookup(share["symbol"])
            if stock_data is None:
                continue
            share["symbol"] = share["symbol"].upper()
            share["price"] = usd(stock_data["price"])
            share["total"] = usd(stock_data["price"] * share["share_count"])
            total_balance += stock_data["price"] * share["share_count"]

        # Fetch user's cash balance
        current_balance = db.execute(
            "SELECT cash FROM users WHERE id = ?", session["user_id"]
        )[0]["cash"]

        total_balance += current_balance

        return render_template("index.html", portfolio=portfolio, cash=usd(current_balance), total=usd(total_balance))

    except Exception as e:
        print(f"Error: {e}")
        return apology("An error occurred while retrieving your portfolio.")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":
        # Retrieve and validate form inputs
        symbol = request.form.get("symbol").lower()
        try:
            shares = int(request.form.get("shares"))
        except ValueError:
            return apology("Invalid shares")

        if not symbol:
            return apology("missing symbol")
        if shares <= 0:
            return apology("invalid number of shares")

        # Look up stock data
        stock_data = lookup(symbol)
        if stock_data is None:
            return apology("invalid symbol")

        # Check current balance
        try:
            current_balance = db.execute(
                "SELECT cash FROM users WHERE id = ?", session["user_id"]
            )[0]["cash"]
        except IndexError:
            return apology("User not found.")

        # Calculate total cost and check if user can afford
        total_cost = stock_data["price"] * shares
        if current_balance < total_cost:
            return apology("insufficient funds")

        # Deduct total cost from user's cash
        db.execute(
            "UPDATE users SET cash = ? WHERE id = ?",
            current_balance - total_cost,
            session["user_id"]
        )

        # Log transaction in history table
        db.execute(
            "INSERT INTO history (user_id, symbol, price, share_count, time, purchased) VALUES (?, ?, ?, ?, ?, ?)",
            session["user_id"],
            symbol,
            stock_data["price"],
            shares,
            datetime.now(),
            1  # 1 indicates purchase
        )

        # Add shares to the user's portfolio
        for _ in range(shares):
            db.execute(
                "INSERT INTO shares (user_id, symbol) VALUES (?, ?)",
                session["user_id"],
                symbol
            )

        return redirect("/")

    # Render the buy form for GET request
    return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    try:
        # Retrieve transaction history from the database
        history = db.execute(
            "SELECT symbol, price, share_count, time FROM history WHERE user_id = ?",
            session["user_id"]
        )

        # Check if the user has any transaction history
        if not history:
            return apology("No transaction history found.")

        # Format each transaction in the history
        for transaction in history:
            transaction["symbol"] = transaction["symbol"].upper()
            transaction["price"] = usd(float(transaction["price"]))

    except Exception as e:
        # Handle any errors that occur during the database query
        print(f"Error retrieving history: {e}")
        return apology("An error occurred while retrieving transaction history.")

    # Render the template with the retrieved transaction history
    return render_template("history.html", history=history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    if request.method == "POST":
        # Ensure username and password were provided
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return apology("must provide username")
        elif not password:
            return apology("must provide password")

        # Query database for user
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure user exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("invalid username and/or password")

        # Remember the user ID in session
        session["user_id"] = rows[0]["id"]

        # Redirect to home page
        return redirect("/")

    # If GET request, render the login form
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
        # Get the symbol input from the form
        symbol = request.form.get("symbol")

        # Ensure the symbol is provided
        if not symbol:
            return apology("missing symbol")

        try:
            # Look up the stock data for the given symbol
            stock_data = lookup(symbol)

            # If no stock data is returned, raise an exception
            if stock_data is None:
                raise ValueError("Invalid symbol")

            # Format the price and render the quote page
            stock_data["price"] = usd(stock_data["price"])
            return render_template("quoted.html", quote=stock_data)

        except (ValueError, TypeError):
            return apology("invalid symbol")

    # Render the quote form if it's a GET request
    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        username = request.form.get("username")
        if not username:
            return apology("must provide username")

        # Ensure password was submitted
        password = request.form.get("password")
        if not password:
            return apology("must provide password")

        # Ensure password was confirmed
        confirmation = request.form.get("confirmation")
        if password != confirmation:
            return apology("password and confirm password must be the same")

        # Check if the username already exists in the database
        existing_user = db.execute(
            "SELECT * FROM users WHERE username = ?", username
        )
        if len(existing_user) > 0:
            return apology("Username already exists")

        # Insert the new user into the database
        db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)",
            username,
            generate_password_hash(password)
        )

        # Remember which user has logged in
        session["user_id"] = db.execute(
            "SELECT id FROM users WHERE username = ?", username
        )[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    if request.method == "POST":
        # Retrieve form data
        symbol = request.form.get("symbol").lower()
        try:
            shares = int(request.form.get("shares"))
        except ValueError:
            return apology("Invalid shares")

        if not symbol:
            return apology("missing symbol")
        if shares <= 0:
            return apology("invalid number of shares")

        # Change shares to integer
        shares = int(shares)
        if shares <= 0:
            return apology("invalid number of shares")

        # Fetch the total number of shares the user owns for the given symbol
        owned_shares = db.execute(
            "SELECT COUNT(symbol) AS count FROM shares WHERE user_id = ? AND symbol = ?",
            session["user_id"],
            symbol
        )[0]["count"]

        # Check if user has enough shares to sell
        if owned_shares < shares:
            return apology("not enough shares")

        # Delete the specified number of shares
        db.execute(
            "DELETE FROM shares WHERE user_id = ? AND symbol = ? LIMIT ?",
            session["user_id"],
            symbol,
            shares
        )

        # Lookup current stock price
        stock_data = lookup(symbol)
        if not stock_data:
            return apology("invalid symbol")

        # Calculate new balance after selling
        current_balance = db.execute(
            "SELECT cash FROM users WHERE id = ?", session["user_id"]
        )[0]["cash"]

        total_price = stock_data["price"] * shares

        # Update user's cash balance
        db.execute(
            "UPDATE users SET cash = ? WHERE id = ?",
            current_balance + total_price,
            session["user_id"]
        )

        # Log the transaction in history (as a sale)
        db.execute(
            "INSERT INTO history (user_id, symbol, price, share_count, time, purchased) VALUES (?, ?, ?, ?, ?, ?)",
            session["user_id"],
            symbol,
            stock_data["price"],
            -shares,  # Negative shares for sale
            datetime.now(),
            0  # 0 indicates a sale
        )

        return redirect("/")

    # If GET request, render the sell form with available symbols
    else:
        symbols = db.execute(
            "SELECT DISTINCT symbol FROM shares WHERE user_id = ?",
            session["user_id"]
        )

        # Convert each symbol to uppercase
        for symbol in symbols:
            symbol["symbol"] = symbol["symbol"].upper()

        return render_template("sell.html", symbols=symbols)


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """Change Password"""

    if request.method == "POST":
        # Get form data
        current_password = request.form.get("current-password")
        new_password = request.form.get("new-password")
        confirmation = request.form.get("confirmation")

        # Validate form inputs
        if not current_password:
            return apology("must provide current password")
        if not new_password:
            return apology("must provide new password")
        if not confirmation:
            return apology("must confirm new password")

        # Retrieve the current password hash from the database
        try:
            old_password = db.execute(
                "SELECT hash FROM users WHERE id = ?",
                session["user_id"]
            )[0]
        except IndexError:
            return apology("user not found")

        # Verify current password
        if not check_password_hash(old_password["hash"], current_password):
            return apology("incorrect current password")

        # Ensure new password matches confirmation
        if new_password != confirmation:
            return apology("password and confirmation must match")

        # Check if the new password is different from the current one
        if new_password == current_password:
            return apology("new password cannot be the same as the current password")

        # Update with the new password hash
        db.execute(
            "UPDATE users SET hash = ? WHERE id = ?",
            generate_password_hash(new_password),
            session["user_id"]
        )

        # Clear session to log out the user and redirect to login page
        session.clear()
        # Redirect to login page after changing the password
        return redirect("/login")

    # If GET request, render the password change form
    return render_template("change-password.html")


@app.route("/loan", methods=["GET", "POST"])
@login_required
def loan():
    """Ask for a Loan"""

    if request.method == "POST":
        # Get loan amount and validate
        try:
            loan_amount = float(request.form.get("loan"))
        except (TypeError, ValueError):
            # Handle invalid input (non-numeric)
            return apology("Invalid loan amount")

        # Ensure loan is within acceptable range
        if loan_amount <= 0 or loan_amount > 10000:
            return apology("Loan must be between $1 and $10,000")

        # Retrieve the user's current balance
        try:
            current_balance = db.execute(
                "SELECT cash FROM users WHERE id = ?",
                session["user_id"]
            )[0]["cash"]
        except IndexError:
            # Handle missing user in case of database issues
            return apology("User not found")

        # Calculate new balance after loan
        new_balance = current_balance + loan_amount

        # Update the user's cash balance in the database
        db.execute(
            "UPDATE users SET cash = ? WHERE id = ?",
            new_balance,
            session["user_id"]
        )

        # Redirect user to the homepage after successful loan update
        return redirect("/")

    # If GET request, render the loan form
    return render_template("loan.html")
