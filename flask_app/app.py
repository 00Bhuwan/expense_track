from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, abort
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
from datetime import datetime, UTC
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError

basedir = os.path.abspath(os.path.dirname(__file__))
env_path = os.path.join(basedir, '..', '.env')
load_dotenv(env_path)

app = Flask(__name__)
DATABASE_URI = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    join_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))

class Transaction(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10))
    category = db.Column(db.String(100))
    date = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('transactions', lazy=True))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html', error="Oops! This page doesn't exist."), 404

@app.errorhandler(500)
def handle_exception(e):
    return render_template('index.html', error="Something went wrong on our end. Please try again later."), 500

@app.route('/')
def home():
    if 'username' in session:
        return render_template('base.html', username=session['username'])
    else:
        return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Both username and password are required.')
            return redirect(url_for('login'))

        user = User.query.filter_by(username=username).first()
        if user and password == user.password:
            session['username'] = username
            flash('Welcome back!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.')
            return redirect(url_for('login'))
    return render_template('index.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')

        if not all([username, password, email]):
            flash("All fields are required!")
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash("Username already taken!")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash("Email already registered!")
            return redirect(url_for('register'))

        try:
            new_user = User(username=username, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            flash("Account created successfully!")
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash("An error occurred during registration.")
            return redirect(url_for('register'))
    return render_template("index.html")

@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route("/dashboard")
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()

    transactions = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.id.desc()).all()

    total_income = sum(t.amount for t in transactions if t.type == "income")
    total_expense = sum(t.amount for t in transactions if t.type == "expense")
    balance = total_income - total_expense

    return render_template(
        "dashboard.html",
        username = session['username'],
        transactions=transactions,
        income=total_income,
        expense=total_expense,
        balance=balance
    )

@app.route("/add", methods=["POST"])
def add_transaction():
    if 'username' not in session:
        return redirect(url_for('login'))

    title = request.form.get("title")
    amount_str = request.form.get("amount")
    t_type = request.form.get("type")
    category = request.form.get("category")

    if not all([title, amount_str, t_type]):
        flash("Title, amount and type are required.")
        return redirect(url_for("dashboard"))

    try:
        amount = float(amount_str)
        if amount <= 0:
            flash("Amount must be greater than zero.")
            return redirect(url_for("dashboard"))
    except ValueError:
        flash("Invalid amount format.")
        return redirect(url_for("dashboard"))

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        session.pop('username', None)
        return redirect(url_for('login'))

    new_transaction = Transaction(title=title, amount=amount, type=t_type, category=category, user_id=user.id)
    try:
        db.session.add(new_transaction)
        db.session.commit()
        flash("Transaction added successfully!")
    except IntegrityError:
        db.session.rollback()
        flash("Error: Transaction title must be unique.")
    except Exception as e:
        db.session.rollback()
        flash("An unexpected error occurred.")

    return redirect(url_for("dashboard"))

# delete
@app.route("/delete/<int:transaction_id>", methods=["POST"])
def del_transaction(transaction_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    delete_trans = Transaction.query.get_or_404(transaction_id)
    
    # Security check: ensure the transaction belongs to the logged-in user
    user = User.query.filter_by(username=session['username']).first()
    if delete_trans.user_id != user.id:
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    try:
        db.session.delete(delete_trans)
        db.session.commit()
        flash("Transaction deleted.")
    except Exception:
        db.session.rollback()
        flash("Could not delete transaction.")
        
    return redirect(url_for("dashboard"))

# edit
@app.route("/edit/<int:transaction_id>", methods=["GET"])
def edit_transaction(transaction_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()

    transactions = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.id.desc()).all()
    transaction = db.session.get(Transaction, transaction_id)

    total_income = sum(t.amount for t in transactions if t.type == "income")
    total_expense = sum(t.amount for t in transactions if t.type == "expense")
    balance = total_income - total_expense

    return render_template(
        "dashboard.html",
        username=session['username'],
        transactions=transactions,
        income=total_income,
        expense=total_expense,
        balance=balance,
        edit_txn=transaction)

# update
@app.route("/update", methods=["POST"])
def update_transaction():
    if 'username' not in session:
        return redirect(url_for("login"))

    txn_id = request.form.get("id")
    if not txn_id:
        flash("Invalid transaction ID.")
        return redirect(url_for("dashboard"))

    transaction = db.session.get(Transaction, txn_id)
    if not transaction:
        flash("Transaction not found.")
        return redirect(url_for("dashboard"))

    # Security check
    user = User.query.filter_by(username=session['username']).first()
    if transaction.user_id != user.id:
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    try:
        transaction.title = request.form.get("title", transaction.title)
        amount_str = request.form.get("amount")
        if amount_str:
            transaction.amount = float(amount_str)
        transaction.type = request.form.get("type", transaction.type)
        transaction.category = request.form.get("category", transaction.category)
        
        db.session.commit()
        flash("Transaction updated successfully!")
    except ValueError:
        flash("Invalid amount format.")
    except Exception as e:
        db.session.rollback()
        flash("Could not update transaction.")

    return redirect(url_for("dashboard"))

@app.route("/filter", methods=["GET"])
def filter():
    if 'username' not in session:
        return redirect(url_for("login"))

    search_term = request.args.get("search_term", '')
    if search_term:
        items = Transaction.query.filter(Transaction.title.contains(search_term)).all()
    else:
        items = Transaction.query.all()
    return jsonify([
        {
            "id": item.id,
            "title": item.title,
            "amount": item.amount,
            "date": item.date
        }
        for item in items
    ])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)