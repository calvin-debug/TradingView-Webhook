from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Email
from app.models import User
from flask_login import current_user



# List of invalid character that cannot be included in any of the input fields (except the email field)
invalid_chars_list = ['@', '/', '\\', ',', ' ', ';', ':', '?', '!', '&', '%', '	', '¤', '"', "'", '(', ')', '{', '}', '[', ']', '~', "#"]
capitals = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']


# Function to check whether the user input contains invalid characters
def check_invalid(check_against):
	
	# Declaring variables
	contains_invalid_chars = False
	char = ""

	# For loop to loop over the input and check against the forbidden list
	for char in invalid_chars_list:
		if char in check_against.data:
			contains_invalid_chars = True
			invalid_char = char
			break

	# Returning a tuple
	return contains_invalid_chars, char



# Function to check whether the user input contains invalid characters
def check_capitals(check_against):
	
	# Declaring variables
	contains_capital = False

	# For loop to loop over the input and check against the forbidden list
	for char in capitals:
		if char in check_against.data:
			contains_capital = True
			break

	# Returning a tuple
	return contains_capital




# Registration form
class RegistrationForm(FlaskForm):

	# Defining the field names
	username = StringField('TradingView username', validators=[DataRequired(), Length(min=2, max=30)])
	email = StringField('Email', validators=[DataRequired()])
	password = PasswordField('Password (at least one symbol, one number and one uppercase letter)', validators=[DataRequired(), Length(min=10, max=30)])
	confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=10, max=30), EqualTo('password')])
	#agree_tc = BooleanField('Terms and conditions', validators=[DataRequired()])
	submit = SubmitField('Sign Up')


	# Defining the validation for the username
	def validate_username(self, username):

		# Invalidation check
		[is_invalid, invalid_char] = check_invalid(username)

		# Fetch user with input username from the database. If doesn't exist, returns "False"
		user = User.query.filter_by(username=username.data).first()

		# If user is found, raise error saying the username already exists
		if user:
			raise ValidationError('That username is already taken. Please choose a different one.')

		# If the username contains invalid characters, invalidate the input
		if is_invalid:
			raise ValidationError(f'Username contains forbidden characters ({invalid_char}).')


	# Defining validation for the email
	def validate_email(self, email):

		# If the input email already exists in the database, then raise error
		email = User.query.filter_by(email=email.data).first()
		if email:
			raise ValidationError('That email is already taken. Please choose a different one.')


	def validate_password(self, password):

		[contains_invalid, _] = check_invalid(password)
		contains_capital = check_capitals(password)

		if not contains_capital:
			raise ValidationError("Password must have at least one capital letter.")





# Login form
class LoginForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(), Email()])
	password = PasswordField('Password', validators=[DataRequired(), Length(min=5, max=30)])
	remember = BooleanField('Remember Me')
	submit = SubmitField('Login')


# Form for updating the account information
class UpdateAccountForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(), Email()])
	api = StringField('API key')
	secret = StringField('Secret key')
	exchange = SelectField('Exchange', choices=[('bin', 'Binance'), ('binus', 'Binance US')])
	size = IntegerField('Bet size', validators=[DataRequired()])
	max_open = IntegerField('Max Open', validators=[DataRequired()])
	submit = SubmitField('Update info')



	def validate_email(self, email):
		if email.data != current_user.email:
			user = User.query.filter_by(email=email.data).first()
			if user:
				raise ValidationError('That email is already taken. Please choose a different one.')


	def validate_api(self, api):

		[is_invalid, invalid_char] = check_invalid(api)

		if is_invalid:
			raise ValidationError(f"API contains forbidden characters ({invalid_char})")


	def validate_secret(self, secret):
		
		[is_invalid, invalid_char] = check_invalid(secret)

		if is_invalid:
			raise ValidationError(f"Secret contains forbidden characters ({invalid_char})")

	def validate_max_open(self, max_open):
		max_value = 25
		min_value = 1

		# Try to turn the input into a number, if it fails, raise "not a valid number" error
		try:
			value_limits = int(max_open.data) < min_value or int(max_open.data) > max_value
		except:
			raise ValidationError(f'{max_open.data} is not a valid number')
		if value_limits:
			raise ValidationError(f'Please choose a value between {min_value} and {max_value}')



class RequestResetForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired()])
	submit = SubmitField('Request Password Reset')

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user is None:
			raise ValidationError('There is no account with that email. You must register first.')


class ResetPasswordForm(FlaskForm):
	password = PasswordField('Password (at least one symbol, one number and one uppercase letter)', validators=[DataRequired(), Length(min=10, max=30)])
	confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=5, max=30), EqualTo('password')])
	submit = SubmitField('Reset Password')



	def validate_password(self, password):

		[contains_invalid, _] = check_invalid(password)
		contains_capital = check_capitals(password)

		if not contains_invalid:
			raise ValidationError("Password must have at least one symbol.")

		if not contains_capital:
			raise ValidationError("Password must have at least one capital letter.")




class RemoveTicker(FlaskForm):
	ticker = StringField("")
	delete = SubmitField("")