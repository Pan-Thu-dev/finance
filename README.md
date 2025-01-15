# Stock Trading Simulation Platform 📈

A Flask-based web application for simulating stock trading, allowing users to buy and sell shares, view transaction history, and manage their portfolio. The app also features secure user authentication, loan requests, and real-time stock price retrieval.

---

## 🌟 Features

### Core Functionalities
- **Portfolio Management**: View current stocks, their market prices, and total portfolio value.
- **Buy and Sell Stocks**: Simulate buying and selling shares with real-time stock prices.
- **Transaction History**: Track all transactions, including purchases and sales.

### User Management
- **User Authentication**: Secure registration and login system using hashed passwords.
- **Password Change**: Update user passwords securely.

### Additional Utilities
- **Loan Requests**: Request loans to increase the cash balance.
- **Real-Time Quotes**: Fetch real-time stock prices using the [Finance API](https://finance.cs50.io/).

---

## 🛠️ Technology Stack

- **Backend**: Flask, CS50 Library
- **Frontend**: Jinja2 templates for dynamic web pages
- **Database**: SQLite
- **APIs**: Finance API for stock data
- **Session Management**: Flask-Session for secure session handling

---

## ⚙️ Setup and Installation

### Prerequisites
- Python 3.x installed on your system.
- Required Python packages listed in `requirements.txt`.

### Installation Steps

1. Clone the repository:
  ```
  git clone https://github.com/your-username/your-repository.git
  ```
2. Navigate to the project directory:
  ```
  cd your-repository
  ```
3. Install dependencies:
  ```
  pip install -r requirements.txt
  ```
4. Start the application:
  ```
  flask run
  ```
  Access the application at http://127.0.0.1:5000.

📂 Project Structure

    app.py: Main application logic and routes.
    helpers.py: Utility functions for common operations.
    requirements.txt: Python package dependencies.
    templates/: HTML templates for the application.
    static/: Static files like CSS and JavaScript.

📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
