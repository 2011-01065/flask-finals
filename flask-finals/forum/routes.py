import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request
from forum import app, db, bcrypt, mail
from forum.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, CommentForm, ForgotPassword, ChangePassword
from forum.models import User, Post, Activity
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

# SEND MAILER
def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)

# UPLOAD
def save_picture(form_picture, type):
	random_hex = secrets.token_hex(8)
	_, f_ext = os.path.splitext(form_picture.filename)
	picture_fn = random_hex + f_ext
	picture_path = os.path.join(app.root_path, 'static/images', picture_fn)

	if type == 'avatar':
		output_size = (150, 150)

	i = Image.open(form_picture)
	if type == 'avatar':
		i.thumbnail(output_size)
	i.save(picture_path)

	return picture_fn


@app.route("/", methods=['GET', 'POST'])
@app.route("/home", methods=['GET', 'POST'])
def home():
	form = CommentForm()

	# DATE SORT
	if request.args.get('date') and request.args.get('date') == 'desc':
		column_name = 'a.date_created'
		order = 'DESC'
	elif request.args.get('date') and request.args.get('date') == 'asc':
		column_name = 'a.date_created'
		order = 'ASC'

	# UPVOTE SORT
	elif request.args.get('upvote') and request.args.get('upvote') == 'desc':
		column_name = 'upvote_count'
		order = 'DESC'
	elif request.args.get('upvote') and request.args.get('upvote') == 'asc':
		column_name = 'upvote_count'
		order = 'ASC'

	# COMMENT SORT
	elif request.args.get('comment') and request.args.get('comment') == 'desc':
		column_name = 'comments_count'
		order = 'DESC'
	elif request.args.get('comment') and request.args.get('comment') == 'asc':
		column_name = 'comments_count'
		order = 'ASC'

	else:
		column_name = 'a.post_id'
		order = 'DESC'


	posts = db.session.execute("SELECT a.post_id, a.title, a.body, a.image, a.date_created, c.email, c.profile_picture, (SELECT COUNT(1) FROM Activity WHERE post_id=a.post_id AND comment <> 'None') AS comments_count, (SELECT COUNT(1) FROM Activity WHERE post_id=a.post_id AND upvote = 1) AS upvote_count, (SELECT COUNT(1) FROM Activity WHERE post_id=a.post_id AND downvote = 1) AS downvote_count FROM Post a LEFT JOIN Activity b ON b.post_id = a.post_id LEFT JOIN User c ON c.id = a.id GROUP BY a.post_id ORDER BY " + column_name + " " + order).fetchall()

	return render_template('home.html', title="Home", posts=posts, form=form)


@app.route("/register", methods=['GET', 'POST'])
def register():
	form = RegistrationForm()
	if form.validate_on_submit():
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user = User(email=form.email.data, password=hashed_password)
		db.session.add(user)
		db.session.commit()
		message = 'Good Day! <p> Welcome to Pi Forum!</p>'
		send_email('Greetings, New User!', 'noreply@forum.com', [form.email.data], message, message)
		flash(f'Account created for {form.email.data}!', 'success')
		return redirect(url_for('login'))
	return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user and bcrypt.check_password_hash(user.password, form.password.data):
			login_user(user, remember=form.remember.data)
			next_page = request.args.get('next')
			return redirect(next_page) if next_page else redirect(url_for('home'))
		else:
			flash('Email or Password is Incorrect!', 'danger')
	return render_template('login.html', title='Login', form=form)


@app.route("/forgot-password", methods=['GET', 'POST'])
def forgot_password():
	form = ForgotPassword()
	if form.validate_on_submit():
		password = secrets.token_hex(8)
		message = 'Your new password is ' + password
		send_email('Password Reset Successful!', 'noreply@forum.com', [form.email.data], message, message)
		flash(f'Check your email for your new password!', 'success')
		return redirect(url_for('login'))
	return render_template('forgot_password.html', title='Login', form=form)


@app.route("/logout")
def logout():
	logout_user()
	return redirect(url_for('home'))

#UPDATE ACCOUNT
@app.route("/profile", methods=['GET','POST'])
@login_required
def profile():
	form = UpdateAccountForm()
	user = User.query.get_or_404(current_user.id)
	if form.validate_on_submit():

		if form.picture.data:
			picture_file = save_picture(form.picture.data, 'avatar')
			current_user.profile_picture = picture_file
			user.email=form.email.data
			user.profile_picture=picture_file
		else:
			current_user.email = form.email.data
			user.email=form.email.data
		db.session.commit()

		flash('Account successfully updated!', 'success')
		return redirect(url_for('profile'))

	elif request.method == 'GET':
		form.email.data = current_user.email
	image_file = url_for('static', filename='images/' + current_user.profile_picture)
	return render_template('profile.html', title='Profile', profile_picture=image_file, form=form)


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
	form = ChangePassword()
	if form.validate_on_submit():
		user = User.query.filter_by(id=current_user.id).first()
		if user and bcrypt.check_password_hash(user.password, form.old_password.data):
			message = 'Successfully updated your password!'
			send_email('Password changed!', 'noreply@forum.com', [user.email], message, message)
			flash('Password updated successfully!', 'success')
			return redirect(url_for('account'))
		else:
			flash('Old password is incorrect!', 'danger')
	return render_template('account.html', title='Login', form=form)

#POSTS
@app.route("/post/new", methods=['GET','POST'])
@login_required
def new_post():
	form = PostForm()
	if form.validate_on_submit():
		if form.image.data:
			image = save_picture(form.image.data, 'post')
			post = Post(title=form.title.data, body=form.body.data, image=image, author=current_user)
		else:
			post = Post(title=form.title.data, body=form.body.data, author=current_user)
		db.session.add(post)
		db.session.commit()
		flash('Post successfully posted!', 'success')
		return redirect(url_for('home'))
	return render_template('create_post.html', title='New Post', form=form)


@app.route("/post/<int:post_id>", methods=['GET','POST'])
def post(post_id):
	post = Post.query.get_or_404(post_id)

	comments = Activity.query.filter_by(post_id=post_id)
	comments_count = 0
	#comments_count = Activity.query.filter_by(post_id=post_id).count()
	for comment in comments:
		if comment.comment:
			comments_count += 1
	comment_form = CommentForm()

	upvote_count = Activity.query.filter_by(post_id=post_id, upvote=True).count()
	downvote_count = Activity.query.filter_by(post_id=post_id, downvote=True).group_by(Activity.id).count()

	return render_template('post.html', title=post.title, post=post,
						comment_form=comment_form, comments=comments,
						comments_count=comments_count, upvote_count=upvote_count,
						downvote_count=downvote_count)

############UPVOTING
@app.route("/post/<int:post_id>/upvote", methods=['GET','POST'])
@login_required
def upvote(post_id):
    #Check existing posts
	post = Post.query.get_or_404(post_id)
	#Check if user upvoted this post
	upvote = Activity.query.filter_by(id=current_user.id, upvote=True, post_id=post_id).first()

	if upvote:
		Activity.query.filter_by(id=current_user.id, upvote=True, post_id=post_id).delete()
	else:
		action_upvote = Activity(upvote=True, id=current_user.id, post_id=post_id)
		db.session.add(action_upvote)
	db.session.commit()

	flash('Successfully upvoted this post', 'success')
	return redirect(url_for('post', post_id=post_id))

############DOWNVOTING
@app.route("/post/<int:post_id>/downvote", methods=['GET','POST'])
@login_required
def downvote(post_id):
	#Check existing posts
	post = Post.query.get_or_404(post_id)
	#Check if user downvoted post
	downvote = Activity.query.filter_by(id=current_user.id, downvote=True, post_id=post_id).first()

	if downvote:
		Activity.query.filter_by(id=current_user.id, downvote=True, post_id=post_id).delete()
	else:
		action_downvote = Activity(downvote=True, id=current_user.id, post_id=post_id)
		db.session.add(action_downvote)
	db.session.commit()

	flash('Successfully downvoted this post', 'success')
	return redirect(url_for('post', post_id=post_id))

#############COMMENTING
@app.route("/post/<int:post_id>/comment", methods=['GET','POST'])
@login_required
def comment(post_id):
	form = CommentForm()
	#Check if comment is made
	if form.validate_on_submit():
		comment = Activity(comment=form.comment.data, id=current_user.id, post_id=post_id)
		db.session.add(comment)
		db.session.commit()
		author_email = db.session.execute("SELECT email FROM User a JOIN Post b ON b.id = a.id WHERE b.post_id = " + str(post_id)).fetchall()
		subject = 'Someone has commented in your post.'
		message = current_user.email + ' New User Comment "' + form.comment.data + '" on your post at http://localhost:5000/post/' + str(post_id) + '.'
		send_email(subject, 'noreply@forum.com', [author_email[0].email], message, message)
		flash('Comment successfully added!', 'success')
		# comments_count = comments_count + 1;

	return redirect(url_for('post', post_id=post_id))

@app.route("/authored")
@login_required
def authored():
	form = CommentForm()
	# sort date
	if request.args.get('date') and request.args.get('date') == 'desc':
		column_name = 'a.date_created'
		order = 'DESC'
	elif request.args.get('date') and request.args.get('date') == 'asc':
		column_name = 'a.date_created'
		order = 'ASC'

	# sort upvote
	elif request.args.get('upvote') and request.args.get('upvote') == 'desc':
		column_name = 'upvote_count'
		order = 'DESC'
	elif request.args.get('upvote') and request.args.get('upvote') == 'asc':
		column_name = 'upvote_count'
		order = 'ASC'

	# sort comment
	elif request.args.get('comment') and request.args.get('comment') == 'desc':
		column_name = 'comments_count'
		order = 'DESC'
	elif request.args.get('comment') and request.args.get('comment') == 'asc':
		column_name = 'comments_count'
		order = 'ASC'

	else:
		column_name = 'a.post_id'
		order = 'DESC'

	#MAIN QUERY
	posts = db.session.execute("SELECT a.post_id, a.title, a.body, a.image, a.date_created, c.email, c.profile_picture, (SELECT COUNT(1) FROM Activity WHERE post_id=a.post_id AND comment <> 'None') AS comments_count, (SELECT COUNT(1) FROM Activity WHERE post_id=a.post_id AND upvote = 1) AS upvote_count, (SELECT COUNT(1) FROM Activity WHERE post_id=a.post_id AND downvote = 1) AS downvote_count FROM Post a LEFT JOIN Activity b ON b.post_id = a.post_id LEFT JOIN User c ON c.id = a.id WHERE a.id = " + str(current_user.id) + " GROUP BY a.post_id ORDER BY " + column_name + " " + order).fetchall()

	return render_template('home.html', title='Authored Posts', posts=posts, form=form)

@app.route("/upvoted")
@login_required
def upvoted():
	form = CommentForm()

	# sort date
	if request.args.get('date') and request.args.get('date') == 'desc':
		column_name = 'a.date_created'
		order = 'DESC'
	elif request.args.get('date') and request.args.get('date') == 'asc':
		column_name = 'a.date_created'
		order = 'ASC'

	# sort upvote
	elif request.args.get('upvote') and request.args.get('upvote') == 'desc':
		column_name = 'upvote_count'
		order = 'DESC'
	elif request.args.get('upvote') and request.args.get('upvote') == 'asc':
		column_name = 'upvote_count'
		order = 'ASC'

	# sort comment
	elif request.args.get('comment') and request.args.get('comment') == 'desc':
		column_name = 'comments_count'
		order = 'DESC'
	elif request.args.get('comment') and request.args.get('comment') == 'asc':
		column_name = 'comments_count'
		order = 'ASC'

	else:
		column_name = 'a.post_id'
		order = 'DESC'

	# main query
	posts = db.session.execute("SELECT a.post_id, a.title, a.body, a.image, a.date_created, c.email, c.profile_picture, (SELECT COUNT(1) FROM Activity WHERE post_id=a.post_id AND comment <> 'None') AS comments_count, (SELECT COUNT(1) FROM Activity WHERE post_id=a.post_id AND upvote = 1) AS upvote_count, (SELECT COUNT(1) FROM Activity WHERE post_id=a.post_id AND downvote = 1) AS downvote_count FROM Post a JOIN Activity b ON b.post_id = a.post_id JOIN User c ON c.id = a.id WHERE b.id = " + str(current_user.id) + " AND b.upvote = 1 GROUP BY a.post_id ORDER BY " + column_name + " " + order).fetchall()

	return render_template('home.html', title='Upvoted Posts', posts=posts, form=form)

@app.route("/commented")
@login_required
def commented():
	form = CommentForm()

	# sort date
	if request.args.get('date') and request.args.get('date') == 'desc':
		column_name = 'a.date_created'
		order = 'DESC'
	elif request.args.get('date') and request.args.get('date') == 'asc':
		column_name = 'a.date_created'
		order = 'ASC'

	# sort upvote
	elif request.args.get('upvote') and request.args.get('upvote') == 'desc':
		column_name = 'upvote_count'
		order = 'DESC'
	elif request.args.get('upvote') and request.args.get('upvote') == 'asc':
		column_name = 'upvote_count'
		order = 'ASC'

	# sort comment
	elif request.args.get('comment') and request.args.get('comment') == 'desc':
		column_name = 'comments_count'
		order = 'DESC'
	elif request.args.get('comment') and request.args.get('comment') == 'asc':
		column_name = 'comments_count'
		order = 'ASC'

	else:
		column_name = 'a.post_id'
		order = 'DESC'

	# main query
	posts = db.session.execute("SELECT a.post_id, a.title, a.body, a.image, a.date_created, c.email, c.profile_picture, (SELECT COUNT(1) FROM Activity WHERE post_id=a.post_id AND comment <> 'None') AS comments_count, (SELECT COUNT(1) FROM Activity WHERE post_id=a.post_id AND upvote = 1) AS upvote_count, (SELECT COUNT(1) FROM Activity WHERE post_id=a.post_id AND downvote = 1) AS downvote_count FROM Post a JOIN Activity b ON b.post_id = a.post_id JOIN User c ON c.id = a.id WHERE b.id = " + str(current_user.id) + " AND b.comment <> 'None' GROUP BY a.post_id ORDER BY " + column_name + " " + order).fetchall()

	return render_template('home.html', title='Commented Posts', posts=posts, form=form)
