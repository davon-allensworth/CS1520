from flask import Flask, request, url_for, redirect, session, render_template, flash, g
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

# Initialize EventSite
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'events.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False    # makes the warning shut up
db = SQLAlchemy(app)

# Initialize secret_key so I can develop
app.secret_key = 'This is a pretty wacky security code but oh well...'

# events.db initialization method
@app.cli.command('initdb')
def initdb_command():
    db.create_all()
    print('events.db has been initialized')

# Building the Database (Models)

# User Model
class User(db.Model):
    username = db.Column(db.String(30), primary_key=True, unique=True, nullable=False)
    pass_hash = db.Column(db.String(64), nullable=False)    # not sure of necessary hash length (borrowed MiniTwit's)
    attends = db.relationship('Event', secondary='attends', lazy='dynamic', backref=db.backref('attended_by', lazy=True))
    def __repr__(self):
        return '<User %r>' % self.username

# Event Model
class Event(db.Model):
    title = db.Column(db.String(30), primary_key=True, unique=True, nullable=False)
    description = db.Column(db.String(30), nullable=True)
    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)
    host = db.Column(db.String(30), db.ForeignKey('user.username'), nullable=False)
    def __repr__(self):
        return '<Event %r>' % self.title

# Users <-> Events (Association Table)
attends = db.Table('attends',
    db.Column('attender', db.String(30), db.ForeignKey('user.username'), primary_key=True),
    db.Column('event', db.String(30), db.ForeignKey('event.title'), primary_key=True)
)


# Controller from here on out

# determines if user is signed in before accessing every template
# Inspired by MiniTwit
@app.before_request
def before_request_func():
    g.user = None
    if 'username' in session:
        g.user = User.query.filter_by(username=session['username']).first()


# homepage where all events are listed
@app.route("/")
def homepage():
    # start with list of all events
    events = Event.query.order_by(Event.start).all()

    # if a user is logged in, display events hosted by logged in user
    if('username' in session):
        userEvents = Event.query.filter_by(host=session['username']).order_by(Event.start)
    else:
        userEvents = None
    # otherwise, display events hosted by all users
    return render_template('home.html', events=events, userEvents=userEvents, attends=attends)


# allows a user to log in to the site
# if an existing user gets here, goes back to home
@app.route("/login", methods=['GET', 'POST'])
def login():
    if('username' in session):
        flash("You are already logged in")
        return redirect(url_for('homepage'))
    if request.method == 'POST':
        # form has went through, need to confirm user
        user = User.query.filter_by(username=request.form['username']).first()
        if user == None:
            flash('Incorrect username')
            return render_template('login.html')
        # check for correct password
        elif not check_password_hash(user.pass_hash, request.form['password']):
            flash('Incorrect password')
            return render_template('login.html')
        # username and password correct, log user in
        else:
            session['username'] = user.username
            flash('Successfully logged in')
            return redirect(url_for('homepage'))
    # no entry yet, to login page
    return render_template('login.html')


# allows a user to register to the site
# if an existing user gets here, goes back to home
@app.route("/register", methods=['GET', 'POST'])
def register():
    if('username' in session):
        flash("Please log out before registering another account")
        return redirect(url_for('homepage'))
    if request.method == 'POST':
        # check to see if username is taken
        if User.query.filter_by(username=request.form['username']).first() != None:
            flash('Sorry, that username is already taken.')
            return redirect(url_for('register'))
        else:
            # username is not in database...hashing method referencing minitwit
            newUser = User(username=request.form['username'], pass_hash=generate_password_hash(request.form['password']))
            db.session.add(newUser)
            db.session.commit()
            flash('Successfully registered. You can now log in.')
            return redirect(url_for('login'))
    return render_template('register.html')


# lets a signed in user create an event.
# if accessed by someone not logged in, directs to login.
@app.route('/create', methods=['GET', 'POST'])
def create_event():
    if('username' not in session):
        flash("Please log in if you want to create an event")
        return redirect(url_for('login'))
    if request.method == 'POST':
        # to make sure event title is unique
        if Event.query.filter_by(title=request.form['title']).first() != None:
            flash('Sorry, an event exists already with that title. Try something different.')
            return redirect(url_for('create_event'))
        splitStartD = request.form['startD'].split('-')
        splitEndD = request.form['endD'].split('-')
        splitStartT = request.form['startT'].split(':')
        splitEndT = request.form['endT'].split(':')
        # please ignore this horrific line, I setup the form beforehand and didn't want to reformat it. It Works.
        newEvent = Event(title=request.form['title'], description=request.form['description'], start=datetime(int(splitStartD[0]), int(splitStartD[1]), int(splitStartD[2]), int(splitStartT[0]), int(splitStartT[1]), 00), end=datetime(int(splitEndD[0]), int(splitEndD[1]), int(splitEndD[2]), int(splitEndT[0]), int(splitEndT[1]), 00), host=session['username'])
        db.session.add(newEvent)
        db.session.commit()
        flash('Event has been successfully created')
        return redirect(url_for('homepage'))
    return render_template('createEvent.html')


# allows a signed in user to register to attend an event
# wont be shown to existing attendees, but handles them anyways
@app.route('/<event>/attend')
def attend_event(event):
    # first make sure user is signed in
    if('username' not in session):
        flash("Please log in if you want to attend this event")
        return redirect(url_for('login'))

    # get event and attendee
    joinEvent = Event.query.filter_by(title=event).first()  # theoretically the event should not be null, since we saw it already
    attendant = User.query.filter_by(username=session['username']).first()

    #check to see if the user is already attending the event
    if joinEvent in attendant.attends:
        flash('You are already attending this event. So no worries.')
        return redirect(url_for('homepage'))

    # here the user is not attending the event
    User.query.filter_by(username=session['username']).first().attends.append(joinEvent)
    db.session.commit()
    flash('You are now attending "%s"' % joinEvent.title)
    return redirect(url_for('homepage'))



# lets a host of a specific event cancel (delete) it.
@app.route('/<dedEvent>/cancel', methods=['GET', 'POST'])
def cancel_event(dedEvent):
    if request.method == 'POST':
        if request.form['choice'] == 'yes':
            event = Event.query.filter_by(title=dedEvent).first()
            db.session.delete(event)
            db.session.commit()
            flash("Event successfully deleted")
        else:
            flash("Event was not deleted")
        return redirect(url_for('homepage'))
    else:
        return render_template('cancelEvent.html')


# lets a signed in user log out.
# if accessed by someone not logged in, directs to login.
@app.route('/logout')
def logout():
    if('username' not in session):
        flash("Please log in if you want to log out")
        return redirect(url_for('login'))
    session.pop('username', None)   # effectively takes the user out
    flash('You have been successfully logged out.')
    return redirect(url_for('homepage'))


if __name__ == "__main__":
    app.run()
