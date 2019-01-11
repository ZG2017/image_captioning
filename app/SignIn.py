from flask import render_template, session, url_for, request, redirect
from app import webapp
from app import dynamodb
import hashlib
import base64
import os

# add salt and hash the password
def Pwd2Hash(password,salt=None):
    password = password.encode()
    if not salt:
        salt = base64.b64encode(os.urandom(32))
    else:
        salt = salt.encode()
    hashInput = hashlib.sha256(salt+password).hexdigest()
    return hashInput,salt

# show signin page
@webapp.route("/",methods=['GET','POST'])
@webapp.route("/index",methods=['GET','POST'])
def SignIn():
    username = None
    error = None
    if "username" in session:
        username = session["username"]
    if "resubmit" in session and session["resubmit"]:
        if "error" in session:
            error = session["error"]
            session["error"] = None

    session["resubmit"] = False
    return render_template("signin.html", username = username, error=error)

# check if input info are valid and add login to homepage if it is 
@webapp.route("/signin_submit",methods=['GET','POST'])
def SignInSubmit():
    user_name = request.form["username"]
    userInfo = dynamodb.get_user(user_name)
    #print(type(userInfo["userSalt"]))
    if not userInfo:
        session["resubmit"] = True
        session["error"] = "username don't exsist!"
        return redirect(url_for("SignIn"))

    if "username" in request.form and request.form["username"] == userInfo["userName"] and "password" in request.form and Pwd2Hash(request.form["password"],userInfo["userSalt"])[0] == userInfo["userPassword"]:
        session['authenticated'] = True
        session["username"] = request.form["username"]
        session["error"] = None
        return redirect(url_for("community",searchName = " "))
    
    if 'username' in request.form:
        session["username"] = request.form["username"]

    session["resubmit"] = True
    session["error"] = "username or password incorrect!"
    return redirect(url_for("SignIn"))
