import os 
from unittest import TestCase
from models import db, User, CountryPreferences, OutletPreferences
from sqlalchemy.exc import IntegrityError, DataError


os.environ['DATABASE_URL'] = "postgresql:///capstone_1_test"

from app import app

db.create_all()


class UserModelTest(TestCase):
    """Tests user model."""
    
    def setUp(self):
            """Create test client"""
            self.client = app.test_client()

    def tearDown(self):
          db.session.remove()
          db.drop_all()
          db.create_all()

    def test_user_model(self):
        user = User(
            username = 'user1',
            email = 'joe@shmoe.com',
            password = 'pass',
            image_url = 'www.google.com'
        )
        db.session.add(user)
        db.session.commit()

        #user should exist with all data
        u = User.query.get(1)
        self.assertEqual(u.username, "user1")
        self.assertEqual(u.email, "joe@shmoe.com")
        self.assertEqual(u.password, "pass")
        self.assertEqual(u.image_url, "www.google.com")

    def test_default_values_model(self):
        """Test default values on User model"""
        user = User(
            username = 'user1',
            email = 'joeshmoe@gmail.com',
            password = 'pass'
         )
        db.session.add(user)
        db.session.commit()

        u = User.query.get(1)
        self.assertEqual(u.image_url, "/static/generic-user-icon.jpg")

    def test_empty_vals(self):
        """Ensure non-nullable values are not committed to db"""
        # should not add empty username
        # TODO: ensure try/except block FAILS if it is committed to db
        user = User(
             username = '',
             email = 'joe@shmoe.com',
             password = 'hashed_pwd'
        )
        try:
             db.session.add(user)
        except IntegrityError as e:
            db.session.rollback()
            self.assertIn("empty key value violates non-nullable constraint", str(e))

        # should not add empty email
        user = User(
             username = 'joeshmoe',
             email = '',
             password = 'hashed_pwd'
        )
        try:
             db.session.add(user)
        except IntegrityError as e:
            db.session.rollback()
            self.assertIn("empty key value violates non-nullable constraint", str(e))
             
         # should not add empty password
        user = User(
             username = 'joeshmoe',
             email = 'joe@shmoe.com',
             password = ''
        )
        try:
             db.session.add(user)
        except IntegrityError as e:
            db.session.rollback()
            self.assertIn("empty key value violates non-nullable constraint", str(e))

    def test_duplicate_vals(self):
        """Should not commit duplicate values to db"""
        user = User(
             username = 'joeshmoe',
             email = 'joe@shmoe.com',
             password = 'hashed_pwd'
        )     
        db.session.add(user)
        db.session.commit()
        # should not add user when username already exists
        try:
               user2 = User (
                    username = 'joeshmoe',
                    email = 'unique@gmail.com',
                    password = 'hashed_pwd'
               )
               db.session.add(user2)
               db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            self.assertIn("duplicate key value violates unique constraint", str(e))

        # should not add user when email already exists
        user2 = User (
            username = 'unique',
            email = 'joe@shmoe.com',
            password = 'hashed_pwd'
        )
        try:
             db.session.add(user2)
             db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            self.assertIn("duplicate key value violates unique constraint", str(e))
        
        # password should not matter if all else is equal
        user2 = User(
            username = 'joeshmoe_unique',
            email = 'unique_joe_shmoe@gmail.com',
            password = 'hashed_pwd'
        )
        db.session.add(user2)
        db.session.commit()
        u = User.query.filter_by(username='joeshmoe_unique').first()
        self.assertEqual(u.password, "hashed_pwd")

        
    def test_signup_method(self):
         """Test the signup class method on the user model."""
         new_user = User.signup(
              username = 'joeyshmoey',
              email = 'josephshmoseph@gmail.com',
              password = 'this_will_be_hashed',
              image_url = 'www.google.com'
         )
         self.assertEqual(f"{new_user}", f"<User #{new_user.id}: {new_user.username}, {new_user.email}>")
         db.session.commit()
        
        #this should test signup function to ensure info sent to db, 
        # and it should test that passwords are saved as hashed versions
         user = User.query.get(1)
         self.assertEqual(user.email, "josephshmoseph@gmail.com")
         self.assertEqual(user.username, "joeyshmoey")
         self.assertNotIn(user.password, "this_will_be_hashed")
         self.assertEqual(user.image_url, "www.google.com")

    def test_authenticate_method(self):
         """Test the authenticate method"""
         user = User.signup(
            username = 'user1',
            email = 'joe@shmoe.com',
            password = 'pass',
            image_url = 'www.google.com'
        )
         db.session.commit()

         auth_user = User.authenticate("user1", "pass")
         self.assertEqual(f'{auth_user}', f"<User #{auth_user.id}: {auth_user.username}, {auth_user.email}>")
         

         false_username = User.authenticate('user2', "pass")
         false_password = User.authenticate('user1', "passs")

         self.assertFalse(false_password)
         self.assertFalse(false_username)


class StoryModelTest(TestCase):
    """Tests story model. Currently there is no functionality to store the story to the db; can add later if time"""

    def setUp(self):
            """Create test client, add sample data."""
            User.query.delete()
            self.client = app.test_client()

class CountryPreferencesTest(TestCase):
     """Tests country preferences model."""
     def setUp(self):
            """Create test client, add sample data."""
            self.client = app.test_client()
            
     def tearDown(self):
          db.session.remove()
          db.drop_all()
          db.create_all()

     def test_country_prefs_model(self):
          """Should not work without user present"""
          try:
               country_prefs = CountryPreferences(
                    user = 1,
                    country = "USA"
               )
               db.session.add(country_prefs)
               db.session.commit()
          except IntegrityError as e: 
               db.session.rollback()
               self.assertIn("Key (user)=(1) is not present in table", str(e))
          
          # when the above fails, add countrypref when a user is in db
          user = User(
            username = 'user1',
            email = 'joe@shmoe.com',
            password = 'pass',
            image_url = 'www.google.com'
          )
          db.session.add(user)
          db.session.commit()

          country_prefs = CountryPreferences(
                    user = 1,
                    country = "USA"
               )
          db.session.add(country_prefs)
          db.session.commit()

          country_prefs = CountryPreferences.query.filter_by(user=1).first()

          self.assertIn(country_prefs.country, "USA")
     
     def test_delete_user_prefs(self):
          """Can delete a user's preferences"""
          user = User(
            username = 'user1',
            email = 'joe@shmoe.com',
            password = 'pass',
            image_url = 'www.google.com'
          )
          db.session.add(user)
          db.session.commit()

          country_prefs = CountryPreferences(
                    user = 1,
                    country = "USA"
               )
          db.session.add(country_prefs)
          db.session.commit()

          pref = CountryPreferences.query.filter_by(user=1).first()

          db.session.delete(pref)
          db.session.commit()

          pref = CountryPreferences.query.filter_by(user=1).first()
          self.assertIsNone(pref)


class TestOutletPreferences(TestCase):
     """Tests media preferences model."""

     def setUp(self):
            """Create test client, add sample data."""
            self.client = app.test_client()
            
     def tearDown(self):
          db.session.remove()
          db.drop_all()
          db.create_all()

     def test_outlet_prefs(self):
          user = User.signup(
            username = 'user1',
            email = 'joe@shmoe.com',
            password = 'pass',
            image_url = 'www.google.com'
        )
          db.session.add(user)
          db.session.commit()

          user = User.query.filter_by(username='user1').first()
          
          outletpref = OutletPreferences(
               user = user.id,
               outlet = "outlet",
               outlet_id = "abc"
          )

          db.session.add(outletpref)
          db.session.commit()

          outletpref = OutletPreferences.query.filter_by(outlet="outlet").first()
          
          self.assertEqual(outletpref.user, user.id)
          self.assertEqual(outletpref.outlet, "outlet")
          self.assertEqual(outletpref.outlet_id, "abc")
     
    
