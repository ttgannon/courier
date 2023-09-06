"""Models for Courier app."""
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

def connect_db(app): 
    db.app = app
    db.init_app(app)

class User(db.Model):
    """An app user profile information"""
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text, nullable=False, unique=True)
    email = db.Column(db.Text, nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.Text)

    @classmethod 
    def register(cls, username, pwd, email, first_name, last_name):
        """Register user w/hashed password and return user"""

        hashed = bcrypt.generate_password_hash(pwd)
        hashed_utf8 = hashed.decode('utf8')

        return cls(username=username, password=hashed_utf8, email=email, first_name=first_name, last_name=last_name)
    
    @classmethod
    def signup(cls, username, email, password, image_url):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
            image_url=image_url,
        )

        db.session.add(user)
        return user
    
    @classmethod
    def authenticate(cls, username, password):
        """Authenticate the sign in. 

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False

class Story(db.Model):
    """Story information from publication"""
    __tablename__ = "stories"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.Text, nullable=False)
    date = db.Column(db.Text)
    author = db.Column(db.Text)
    outlet = db.Column(db.Integer, db.ForeignKey('outlets.id'))

class Outlet(db.Model):
    """Outlet information from publication"""
    __tablename__ = "outlets"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False, unique=True)

class Content(db.Model):
    """Content tags for users to add to their story filters"""
    __tablename__ = "content"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, unique=True, nullable = False)
    story = db.Column(db.Integer, db.ForeignKey('stories.id'))

class Likes(db.Model):
    """Likes users make on stories"""
    __tablename__ = "likes"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user = db.Column(db.Integer, db.ForeignKey('users.id'))
    story = db.Column(db.Integer, db.ForeignKey('stories.id'))

class Preferences(db.Model):
    """Users set their own content preferences saved in the database"""
    __tablename__ = "preferences"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user = db.Column(db.Integer, db.ForeignKey('users.id'))
    content_preference = db.Column(db.Integer, db.ForeignKey('content.id'))
    outlet_preference = db.Column(db.Integer, db.ForeignKey('outlets.id'))
    country = db.Column(db.Text)


class CountryPreferences(db.Model):
    """Users set their country preferences"""
    __tablename__ = "country_preferences"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user = db.Column(db.Integer, db.ForeignKey('users.id'))
    country = db.Column(db.Text)
