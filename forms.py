from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, FieldList, FormField, Form, IntegerField
from wtforms.validators import DataRequired, Email, Length
from config import supported_countries


class UserAddForm(FlaskForm):
    """Form for adding users."""
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6), DataRequired()])
    image_url = StringField('Profile Picture URL')
    header_image_url = StringField('Header Image URL')


class LoginForm(FlaskForm):
    """Login form."""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])


class CountryForm(Form):
    name = StringField('Name')

class PreferencesForm(FlaskForm):
    """Form for news users to establish their country preferences."""
    countries = FieldList(FormField(CountryForm), min_entries=1)