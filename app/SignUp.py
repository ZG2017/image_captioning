from flask import render_template, url_for, request, redirect, session,g
from app import webapp
from app import dynamodb
import hashlib
import base64
import os
from app import config
import boto3

# add salt and hash the password
def Pwd2Hash(password,salt=None):
    password = password.encode()
    if not salt:
        salt = base64.b64encode(os.urandom(32))
    hashInput = hashlib.sha256(salt+password).hexdigest()
    salt = salt.decode()
    return hashInput,salt

# show signup page
@webapp.route("/signup", methods = ["GET","POST"])
def SignUp():
    username = None
    error = None
    email = None  
    if "username" in session:
        username = session["username"]
    if "error" in session:
        error = session["error"]
    if "email" in session:
        email = session["email"]
    return render_template("signup.html", email = email, error = error, username = username)

# check if user info are valid and submit the info 
@webapp.route("/signup_submit",methods = ["POST"])
def SignUpSubmit():
    error = ""
    # check if name is valid
    if "username" in request.form:
        if request.form["username"] == "":
            error += "Please enter a username.\n"
        elif len(request.form["username"]) > 20:
            error += "The username is too long. Please retry.\n"
        for char in request.form["username"]:
            if char not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_":
                error += "Username should only contain letters, numbers and '_'.\n"
                break
    

    # check if name already exsist
    userdata = dynamodb.get_user(request.form["username"])
    if not userdata:
        session["username"] = request.form["username"]
    else:
        session["error"] = "Username has been taken. Please choose another name!\n"
        return redirect(url_for("SignUp"))

    # check if email is entered or taken
    if "email" in request.form:
        if request.form["email"] == "":
            error += "Please enter the email address.\n"

    userdata = dynamodb.get_item_by_email(request.form["email"])
    if not userdata:
        session["email"] = request.form["email"]
    else:
        session["error"] = "Email address has been taken. Please choose another!\n"
        return redirect(url_for("SignUp"))
    session["email"] = request.form["email"]
    
    # check if password are match
    if "password" in request.form and "com_password" in request.form:
        if request.form["password"] == "" or request.form["com_password"] == "":
            error += "Please enter the password or password comfirm.\n"
        elif request.form["password"] != request.form["com_password"]:
            error += "password doesn't match the comfirm password.\n"
    
    if error != "":
        session["error"] = error
        return redirect(url_for("SignUp"))
    else:
        session['authenticated'] = True
        
    # save userinfo
    pwd,salt = Pwd2Hash(request.form["password"], salt = None)

    dynamodb.put_user(request.form["username"],request.form["email"],pwd,salt)
    create_file(session["username"]+'/')
    session["error"] = None
    return redirect(url_for("community", searchName = " "))

def create_file(username):
    s3_client = boto3.client('s3',**config.aws_connection_args)
    try:
        response = s3_client.put_object(Bucket=config.S3_BUCKETNAME, Key=username)
    except Exception as e:
        print("create fail")
        return e
    
