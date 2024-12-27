from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = secrets.token_urlsafe(24)
db = SQLAlchemy(app)


# Database Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    password_hash = db.Column(db.String(50), nullable=False)
    balance = db.Column(db.Float, nullable=False, default=0.0)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self,password):
        self.password_hash = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password_hash, password)

@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for('dashboard'))
    return render_template("index.html")

# Login
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form['login-username']
        password = request.form['login-password']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('index.html')
    return render_template("login.html")

#Signup
@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        username = request.form["signup-username"]
        password = request.form["signup-password"]
        user = User.query.filter_by(username=username).first()
        if user:
            return render_template("index.html",error="User already here!")
        else:
            new_user = User(username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect(url_for('dashboard'))
    return render_template("signup.html")

@app.route("/dashboard")
def dashboard():
    if "username" in session:
        return render_template("dashboard.html")
    return redirect(url_for('home'))

@app.route('/check_balance', methods=['GET'])
def check_balance():
    username = session.get('username')  # Get username directly from the session
    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            return jsonify({'balance': user.balance})  # Return balance as JSON
        else:
            return jsonify({'message': 'User not found'}), 404
    return jsonify({'message': 'User not logged in'}), 401  # If user is not logged in

@app.route('/deposit', methods=['POST'])
def deposit():
    username = session.get('username')  # Get username directly from the session
    amount = float(request.json.get('amount'))

    user = User.query.filter_by(username=username).first()  # Find the user

    if user:
        user.balance += amount  # Update the balance
        db.session.commit()  # Commit the changes to the database
        return jsonify({'balance': user.balance})  # Return the updated balance as JSON
    else:
        return jsonify({'message': 'User not found'}), 404

@app.route('/withdraw', methods=['POST'])
def withdraw():
    username = session.get('username')  # Get username directly from the session
    amount = float(request.json.get('amount'))

    user = User.query.filter_by(username=username).first()  # Find the user

    if user:
        if user.balance >= amount:  # Check if the user has sufficient balance
            user.balance -= amount  # Deduct the amount from the balance
            db.session.commit()  # Commit the changes to the database
            return jsonify({'balance': user.balance})  # Return the updated balance as JSON
        else:
            return jsonify({'message': 'Insufficient balance'}), 400
    else:
        return jsonify({'message': 'User not found'}), 404

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)  # Remove 'username' from the session
    return redirect(url_for('home'))  # Redirect to the home page


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


