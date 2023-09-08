import os

from flask import Flask, render_template, session, g, flash, redirect, url_for, request, jsonify
from models import connect_db, db, User, CountryPreferences, OutletPreferences
from forms import UserAddForm, LoginForm, PreferencesForm
from functools import wraps
from helpers import signUpNewUser, CURR_USER_KEY, handle_login, do_login
import requests
from config import api_key, supported_countries
import json


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


def do_logout():
    """Logout user."""
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        """Add login-required decorator"""
        if not g.user:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return decorated_function


########## Routes before logging in #########
@app.route('/')
def home():
    """Home landing page for all site visits"""
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login route for signed up users"""
    form = LoginForm()
    if form.is_submitted() and form.validate():
        return handle_login(form)
    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = UserAddForm()
    if form.is_submitted() and form.validate():
        user = signUpNewUser(form)
        do_login(user)
        return redirect("/user/first")
    else:
        return render_template('signup.html', form=form)
    


####### Logged in user views and functions #######

@app.route('/user_home')
@login_required
def go_homepage():
    outlets = OutletPreferences.query.filter_by(user=g.user.id).all()
    home_news_url = f"{BASE_URL}/top-headlines?sources="
    for i in range(len(outlets)):
        if i < len(outlets)-1:
            home_news_url += outlets[i].outlet + ','
        else:
            home_news_url += outlets[i].outlet
        print("+++++++++",home_news_url)
    response = requests.get(f"{home_news_url}&pagesize=50", headers=headers)
    print("+++++++++++++=====", response)
    data = response.json()
    print("++++++++",data)
    return render_template('user/home.html', data=data)


@app.route('/logout')
@login_required
def logout():
    do_logout()
    return redirect('/')

@app.route('/user/first', methods=['GET','POST'])
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
        print("++++++++++++++++",country_preferences)
        outlet_preferences = request.form.getlist('outlets[]')
        print("+++++++++++++++", outlet_preferences)
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
        print("++++ RETURNING REDIRECT +++++")
        return redirect('/user_home')
    return redirect('/user_home')

@app.route('/display_profile')
def show_profile():
    user = User.query.get(g.user.id)
    return render_template('user/profile.html', user = user)