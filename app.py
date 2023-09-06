import os

from flask import Flask, render_template, session, g, flash, redirect, url_for, request
from models import connect_db, db, User, CountryPreferences
from forms import UserAddForm, LoginForm, PreferencesForm
from sqlalchemy.exc import IntegrityError
from functools import wraps
import requests
from config import api_key, supported_countries

CURR_USER_KEY = "curr_user"
BASE_URL = 'https://newsapi.org/v2'
API_KEY = api_key
headers = {'X-API-Key': API_KEY}

##### Initializing app ######
app = Flask(__name__)
app.app_context().push()

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = "fjrgjfgoij34389792fruhg"

app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///courier_capstone'))

connect_db(app)
# db.drop_all()
# db.create_all()


#### Helper functions ####
@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not g.user:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        
        return func(*args, **kwargs)
    
    return decorated_function


########## Routes before logging in #########
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.is_submitted() and form.validate():
        if form.is_submitted() and form.validate():
            user = User.authenticate(form.username.data,
                                    form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/user/home")

        flash("Invalid credentials.", 'danger')
        return redirect('/')
    return render_template('login.html', form=form)



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = UserAddForm()
    if form.is_submitted() and form.validate():
        try:
            user = User.signup(
                    username=form.username.data,
                    password=form.password.data,
                    email=form.email.data,
                    image_url=form.image_url.data,
                )
            db.session.commit()

        except IntegrityError:
                flash("Username already taken", 'danger')
                db.session.rollback()
                return render_template('signup.html', form=form)

        do_login(user)

        return redirect("/user/home")

    else:
        return render_template('signup.html', form=form)
    


####### Logged in user views and functions #######

@app.route('/logout')
@login_required
def logout():
    do_logout()
    return redirect('/')

@app.route('/user/home', methods=['GET','POST'])
@login_required
def user_home():
    """When user initially logs in, allow them to select preferences for their user experience."""
    user = User.query.get(g.user.id)
    form = PreferencesForm()
    
    if form.is_submitted() and form.validate():
        country_preferences = request.form.getlist('countries[]')
        for country in country_preferences:
            # find if user already has preference; remove it if so, add it if not
            existing_pref = CountryPreferences.query.filter_by(user=g.user.id, country=country).first()
            cpref = CountryPreferences(country=country, user=g.user.id)
            if existing_pref is None:
                db.session.add(cpref)
            else:
                db.session.delete(existing_pref)
        db.session.commit()
        return redirect('/user/home')
    
    return render_template('/user/home.html', user=user, countries=supported_countries, form=form)

@app.route('/user/news')
@login_required
def get_news():
    response = requests.get(f"{BASE_URL}/top-headlines?country=us&pagesize=1", headers=headers)
    data = response.json()
    print(data)
    return render_template('/user/news.html')