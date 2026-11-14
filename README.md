
# Simple Banking System (Flask backend + HTML/CSS frontend)

A minimal but solid banking web app using **Python (Flask)** for the backend and **HTML/CSS** for the frontend.

## Features
- Register / Login / Logout
- Secure password hashing (Werkzeug)
- SQLite database (auto-created on first run)
- View balance/dashboard
- Deposit, Withdraw, Transfer to another user
- Transaction history

## Tech Stack
- Python 3.9+
- Flask, Flask-Login, Flask_SQLAlchemy
- SQLite

## Project Structure
```
banking_system_flask/
├── app.py
├── requirements.txt
├── README.md
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   ├── dashboard.html
│   ├── deposit.html
│   ├── withdraw.html
│   ├── transfer.html
│   └── transactions.html
└── static/
    └── styles.css
```

## Quick Start

1) **Create & activate a virtual environment (recommended)**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

2) **Install dependencies**
```bash
pip install -r requirements.txt
```

3) **Run the app**
```bash
python app.py
```
App runs by default at http://127.0.0.1:5000

4) **Create two users** (e.g., alice and bob) to test transfers.

### Notes
- Database file: `bank.db` (created in project root).
- If you need to reset the app, stop the server and delete `bank.db` then run again.
- This is an educational mini-project. For production: add CSRF protection, input validation libraries, better error handling, and deploy behind a real server (gunicorn/uwsgi + nginx).

Enjoy!
