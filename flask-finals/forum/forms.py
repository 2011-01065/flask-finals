from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import InputRequired, Email, EqualTo, ValidationError
from forum.models import User, Post, Activity

#LOGIN SYSTEM
class RegistrationForm(FlaskForm):
	email = StringField('Email Address', validators=[InputRequired(), Email()])
	password = PasswordField('Password', [InputRequired(), EqualTo('confirm', message='Passwords must match')])
	confirm  = PasswordField('Repeat Password')
	submit = SubmitField('Sign Up')

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user:
			raise ValidationError('The email you entered is already in use. Try again.')


class LoginForm(FlaskForm):
	email = StringField('Email Address', validators=[InputRequired(), Email()])
	password = PasswordField('Password', [InputRequired()])
	remember = BooleanField('Remember Me')
	submit = SubmitField('Login')

#UPDATE ACCOUNT
class UpdateAccountForm(FlaskForm):
	email = StringField('Email Address', validators=[InputRequired(), Email()])
	picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg','jpeg','png'])])
	submit = SubmitField('Update')

	def validate_email(self, email):
		if email.data != current_user.email:
			user = User.query.filter_by(email=email.data).first()
			if user:
				raise ValidationError('The email you entered is already in use. Try again.')

class ForgotPassword(FlaskForm):
	email = StringField('Email Address', validators=[InputRequired(), Email()])
	submit = SubmitField('Reset')

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user == None:
			raise ValidationError('Account does\'t exist.')

class ChangePassword(FlaskForm):
	old_password = PasswordField('Old Password', [InputRequired()])
	new_password = PasswordField('New Password', [InputRequired(), EqualTo('confirm_password', message='Passwords Must Match!')])
	confirm_password = PasswordField('Confirm Password', [InputRequired()])
	submit = SubmitField('Update Password')

#POSTS
class PostForm(FlaskForm):
	title = StringField('Title', validators=[InputRequired()])
	body = TextAreaField('Body', validators=[InputRequired()])
	image = FileField('Add picture', validators=[FileAllowed(['jpg','jpeg','png'])])
	submit = SubmitField('Post')

class CommentForm(FlaskForm):
	comment = TextAreaField('Write a comment', validators=[InputRequired()])
	submit = SubmitField('Comment')
