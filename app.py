import os

from flask import Flask, render_template, session, g, flash, redirect, url_for, request, jsonify
from models import connect_db, db, User, CountryPreferences, OutletPreferences
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

@app.route('/user_home')
@login_required
def go_homepage():
    outletprefs = []
    outletpreflist = OutletPreferences.query.filter_by(user=g.user.id).all()
    for outlet in outletpreflist:
        print("++++++++++++++++",outlet)
        outletprefs.append(outlet)
    stories = requests.get(f"{BASE_URL}/top-headlines?sources=", headers=headers)

    return render_template('user/home.html')


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
    form1 = PreferencesForm()
    form2 = PreferencesForm()
    return render_template('/user/first.html', user=user, countries=supported_countries, form1=form1, form2=form2)

@app.route('/user/first_prefs', methods=['GET', 'POST'])
@login_required
def first_prefs():
    user = User.query.get(g.user.id) 
    form = PreferencesForm()
    if form.is_submitted() and form.validate():
        country_preferences = request.form.getlist('countries[]')
        params = []
        for country in country_preferences:
            params.append(country)
        data = []
        for country in params:
            response = requests.get(f"{BASE_URL}/top-headlines/sources?country={country}", headers=headers)
            data.append(response.json())
        return jsonify(data)
        


@app.route('/user/news')
@login_required
def get_news():
    response = requests.get(f"{BASE_URL}/top-headlines?country=us&pagesize=1", headers=headers)
    data = response.json()
    print(data)
    return render_template('/user/news.html')

@app.route('/user/pref')
@login_required
def new_user_prefs():
    preferences = CountryPreferences.query.filter_by(user=g.user.id).all()
    params = []
    for country in preferences:
        params.append(country.country)
    response = requests.get(f"{BASE_URL}/top-headlines/sources", params={"country": params})
    data = response.json()
    return jsonify(data)


@app.route('/submit_prefs', methods=["GET","POST"])
@login_required
def send_to_db():
    form = PreferencesForm()
    if form.is_submitted() and form.validate():
        country_preferences = request.form.getlist('countries[]')
        outlet_preferences = request.form.getlist('outlets[]')
        for country in country_preferences:
            # check if already in list
            if CountryPreferences.query.filter_by(country=country, user=g.user.id).first() is None:
                cpref = CountryPreferences(country=country, user=g.user.id)
                db.session.add(cpref)
        for outlet in outlet_preferences:
            if OutletPreferences.query.filter_by(outlet=outlet, user=g.user.id).first() is None:
                opref = OutletPreferences(user=g.user.id, outlet=outlet)
                db.session.add(opref)
        db.session.commit()
    return redirect('/user_home')