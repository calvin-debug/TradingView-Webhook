# Importing
import app.route_functions as route_functions
from flask import url_for, redirect
from app import app
from flask_login import logout_user, login_required


# Homepage
# Both the "/" (no subpage specified) and the "/home" direct to the home page
@app.route("/")
def ret_home():
    return redirect(url_for("home"))

@app.route("/home", methods=['GET', 'POST'])
def home():
    return route_functions.home_route()


# Register page
@app.route("/register", methods=['GET', 'POST'])
def register():
    return route_functions.register_route()


# Log the user out
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


# User log route
@app.route("/log")
@login_required
def user_log():
    return route_functions.log_route()


# Overview route
@app.route("/overview", methods=['GET', 'POST'])
# Requires login
@login_required
def overview():
    return route_functions.overview_route()


# Account info route
@app.route('/account', methods=['POST', 'GET'])
@login_required
def account():
    return route_functions.account_route()
    

# Webhook route - receives and processes signals
@app.route("/webhook", methods=['POST', 'GET'])
def webhook():
    return route_functions.webhook_route()


# Resetting your password
def send_reset_email(user):
    return route_functions.send_reset_email_route(user)

@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    return route_functions.reset_route()

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    return route_functions.reset_token_route(token)



