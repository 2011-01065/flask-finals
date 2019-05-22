from datetime import datetime
from forum import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(50), unique=True, nullable=False)
	password = db.Column(db.String(60), nullable=False)
	profile_picture = db.Column(db.String(100), nullable=True, default='default.jpg')
	date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
	posts = db.relationship('Post', backref='author', lazy=True)
	activities = db.relationship('Activity', backref='author', lazy=True)

	def __repr__(self):
		return f"User('{self.id}',{self.email}'.'{self.profile_picture}')"

class Post(db.Model):
	post_id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(100), nullable=False)
	body = db.Column(db.String(250), nullable=False)
	image = db.Column(db.String(100), nullable=True, default='default.jpg')
	id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
	activities = db.relationship('Activity', backref='post', lazy=True)

	def __repr__(self):
		return f"Post('{self.post_id}','{self.title}','{self.body}','{self.image}','{self.id}')"

class Activity(db.Model):
	activity_id = db.Column(db.Integer, primary_key=True)
	comment = db.Column(db.String(250), nullable=True)
	upvote = db.Column(db.Boolean, default=False)
	downvote = db.Column(db.Boolean, default=False)
	id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	post_id = db.Column(db.Integer, db.ForeignKey('post.post_id'), nullable=False)
	date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

	def __repr__(self):
		return f"Activity('{self.activity_id}','{self.post_id},'{self.comment}','{self.upvote}','{self.downvote}','{self.date_created}')"
