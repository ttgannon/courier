import os

from flask import Flask, render_template, session, g, flash, redirect, url_for, request, jsonify
from models import connect_db, db, User, CountryPreferences, OutletPreferences
from forms import UserAddForm, LoginForm, PreferencesForm
from functools import wraps
from helpers import signUpNewUser, CURR_USER_KEY, handle_login, do_login
import requests
from config import supported_countries, categories
from api_key import api_key


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
        if isinstance(user, str):
            return render_template("signup.html", form=form)
        do_login(user)
        return redirect("/user/first")
    else:
        return render_template('signup.html', form=form)
    


####### Logged in user views and functions #######
@app.route('/user_home')
@login_required
def go_homepage():
    outlets = OutletPreferences.query.filter_by(user=g.user.id).all()
    if len(outlets) != 0:
        home_news_url = f"{BASE_URL}/top-headlines?sources="
        for i in range(len(outlets)):
            if i < len(outlets)-1:
                home_news_url += outlets[i].outlet + ','
            else:
                home_news_url += outlets[i].outlet
        response = requests.get(f"{home_news_url}&pagesize=50", headers=headers)
        data = response.json()
        return render_template('user/home.html', data=data)
    flash("We don't have any preferences for you yet. Set some here.")
    return redirect ('/user/first')

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
def update_preferences():
    form = PreferencesForm()
    # deletes all user prefs in db and readds all the ones present in country list
    if form.is_submitted() and form.validate():
        country_preferences = request.form.getlist('countries[]')
        outlet_preferences = request.form.getlist('outlets[]')
        country_prefs_db = CountryPreferences.query.filter_by(user=g.user.id).all()
        outlet_prefs_db = OutletPreferences.query.filter_by(user=g.user.id).all()
        
        # Delete user preferences from the db;
        if len(country_preferences) > 0:
            for country in country_prefs_db:
                db.session.delete(country)
            for outlet in outlet_prefs_db:
                db.session.delete(outlet)
        
            #Instate users preferences from form data into db; 
            for country in country_preferences:
                cpref = CountryPreferences(country=country, user=g.user.id)
                db.session.add(cpref)
            for outlet in outlet_preferences:
                opref = OutletPreferences(user=g.user.id, outlet=outlet)
                db.session.add(opref)
            
            db.session.commit()
        else:
            flash("Your preferences have been saved, but you didn't select any outlets. We are showing top US headlines.")
            return redirect('/user_home')
        return redirect('/user_home')
    return redirect('/user_home')


@app.route('/display_profile')
def show_profile():
    user = User.query.get(g.user.id)
    return render_template('user/profile.html', user = user)


@app.route('/user/manage_prefs', methods=['GET','POST'])
@login_required
def manage_preferences():
    """Allow user to update preferences for their user experience."""
    country_prefs = CountryPreferences.query.filter_by(user=g.user.id).all()
    user = User.query.get(g.user.id)
    form1 = PreferencesForm()
    form2 = PreferencesForm()
    for preference in country_prefs:
        form1.countries.append_entry({'name': preference.country})
    return render_template('/user/manage_prefs.html', user=user, countries=supported_countries, form1=form1, form2=form2)


@app.route('/discover', methods=['GET','POST'])
@login_required
def discover_news():
    """Open Discover page, and allow user to discover news sources and articles based on categories."""
    form = PreferencesForm()
    if request.method == 'GET':
        return render_template('user/discover.html', countries=supported_countries, categories=categories, form=form)
    else:
        data = request.json.get('articles')
        return render_template('/user/discover.html', data=data, form=form, categories=categories)
    
@app.route('/interact_with_api', methods=['GET','POST'])
@login_required
def interact_with_api():
    category = request.args.get('category')
    country = request.args.get('country')
    response = requests.get(f'{BASE_URL}/top-headlines?country={country}&category={category}', headers=headers)
    data = response.json()
    return data