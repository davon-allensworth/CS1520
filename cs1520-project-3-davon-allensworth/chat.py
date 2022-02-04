from flask import Flask, request, url_for, redirect, session, render_template, flash, g
import json
import os

# App Config
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'events.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # makes the warning shut up
app.secret_key = 'This is still a pretty wacky security code but oh well...'


# Structures
class Room(object):
    def __init__(self, name, description, admin, messages):
        self.name = name
        self.description = description
        self.admin = admin
        self.messages = messages


class Message(object):
    def __init__(self, text, author):
        self.text = text
        self.author = author
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
    

#necessary variables
users = {}          #represents all registered users
active_users = []   #represents signed in users
chatRooms = []      #represents existing chat rooms


# Homepage
@app.route("/", methods=['GET', 'POST'])
def home():
    # User can either sign in or register
    if request.method == 'POST':
        if request.form['result'] == 'Login':
            return redirect(url_for('login'))
        else:
            return redirect(url_for('register'))
    else:
        return render_template('home.html')


# Register
@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = request.form['username']
        if user in users:
            flash("Sorry that username is already taken.")
            return redirect(url_for('register'))
        else:
            users[request.form['username']] = request.form['password']
            flash("Welcome aboard " + user + "! Please login to begin chatting.")
            return redirect(url_for('login'))
    else:
        return render_template('register.html')


# Login
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        if user not in users:
            flash("Sorry the username '" + user + "' is not registered.")
            return redirect(url_for('login'))
        elif users.get(user) != request.form['password']:
            flash("Incorrect password for user: " + user)
            return redirect(url_for('login'))
        elif user in active_users:
            flash("Sorry, the username '" + user + "' is already logged in elsewhere.")
            return redirect(url_for('login'))
        else:
            flash("Successfully logged in user: " + user)
            active_users.append(user)
            return redirect(url_for('rooms', user=user))
    else:
        return render_template('login.html')


# Logout
@app.route("/<user>/logout")
def logout(user):
    flash("Successfully logged out user: " + user)
    active_users.remove(user)
    return redirect(url_for('home'))


# List Available Rooms
@app.route("/<user>/rooms")
def rooms(user):
    # List all chat rooms (if any)
    if user not in active_users:
        flash("Sorry, the username '" + user + "' is not logged in.")
        return redirect(url_for('login'))
    return render_template('rooms.html', user=user, rooms=chatRooms)


# Room Creation
@app.route("/<user>/makeRoom", methods=['GET', 'POST'])
def makeRoom(user):
    # Use a form to construct a new chat room
    if user not in active_users:
        flash("Sorry, the username '" + user + "' is not logged in.")
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form["name"]
        for chatRoom in chatRooms:
            if chatRoom.name == name:
                flash("Sorry, a room with the name '" + name + "' already exists.")
                return redirect(url_for('makeRoom', user=user))
        description = request.form["description"]
        messages = []
        new_room = Room(name, description, user, messages)
        chatRooms.append(new_room)
        flash("Your room was successfully created.")
        return redirect(url_for('rooms', user=user))
    return render_template('createRoom.html', user=user)


# Delete Chatroom
@app.route("/<user>/roomId=<room>/delete")
def removeRoom(user, room):
    for chatRoom in chatRooms:
        if chatRoom.name == room:
            chatRooms.remove(chatRoom)
            break
    flash("Successfully deleted chatroom: " + room)
    return redirect(url_for('rooms', user=user))


# Enter Chatroom
@app.route("/<user>/roomId=<room>")
def loadRoom(user, room):
    targetRoom = ""
    for chatRoom in chatRooms:
        if chatRoom.name == room:
            targetRoom = chatRoom
            break
    return render_template('room.html', user=user, room=targetRoom)


# Recieves new messages from client
@app.route("/add_message", methods=['POST'])
def add_message():
    targetRoom = ""
    room = request.form["room"]
    for chatRoom in chatRooms:
        if chatRoom.name == room:
            targetRoom = chatRoom
            break
    user = request.form["user"]
    message = request.form["message"]
    new_message = Message(message, user)
    targetRoom.messages.append(new_message)
    return "OK!"


# Sends current messages to client
@app.route("/<user>/<room>/get_messages")
def get_messages(room, user):
    targetRoom = None
    for chatRoom in chatRooms:
        if chatRoom.name == room:
            targetRoom = chatRoom
            break
    if targetRoom == None:
        flash("The admin of room '" + room + "' has deleted it.")
        return redirect(url_for('rooms', user=user))
    return json.dumps([message.__dict__ for message in targetRoom.messages])


# Initializes ChatSite
if __name__ == "__main__":
    app.run()
