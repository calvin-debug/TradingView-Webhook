
import secrets
import json
from flask_mail import Message
from flask import request, render_template, url_for, flash, redirect
from flask import render_template, flash, redirect, url_for
from flask_login import login_user, current_user

from app import db, bcrypt, mail
from app.models import User
from app.forms import RegistrationForm, LoginForm, UpdateAccountForm, ResetPasswordForm, RequestResetForm, RemoveTicker
from app.functions import create_data, create_log_entry, convert_log, get_open_trades, handle_alert
from app.encryption import enc_data


# Functions for different routes
def home_route():
    # If the current user is authenticated, redirect the user to the account page
    if current_user.is_authenticated:
        return redirect(url_for("overview"))
    
    # Define the login form
    form = LoginForm()

    # The the form is submitted
    if form.validate_on_submit():
        # Check whether such a user with that email exists
        user = User.query.filter_by(email=form.email.data).first()

        # If the user exists and the entered password matches the hashed one
        if user and form.password.data == user.password:

            # Log the user in
            login_user(user)
            return redirect(url_for("overview"))

        # Otherwise flash invalid login
        else:
            flash('Unable to sign in', 'danger')

    # Otherwise, render the "home" template
    return render_template("home.html", form=form)


# Registering route
def register_route():
    # If the user is logged in, redirect them to the account page
    if current_user.is_authenticated:
        return redirect(url_for("account"))

    # Define the registration form
    form = RegistrationForm()

    # If the form is submitted and validated
    if form.validate_on_submit():

        # Creating the password
        # hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        hashed_password = form.password.data

        # Generate the random 16-digit user ID
        user_id = secrets.token_hex(16)

        # Define the current user with the form data to send the data to the database
        user = User(username=form.username.data, email=form.email.data, 
            password=hashed_password, user_id=user_id, exchange="bin", size=25, max_open=0)

        # Add and commit the user to the database
        db.session.add(user)
        db.session.commit()

        create_data(user_id)
        create_log_entry(user_id, "Created account")


        # Refresh the page
        return redirect(url_for('home'))


    # Render the register template and pass the 'form' as a variable so that the HTML can use it
    return render_template('register.html', title="Register", form=form)


# Account page route
def account_route():
    # Form for updating account information
    form = UpdateAccountForm()

    # Current user
    user = User.query.filter_by(user_id=current_user.user_id).first()
    
    if form.validate_on_submit() and form.submit.data:
        current_user.api = form.api.data
        if form.secret.data != '*******':
            # current_user.secret = enc_data(form.secret.data)
            current_user.secret = form.secret.data
        current_user.exchange = form.exchange.data
        current_user.size = round(form.size.data, 0)
        current_user.max_open = round(form.max_open.data, 0)
        db.session.commit()
        flash("Account data updated", 'flash-success')
        return redirect(url_for('account'))
    else:
        # Setting placeholder values for the form
        form.email.data = current_user.email
        form.api.data = current_user.api
        if current_user.secret and current_user.secret != "":
            form.secret.data = "*******"
        form.exchange.data = current_user.exchange
        form.size.data = current_user.size
        form.max_open.data = current_user.max_open
        
    return render_template('account.html', form=form)


# Log route
def log_route():
    log = convert_log()
    return render_template('log.html', log=log)


# Overview route
def overview_route():
    # Fetching the current users user data file
    data = get_open_trades(current_user.user_id)

    # List size
    size = len(data)

    # Getting the user log
    log = convert_log(10)
    
    # Creating the form
    form = RemoveTicker()

    # If the form is submitted
    if form.validate_on_submit():
        # process_signal("sell", form.ticker.data, current_user.user_id)
        return redirect(url_for("overview"))

    # Render the template
    return render_template('overview.html', title="Account", data=data, size=size, form=form, log=log)


# Webhook route
def webhook_route():
    if request.method == 'POST':
        # Loading the data as JSON
        data = json.loads(request.data)

        # Calling the function to handle the message
        handle_alert(data)
        return "Success"
    else:
        return redirect(url_for("home"))


# Send reset route
def send_reset_email_route(user):
    token = user.get_reset_token()
    msg = Message('Password reset request', sender=('TradingView Webhook', 'noreply@tradingviewwebhook.com'), recipients=[user.email])
    msg.body = f'''To reset your TradingView webhook password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request, then simply ignore this email and no changes will be made to your account

    '''

    mail.send(msg)


# Reset route
def reset_route():
    if current_user.is_authenticated:
        return redirect(url_for("account"))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email_route(user)
        flash("An email has been sent with instructions to reset your password", 'info')
        return redirect(url_for("home"))
    return render_template('reset_request.html', title="Reset password", form=form)


# Reset token route
def reset_token_route(token):
    if current_user.is_authenticated:
        return redirect(url_for("account"))

    user = User.verify_reset_token(token)

    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))

    form = ResetPasswordForm()
    if form.validate_on_submit():

        # Hash the password to be saved in the database
        # hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        hashed_password = form.password.data

        # Add and commit the user to the database
        user.password = hashed_password
        db.session.commit()

        # Create the message flash that will be displayed when the page refreshes
        flash("Your password has been updated! You can now log in.", 'success')

        # Refresh the page
        return redirect(url_for('home'))
    return render_template('reset_token.html', title="Reset password", form=form)