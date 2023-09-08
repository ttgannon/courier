from models import User, db
from flask import flash, render_template, redirect, session
from sqlalchemy.exc import IntegrityError

CURR_USER_KEY = "curr_user"


def signUpNewUser(form):
    try:
        user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data,
            )
        db.session.commit()
    except IntegrityError as e:
        error_info = str(e.orig)
        if "unique constraint" in error_info.lower():
            if "username" in error_info.lower():
                flash("Username is already taken.", 'danger')
            elif "email" in error_info.lower():
                flash("Email address is already in use.", 'danger')
        else:
            flash("An integrity error occurred.", 'danger')
        return render_template('signup.html', form=form)
    return user


def handle_login(form):
    user = User.authenticate(form.username.data, form.password.data)
    if user:
        do_login(user)
        flash(f"Hello, {user.username}!", "success")
        return redirect("/user_home")
    else:
        flash("Invalid credentials.", 'danger')
        return redirect('/login')


def do_login(user):
    """Log in user."""
    session[CURR_USER_KEY] = user.id