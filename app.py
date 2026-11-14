
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# -----------------------
# Models
# -----------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    account = db.relationship("Account", backref="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    balance = db.Column(db.Float, default=0.0)

    transactions = db.relationship("Transaction", backref="account", cascade="all, delete-orphan", order_by="desc(Transaction.timestamp)")


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # deposit, withdraw, transfer_in, transfer_out
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    note = db.Column(db.String(255))
    counterparty = db.Column(db.String(80))  # username for transfers

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables if not exist
with app.app_context():
    db.create_all()

# -----------------------
# Helpers
# -----------------------
def commit_and_flash(message, category="success"):
    try:
        db.session.commit()
        flash(message, category)
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {e}", "danger")

# -----------------------
# Routes
# -----------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        if not username or not password:
            flash("Username and password are required.", "warning")
            return redirect(url_for('register'))
        if password != confirm:
            flash("Passwords do not match.", "warning")
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "warning")
            return redirect(url_for('register'))

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # get user.id

        account = Account(user_id=user.id, balance=0.0)
        db.session.add(account)
        commit_and_flash("Registration successful. Please log in.")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Logged in successfully.", "success")
            return redirect(url_for('dashboard'))
        flash("Invalid username or password.", "danger")
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', balance=current_user.account.balance)

@app.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount', '0'))
        except ValueError:
            amount = 0
        if amount <= 0:
            flash("Enter a positive amount.", "warning")
            return redirect(url_for('deposit'))

        acct = current_user.account
        acct.balance += amount
        txn = Transaction(account_id=acct.id, type='deposit', amount=amount, note='Cash deposit')
        db.session.add(txn)
        commit_and_flash("Deposit successful.")
        return redirect(url_for('dashboard'))
    return render_template('deposit.html')

@app.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount', '0'))
        except ValueError:
            amount = 0
        if amount <= 0:
            flash("Enter a positive amount.", "warning")
            return redirect(url_for('withdraw'))

        acct = current_user.account
        if acct.balance < amount:
            flash("Insufficient funds.", "danger")
            return redirect(url_for('withdraw'))

        acct.balance -= amount
        txn = Transaction(account_id=acct.id, type='withdraw', amount=amount, note='Cash withdrawal')
        db.session.add(txn)
        commit_and_flash("Withdrawal successful.")
        return redirect(url_for('dashboard'))
    return render_template('withdraw.html')

@app.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    if request.method == 'POST':
        to_username = request.form.get('to_username', '').strip().lower()
        try:
            amount = float(request.form.get('amount', '0'))
        except ValueError:
            amount = 0

        if not to_username or amount <= 0:
            flash("Provide a valid recipient and positive amount.", "warning")
            return redirect(url_for('transfer'))
        if to_username == current_user.username:
            flash("You cannot transfer to yourself.", "warning")
            return redirect(url_for('transfer'))

        recipient = User.query.filter_by(username=to_username).first()
        if not recipient:
            flash("Recipient not found.", "danger")
            return redirect(url_for('transfer'))

        sender_acct = current_user.account
        if sender_acct.balance < amount:
            flash("Insufficient funds.", "danger")
            return redirect(url_for('transfer'))

        # Perform transfer
        sender_acct.balance -= amount
        recipient_acct = recipient.account
        recipient_acct.balance += amount

        # Record transactions for both sides
        out_txn = Transaction(account_id=sender_acct.id, type='transfer_out', amount=amount, counterparty=recipient.username, note='Transfer sent')
        in_txn = Transaction(account_id=recipient_acct.id, type='transfer_in', amount=amount, counterparty=current_user.username, note='Transfer received')
        db.session.add(out_txn)
        db.session.add(in_txn)

        commit_and_flash("Transfer successful.")
        return redirect(url_for('dashboard'))

    return render_template('transfer.html')

@app.route('/transactions')
@login_required
def transactions():
    txns = current_user.account.transactions
    return render_template('transactions.html', transactions=txns)

# -----------------------
# Run
# -----------------------

if __name__ == '__main__':
    app.run(debug=True)
