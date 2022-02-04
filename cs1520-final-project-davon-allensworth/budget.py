from flask import Flask, request, url_for, redirect, session, render_template, flash, g, json
from flask_sqlalchemy import SQLAlchemy
from flask_restful import reqparse, abort, Api, Resource
import os

# App Config
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'budget.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # makes the warning shut up
app.secret_key = 'This is the last wacky security code but oh well...'
db = SQLAlchemy(app)
api = Api(app)


# MODELS


# User
class User(db.Model):
    username = db.Column(db.String(30), primary_key=True, unique=True, nullable=False)
    password = db.Column(db.String(30), nullable=False)
    categories = db.relationship("Category", back_populates="user")
    purchases = db.relationship("Purchase", back_populates="user")

    def __repr__(self):
        return '<User %r>' % self.username


# Categories
class Category(db.Model):
    name = db.Column(db.String(30), primary_key=True, unique=True, nullable=False)
    limit = db.Column(db.String(30), nullable=False)
    username = db.Column(db.String(30), db.ForeignKey('user.username'))
    user = db.relationship("User", back_populates="categories")

    def __repr__(self):
        return '<Category %r>' % self.name


# Purchases
class Purchase(db.Model):
    username = db.Column(db.String(30), db.ForeignKey('user.username'))
    description = db.Column(db.String(30), primary_key=True, unique=True, nullable=False)
    amount = db.Column(db.String(30), nullable=False)
    date = db.Column(db.String(30), nullable=False)
    category = db.Column(db.String(30), nullable=False)
    user = db.relationship("User", back_populates="purchases")

    def __repr__(self):
        return '<Purchase %r>' % self.description



# RESTful
class CategoryResource(Resource):
    def get(self):
        categories = Category.query.filter_by(username=session['username']).all()
        c = []
        for category in categories:
            category = category.__dict__
            del category['_sa_instance_state']
            c.append(category)
        return json.jsonify(c)

    def post(self):
        new_category = Category(
            name=request.form['name'],
            limit=request.form['limit'],
            username=session['username']
        )
        db.session.add(new_category)
        db.session.commit()
        return 201


class DelCategoryResource(Resource):
    def delete(self, categoryId):
        category = Category.query.filter_by(name=categoryId).first()
        cat_purchases = Purchase.query.filter_by(category=categoryId).all()
        for purchase in cat_purchases:
            purchase.category = ""
        db.session.delete(category)
        db.session.commit()
        return '', 204


class PurchaseResource(Resource):
    def get(self):
        purchases = Purchase.query.filter_by(username=session['username']).all()
        p = []
        for purchase in purchases:
            purchase = purchase.__dict__
            del purchase['_sa_instance_state']
            p.append(purchase)
        return json.jsonify(p)

    def post(self):
        if request.form['category'] != "" and Category.query.filter_by(name=request.form['category']).first() is None:
            return 400
        if Purchase.query.filter_by(description=request.form['description']).first() is not None:
            return 400
        new_purchase = Purchase(
            username=session['username'],
            description=request.form['description'],
            amount=request.form['amount'],
            date=request.form['date'],
            category=request.form['category']
        )
        print(new_purchase.category)
        db.session.add(new_purchase)
        db.session.commit()


# API Resource Setup
api.add_resource(CategoryResource, '/cats')
api.add_resource(DelCategoryResource, '/cats/<categoryId>')
api.add_resource(PurchaseResource, '/purchases')


# determines if user is signed in before accessing every template
# Inspired by MiniTwit
@app.before_request
def before_request_func():
    g.user = None
    if 'username' in session:
        g.user = User.query.filter_by(username=session['username']).first()


# Homepage
@app.route("/", methods=['GET', 'POST'])
def home():
    # Not Signed in
    if 'username' not in session:
        # Register or Login
        if request.method == 'POST':
            if request.form['result'] == 'Login':
                return redirect(url_for('login'))
            else:
                return redirect(url_for('register'))
        else:
            return render_template('home.html')
    # Signed in
    else:
        return render_template('budget.html')


# Register
@app.route("/register", methods=['GET', 'POST'])
def register():
    if 'username' in session:
        flash("Please log out before registering another account")
        return redirect(url_for('home'))
    if request.method == 'POST':
        # check to see if username is taken
        if User.query.filter_by(username=request.form['username']).first() is not None:
            flash('Sorry, that username is already taken.')
            return redirect(url_for('register'))
        else:
            # username is not in database
            new_user = User(username=request.form['username'], password=request.form['password'])
            db.session.add(new_user)
            db.session.commit()
            flash('Successfully registered. You can now log in.')
            return redirect(url_for('login'))
    return render_template('register.html')


# Login
@app.route("/login", methods=['GET', 'POST'])
def login():
    if 'username' in session:
        flash("You are already logged in")
        return redirect(url_for('home'))
    if request.method == 'POST':
        # form has went through, need to confirm user
        user = User.query.filter_by(username=request.form['username']).first()
        if user is None:
            flash('Incorrect username')
            return render_template('login.html')
        # check for correct password
        elif not user.password == request.form['password']:
            flash('Incorrect password')
            return render_template('login.html')
        # username and password correct, log user in
        else:
            session['username'] = user.username
            flash('Successfully logged in')
            return redirect(url_for('home'))
    # no entry yet, to login page
    return render_template('login.html')


# Logout
@app.route('/logout')
def logout():
    if 'username' not in session:
        flash("Please log in if you want to log out")
        return redirect(url_for('login'))
    session.pop('username', None)  # effectively takes the user out
    flash('You have been successfully logged out.')
    return redirect(url_for('home'))


# Initialization
@app.cli.command('initdb')
def initdb_command():
    db.create_all()
    print('budget.db has been initialized')


if __name__ == "__main__":
    app.run()
