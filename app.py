from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
from datetime import datetime, UTC
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError

load_dotenv()

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
    join_date = db.Column(db.DateTime, nullable=False, default=datetime.now(UTC))

class Transaction(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10))
    category = db.Column(db.String(100))
    date = db.Column(db.DateTime, default=datetime.now(UTC))

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

@app.route('/')
def home():
    if 'username' in session:
        return render_template('base.html', username=session['username'])
    else:
        return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and password == user.password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('index.html', error='Invalid credentials')
    return render_template('index.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        user = User.query.filter_by(username=username).first()
        if user:
            return render_template("index.html", error="User already registered!!")
        else:
            new_user = User(username=username, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect(url_for('dashboard'))
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

    title = request.form["title"]
    amount = request.form["amount"]
    t_type = request.form["type"]
    category = request.form["category"]

    user = User.query.filter_by(username=session['username']).first()

    new_transaction = Transaction(title=title, amount=amount, type=t_type, category=category, user_id=user.id)
    try:
        db.session.add(new_transaction)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return f"Error: Title must be unique."

    return redirect(url_for("dashboard"))


# delete
@app.route("/delete/<int:transaction_id>", methods=["POST"])
def del_transaction(transaction_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    delete_trans = Transaction.query.get_or_404(transaction_id)
    db.session.delete(delete_trans)
    db.session.commit()
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

    txn_id = request.form["id"]
    transaction = db.session.get(Transaction, txn_id)

    if transaction:
        transaction.title = request.form["title"]
        transaction.amount = float(request.form["amount"])
        transaction.type = request.form["type"]
        transaction.category = request.form["category"]
        db.session.commit()

    return redirect(url_for("dashboard"))

if __name__ == '__main__':
    app.run(debug=True)