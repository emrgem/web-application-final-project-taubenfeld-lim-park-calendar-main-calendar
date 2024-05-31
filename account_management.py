from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, current_user, logout_user, login_required, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from classes import User
from extensions import db  # Adjust the import path as necessary
from authlib.integrations.flask_client import OAuth

def register_main():
    first_name = request.form.get('first-name')
    last_name = request.form.get('last-name')
    email = request.form.get('email')
    password = request.form.get('password')
    verify_password = request.form.get('v_password')
    
    # Check for existing user
    user = User.query.filter_by(email=email).first()
    if user:
        flash('User with this email already exists!', 'warning')
        return None
    
    # Check password match
    if password != verify_password:
        flash('Passwords do not match', 'danger')
        return None
    
    # Create new user
    new_user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password_hash=generate_password_hash(password)
    )
    
    # Insert the user into the database
    db.session.add(new_user)
    db.session.commit()
    
    return new_user

def login_management():
    email = request.form.get('email')
    password = request.form.get('password')
    
    # Retrieve user from the database
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        return True
    else:
        flash('Invalid login credentials', 'danger')
        return False

def load_user_main(user_id):
    return User.query.get(int(user_id))

def logout_main():
    logout_user()
    flash("Successfully Logged Out!", 'success')
