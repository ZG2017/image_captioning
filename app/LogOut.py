from flask import render_template, url_for, request, redirect, session
from app import webapp

# log out a user and return to sign in page
@webapp.route("/logout")
def LogOut():
    session['authenticated'] = False
    session["error"] = None
    session["username"] = None
    session["email"] = None
    return redirect(url_for("SignIn"))