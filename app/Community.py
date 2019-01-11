from flask import render_template, url_for, request, redirect, session
from werkzeug.utils import secure_filename
from app import webapp
import os
from app import dynamodb
from app import config
import urllib

# community page
@webapp.route('/community/<string:searchName>', methods = ['GET','POST'])
def community(searchName):
    if searchName == ' ':
        images = dynamodb.get_all_pub_image()
    else:
        images = dynamodb.search_all_by_imagename(searchName)
    session['search'] = searchName
    #final_results = []
    for i in range(len(images)):
        ratingInfo = dynamodb.get_rating_information(images[i]['userName'], images[i]['uploadTime'])
        images[i]['text'] = [i for i in urllib.request.urlopen(images[i]['textPath'])][0].decode("utf-8")
        images[i]['allNumber'] = ratingInfo[1]
        images[i]['5Number'] = ratingInfo[0][5]
        images[i]['4Number'] = ratingInfo[0][4]
        images[i]['3Number'] = ratingInfo[0][3]
        images[i]['2Number'] = ratingInfo[0][2]
        images[i]['1Number'] = ratingInfo[0][1]
    return render_template('community.html', images = images, userName = session['username'])

# sort by time
@webapp.route('/community/sort_by_time', methods = ['GET'])
def community_sort_by_time():
    if session['search'] == ' ':
        images = dynamodb.get_all_pub_image()
    else:
        images = dynamodb.search_all_by_imagename(session['search'])
    
    #final_results = []
    for i in range(len(images)):
        ratingInfo = dynamodb.get_rating_information(images[i]['userName'], images[i]['uploadTime'])
        images[i]['text'] = [i for i in urllib.request.urlopen(images[i]['textPath'])][0].decode("utf-8")
        images[i]['allNumber'] = ratingInfo[1]
        images[i]['5Number'] = ratingInfo[0][5]
        images[i]['4Number'] = ratingInfo[0][4]
        images[i]['3Number'] = ratingInfo[0][3]
        images[i]['2Number'] = ratingInfo[0][2]
        images[i]['1Number'] = ratingInfo[0][1]
    return render_template('community.html', images = images, userName = session['username'])


# sort by rate
@webapp.route('/community/sort_by_rate', methods = ['GET'])
def community_sort_by_rate():
    if session['search'] == ' ':
        images = dynamodb.get_all_pub_image()
    else:
        images = dynamodb.search_all_by_imagename(session['search'])
    for i in range(len(images)):
        ratingInfo = dynamodb.get_rating_information(images[i]['userName'], images[i]['uploadTime'])
        images[i]['text'] = [i for i in urllib.request.urlopen(images[i]['textPath'])][0].decode("utf-8")
        images[i]['allNumber'] = ratingInfo[1]
        images[i]['5Number'] = ratingInfo[0][5]
        images[i]['4Number'] = ratingInfo[0][4]
        images[i]['3Number'] = ratingInfo[0][3]
        images[i]['2Number'] = ratingInfo[0][2]
        images[i]['1Number'] = ratingInfo[0][1]
    images = sorted(images, reverse = True, key = lambda x:x['averRating'])
    return render_template('community.html', images = images, userName = session['username'])


# search bar
@webapp.route('/search_submit', methods = ['GET','POST'])
def image_search():
    if request.form['search']:
        session['search'] = request.form['search']
    print(session['search'])
    return redirect(url_for('community', searchName = session['search']))


# rating one image
@webapp.route('/rating_submit/<string:userName>/<string:uploadTime>/', methods = ['POST','GET'])
def image_rating(userName,uploadTime):
    print(request.form['rating'])
    currentUserName = session['username']
    rating = int(request.form['rating'])
    dynamodb.update_rating_item(userName,uploadTime,currentUserName,rating)
    return redirect(url_for('community', searchName = session['search']))


# go to user homepage 
@webapp.route('/userHomePage', methods = ['GET'])
def go_to_user_homepage():
    return redirect(url_for('user_homepage', userName = session['username']))