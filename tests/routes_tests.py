import os
from unittest import TestCase
from flask import session
from models import db, User, CountryPreferences
from forms import LoginForm, UserAddForm, PreferencesForm

os.environ['DATABASE_URL'] = "postgresql:///capstone_1_test"


from app import app
from helpers import CURR_USER_KEY, do_login


db.create_all()
app.config['WTF_CSRF_ENABLED'] = False


class UserRoutesTestCase(TestCase):
    """Tests user routes."""
    def setUp(self):
        self.client = app.test_client()
        User.query.delete()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        
        self.not_current_user = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser",
                                    image_url=None)
        
        db.session.commit()

    def tearDown(self):
          db.session.remove()
          db.drop_all()
          db.create_all()

    def test_do_login(self):
        """Test login function"""
        test_user = User.query.filter_by(username='testuser').first()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = test_user.id
            self.assertEqual(sess[CURR_USER_KEY], self.testuser.id)

    def test_handle_login_success(self):
        """Test successful first time logging in"""
        form = LoginForm(username='testuser', password='testuser')
        with self.client as c:
            response = c.post('/login', data=form.data, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(session.get(CURR_USER_KEY), self.testuser.id)
            self.assertIn(b"welcome to courier,", response.data)
            self.assertIn(b"Help us store your preferences", response.data)

    def test_handle_login_failure(self):
        """Test failure logging in"""
        form = LoginForm(username='testuser', password='wrongpassword')
        with self.client as c:
            response = c.post('/login', data=form.data, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertNotEqual(session.get(CURR_USER_KEY), self.testuser.id)
            self.assertIn(b"Invalid credentials", response.data)
            
        
    def test_signup_success(self):
        form = UserAddForm(username='testuser1', email="g@test.com", password='testuser')
        with self.client as c:
            response = c.post('/signup', data=form.data, follow_redirects=True)
            db.session.commit()
            new_user = User.query.filter_by(username='testuser1').first()
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(session.get(CURR_USER_KEY), new_user.id)
            self.assertIn(b"welcome to courier", response.data)
            self.assertIn(b"Help us store your preferences.", response.data)
            self.assertIn(b"Select the countries you'd like to get your news from", response.data)

    def test_signup_failure(self):
        # fails if username is duplicate
        form = UserAddForm(username='testuser', email="unique@unique.com", password='password')
        with self.client as c:
            response = c.post('/signup', data=form.data)
            self.assertEqual(response.status_code, 200)
            self.assertIsNone(session.get(CURR_USER_KEY))
            self.assertIn(b"Username is already taken", response.data)
            db.session.rollback()

        # fails if email is duplicate
        form = UserAddForm(username='unique', email="test@test.com", password='password')
        with self.client as c:
            response=c.post('/signup', data=form.data)
            self.assertEqual(response.status_code, 200)
            self.assertIsNone(session.get(CURR_USER_KEY))
            self.assertIn(b"Email address is already in use", response.data)
            
    def test_user_home(self):
        """Tests the user homepage view."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            # this user has no preferences set, so it should flash a message to set new ones
            response = c.get('/user_home', follow_redirects=True)
            self.assertIn(b"have any preferences for you yet.", response.data)
            self.assertIn(b"welcome to courier,", response.data)

    def test_logout(self):
        """Tests user logout function."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            response = c.get('/logout')
            self.assertIn("welcome to courier", response.data)
            self.assertIn("Login", response.data)
            self.assertIn("Signup", response.data)
            self.assertIsNone(session.get(CURR_USER_KEY))


    def test_user_first_prefs(self):
        """Test user first preferences API call"""
        form_data = {'countries[]': ['ar']}
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            response = c.post('/user/first_prefs', data=form_data)
            self.assertIn(b"ar", response.data)
            

    
    def test_user_prefs(self):
        """Test retrieval of country information"""
        # user has to have country preferences committed to the database
        prefs = CountryPreferences(user=self.testuser.id, country='ar')
        db.session.add(prefs)
        db.session.commit()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            response = c.get('/user/pref')
            self.assertIn(b"ar", response.data)

    
    def test_display_profile(self):
        """Test displaying user home page"""
        with self.client as c:
             with c.session_transaction() as sess:
                  sess[CURR_USER_KEY] = self.testuser.id
             response = c.get('/display_profile')
             self.assertIn(b"testuser", response.data)
                  


            
