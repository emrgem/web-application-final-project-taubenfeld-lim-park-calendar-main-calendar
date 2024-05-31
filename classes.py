from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON
import json
from sqlalchemy.exc import IntegrityError
from sqlalchemy import Column, Integer, String, ForeignKey, LargeBinary, Boolean, Float, Table
from sqlalchemy.orm.attributes import flag_modified
from werkzeug.security import generate_password_hash, check_password_hash
import csv, io
from extensions import db  
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from functools import wraps
from flask import abort
from flask_login import login_user, current_user, logout_user, login_required
# app = Flask(__name__)
# app.secret_key ='soujgpoisefpowigmppwoigvhw0wefwefwogihj'

# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///calendar.db"
# db = SQLAlchemy(app)


# flag_modified(user_instance, 'modified parameter') when modifying json file; tell database json is modified
def load_default_events():
    with open('static/assets/jsons/default_events.json', 'r') as file:
        default_events = json.load(file)
    return default_events

def load_create_default():
    with open('static/assets/jsons/created_events.json', 'r') as file:
        default_events = json.load(file)
    return default_events

def load_joined_users():
    with open('static/assets/jsons/joined_users.json', 'r') as file:
        default_events = json.load(file)
    return default_events

class UserBase(db.Model, UserMixin):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    email_verification_token = db.Column(db.String(255))
    is_verified = db.Column(db.Boolean, default=False)
    mfa_enabled = db.Column(db.Boolean, default=False)
    phone_number = db.Column(db.String(10), nullable=False, default='')
    account_type = db.Column(db.String(255), nullable=False, default="Student")
    joined_events = db.Column(JSON, default = load_default_events)
    events_created = db.Column(JSON, default = load_create_default)


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"ID: {self.id}\nFirst Name: {self.first_name}\nLast Name: {self.last_name}\nEmail: {self.email}\n Account Type {self.__class__.__name__}"

class User(UserBase):
    __tablename__ = 'users'

class Teacher(User):
    __tablename__ = 'teacher'
    # id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    

class Admin(Teacher):
    __tablename__ = 'admin'
    # id = db.Column(db.Integer, db.ForeignKey('teacher.id'), primary_key=True)

class SuperAdmin(Admin):
    __tablename__ = 's_admin'
    # id = db.Column(db.Integer,db.ForeignKey('admin.id'), primary_key=True)

class Event(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False, default='null')
    description = db.Column(db.Text, nullable=False, default='null')
    image = db.Column(db.LargeBinary, nullable=True)  # Allow image to be None
    image_b64 = db.Column(db.String(255), default='')
    student_limit = db.Column(db.Integer, nullable=False)
    participants = db.Column(JSON, default=load_joined_users)

    def __repr__(self):
        return f"Event Type: {self.__class__.__name__}\nName: {self.name}\n ID: {self.id}\n Creator ID: {self.creator_id}"



class ProjectWednesday(Event):
    id = db.Column(db.Integer, db.ForeignKey('event.id'), primary_key=True, autoincrement=True)
    cycle_number = db.Column(db.Integer, default=1, nullable=False)
    cost = db.Column(db.String(50), default = '0', nullable = True)
    teachers = db.Column(db.String(100), default = '', nullable = False)
    student_assistant = db.Column(db.String(50), default = '', nullable = True)
    special_note = db.Column(db.String(50), default = '', nullable = True)
    

class Tournaments(Event):
    id = db.Column(db.Integer, db.ForeignKey('event.id'), primary_key=True)
    cost_spectator = db.Column(db.Float, default=1, nullable=False)
    cost_competitor = db.Column(db.Float, default=1, nullable=False)
    date_of_tournament = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Performances(Event):
    id = db.Column(db.Integer, db.ForeignKey('event.id'), primary_key=True)
    cost_audience = db.Column(db.Float, default=1, nullable=False)
    date_of_performance = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)



def parse_csv_data(csv_file):
    text_data = csv_file.read().decode("utf-8")
    reader = csv.reader(io.StringIO(text_data))
    headers = next(reader)  # Skip header
    data = [row for row in reader]
    return data


def upload_csv_tournaments(csv_data, creator_id):
    for row in csv_data:
        try:
            event = Tournaments(
                name = row[0],
                description = row[1],
                student_limit = row[2], 
                creator_id = creator_id,
                cost_spectator = row[3],
                cost_competitor = row[4],
                date_of_tournament = row[5], #will need special processing to convert it for database
            )
            db.session.add(event)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        

def upload_csv_wednesday(csv_data, creator_id):
    for row in csv_data:
        try:
            event = ProjectWednesday(
                name=row[0],
                creator_id=creator_id,
                teachers=row[1],
                student_assistant=row[2] if row[2] else '',
                description=row[3][:2500],
                cost=row[4],
                cycle_number=int(row[6]),
                student_limit=20,  # Assuming a default value of 20
                special_note=row[5] if row[5] else '',
                image=b''  # Explicitly set image to empty bytes
            )
            db.session.add(event)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
    
def enter_event(user_id, event_id, param): #pass dictionary parameter as a string in the param
    current_event = Event.query.get(event_id)
    user = User.query.get(user_id)
    if param == "Project Wednesday":
        user.joined_events[param] = f"{current_event.name}" #project wednesday treated as string
    else:
        user.joined_events[param].append(current_event.name)  #all three dictionary parameters are treated as a list
    if param == "Tournaments Competing":
        current_event.participants["Competitors"].append(user_id)
    else:
        current_event.participants["Joined Users"].append(user_id)
    flag_modified(current_event,'participants')
    flag_modified(user,'joined_events')
    db.session.commit()
    return

def leave_event(user_id, event_id, param):
    current_event = Event.query.get(event_id)
    user = User.query.get(user_id)
    # check if used for project wednesday
    if param == 'Project Wednesday':
        user.joined_events[param] = ''
        current_event.participants["Joined Users"].pop(current_event.participants["Joined Users"].index(user_id))
    else:
        if param == 'Tournaments Competing':
            current_event.participants["Competitors"].pop(current_event.participants["Competitors"].index(user_id))
        else:
            current_event.participants["Joined Users"].pop(current_event.participants["Joined Users"].index(user_id))
        user.joined_events[param].pop(user.joined_events[param].index(current_event.name))
    flag_modified(current_event,'participants')
    flag_modified(user,'joined_events')
    db.session.commit()
    return

#Adds to Jinja Front
def is_instance_of(user, class_name):
    cls = globals().get(class_name)
    if cls and isinstance(user,cls):
        return True
    return False

# this is for @admin_required
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.account_type not in ['Admin', 'SuperAdmin']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function