import os
import numpy as np
from vocabulary import Vocabulary

import torch
from torchvision import transforms
from model import EncoderCNN, DecoderRNN
from utils import clean_sentence, get_prediction
from torch.autograd import Variable

from PIL import Image

from flask import render_template, redirect, url_for, request, g, session
from app import webapp
from watson_developer_cloud import TextToSpeechV1
import json
import time
from flask import make_response
import requests
from io import BytesIO
import urllib

from app import dynamodb
from app import config
from app import s3


def model_loader(model_path,
                 vocab_threshold=None,
                 vocab_file="./vocab.pkl",
                 start_word="<start>",
                 end_word="<end>",
                 unk_word="<unk>",
                 annotations_file="./cocoapi/annotations/image_info_train2014.json",
                 vocab_from_file=True):
    # Load the most recent checkpoint
    model = torch.load(model_path, map_location=lambda storage, loc: storage)
    # Get the vocabulary and its size
    vocab = Vocabulary(vocab_threshold, vocab_file, start_word,
                    end_word, unk_word, annotations_file, vocab_from_file)
    vocab_size = len(vocab)
    # Initialize the encoder and decoder, and set each to inference mode
    encoder = EncoderCNN(embed_size=256)
    encoder.eval()
    decoder = DecoderRNN(embed_size=256, hidden_size=512, vocab_size=vocab_size)
    decoder.eval()

    # Load the pre-trained weights
    encoder.load_state_dict(model['encoder'])
    decoder.load_state_dict(model['decoder'])

    # Move models to GPU if CUDA is available.
    if torch.cuda.is_available():
        encoder.cuda()
        decoder.cuda()
    return encoder, decoder, vocab

transform_sample = transforms.Compose([
    transforms.Resize(256),                          # smaller edge of image resized to 256
    transforms.CenterCrop(224),                      # get 224x224 crop from the center
    transforms.ToTensor(),                           # convert the PIL Image to a tensor
    transforms.Normalize((0.485, 0.456, 0.406),      # normalize image for pre-trained model
                         (0.229, 0.224, 0.225))])



encoder, decoder, vocab = model_loader('./models/best-model.pkl')
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','TXT','PDF','PNG','JPG','JPEG','GIF'])



def sample_loader(source_path,
                  transform=transform_sample):
    """Return the preprocessed sample image.
    Parameters:
        source_path: Image path
        transform: Image transform.
    """
    response = requests.get(source_path)
    source_image = Image.open(BytesIO(response.content)).convert("RGB")
    orig_image = torch.from_numpy(np.array(source_image)).unsqueeze_(0)
    image = transform(source_image).unsqueeze_(0)
    if torch.cuda.is_available():
        image = image.cuda()

    return orig_image, image


def sentence_generator(image, encoder, decoder, vocab):
    # Obtain the embedded image features.
    features = encoder(image).unsqueeze(1)

    print ("Caption without beam search:")

    # Pass the embedded image features through the model to get a predicted caption.
    output = decoder.sample(features)

    # print('example output:', output)
    sentence_no_beam = clean_sentence(output, vocab)

    print("Top captions using beam search:")
    outputs = decoder.sample_beam_search(features)

    # Print maximum the top 3 predictions
    num_sents = min(len(outputs), 3)
    sentence_beam = []
    for output in outputs[:num_sents]:
        sentence = clean_sentence(output, vocab)
        sentence_beam.append(sentence)
        print(sentence)
    return sentence_beam[0]


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS


#  text to speech processing
def text2Speech(localFilePath, bucketPath, message):
    # user watson api to transfer the text to speech
    text_to_speech = TextToSpeechV1(
        url='**************************************',
        iam_apikey='***************************************'
    )  
    
    # save to s3
    with open(localFilePath, 'wb') as audio_file:
        audio_file.write(text_to_speech.synthesize(message[:-1], accept='audio/wav',voice="en-US_AllisonVoice").get_result().content)
    s3.upload_to_s3(localFilePath, config.S3_BUCKETNAME, bucketPath, acl="public-read")
    os.remove(localFilePath)


@webapp.route('/homepage/<userName>')
# @webapp.route('/index',methods=['GET'])
# @webapp.route('/welcome',methods=['GET'])
# Display an HTML page with links
def user_homepage(userName):
    images = dynamodb.get_all_image_by_user(userName)
    #tmp_results.sort(reverse = True, key = lambda x:x['uploadTime'])
    for i in range(len(images)):
        ratingInfo = dynamodb.get_rating_information(session['username'],images[i]['uploadTime'])
        images[i]['text'] = [i for i in urllib.request.urlopen(images[i]['textPath'])][0].decode("utf-8")
        images[i]['allNumber'] = ratingInfo[1]
        images[i]['5Number'] = ratingInfo[0][5]
        images[i]['4Number'] = ratingInfo[0][4]
        images[i]['3Number'] = ratingInfo[0][3]
        images[i]['2Number'] = ratingInfo[0][2]
        images[i]['1Number'] = ratingInfo[0][1]

    return render_template("homepage.html", images = images, userName = session['username'])


# sort by time
@webapp.route('/homepage/sort_by_time', methods = ['GET'])
def homepage_sort_by_time():
    images = dynamodb.get_all_image_by_user(session['username'])
    for i in range(len(images)):
        ratingInfo = dynamodb.get_rating_information(session['username'],images[i]['uploadTime'])
        images[i]['text'] = [i for i in urllib.request.urlopen(images[i]['textPath'])][0].decode("utf-8")
        images[i]['allNumber'] = ratingInfo[1]
        images[i]['5Number'] = ratingInfo[0][5]
        images[i]['4Number'] = ratingInfo[0][4]
        images[i]['3Number'] = ratingInfo[0][3]
        images[i]['2Number'] = ratingInfo[0][2]
        images[i]['1Number'] = ratingInfo[0][1]
    return render_template('homepage.html', images = images, userName = session['username'])



# sort by rate
@webapp.route('/homepage/sort_by_rate', methods = ['GET'])
def homepage_sort_by_rate():
    images = dynamodb.get_all_image_by_user(session['username'])
    for i in range(len(images)):
        ratingInfo = dynamodb.get_rating_information(session['username'],images[i]['uploadTime'])
        images[i]['text'] = [i for i in urllib.request.urlopen(images[i]['textPath'])][0].decode("utf-8")
        images[i]['allNumber'] = ratingInfo[1]
        images[i]['5Number'] = ratingInfo[0][5]
        images[i]['4Number'] = ratingInfo[0][4]
        images[i]['3Number'] = ratingInfo[0][3]
        images[i]['2Number'] = ratingInfo[0][2]
        images[i]['1Number'] = ratingInfo[0][1]
    images = sorted(images,reverse = True, key = lambda x:x['averRating'])
    return render_template('homepage.html', images = images, userName = session['username'])
    

@webapp.route('/homepage/to_upload', methods = ['GET','POST'])
def go_to_upload():
    return redirect(url_for('upload',uploadTime=' '))

@webapp.route('/homepage/upload/<string:uploadTime>', methods = ['GET','POST'])
def upload(uploadTime):
    imagePath = None
    audioPath = None
    text = None
    rating = None
    if uploadTime != ' ':
        image = dynamodb.get_image_item(session['username'],uploadTime)
        imagePath = image['imagePath']
        audioPath = image['audioPath']
        text = [i for i in urllib.request.urlopen(image['textPath'])][0].decode("utf-8")
        rating = image['myRating']
    return render_template('upload.html',userName = session['username'], uploadTime = uploadTime, imagePath = imagePath, audioPath = audioPath, text = text)

@webapp.route('/camera', methods=['GET', 'POST'])
def camera():

    return render_template("camera.html")


@webapp.route('/snapshot', methods=['GET', 'POST'])
def snapshot():

    return redirect(url_for("camera.html"))

@webapp.route('/homepage/upload_file',methods=['GET','POST'])
def upload_submit():

    if request.method=='POST' and 'file' in request.files:
        file=request.files['file']
        # name = request.form['formname']
        # print(name)
        # error=False
    else:
        return redirect(url_for('upload', uploadTime=' '))
    
    # create the folder on S3
    cur_time = str(time.time()).split('.')[0]
    file_path = os.path.join(session['username'],cur_time)
    s3.create_file(file_path+'/')

    # generate dir form files and save the image file
    if file and allowed_file(file.filename):
        imageFileName = file.filename
    
    PureImageName = ".".join(imageFileName.split('.')[:-1])

    # generate file path within the bucket
    imagePathInBucket = '%s/%s'%(file_path, imageFileName)
    audioPathInBucket = '%s/%s'%(file_path, 'audio.wav')
    textPathInBucket = '%s/%s'%(file_path, 'text.txt')

    # generate S3 paths for this set of file
    imagePath = os.path.join(config.S3_ADDRESS, imagePathInBucket)
    audioPath = os.path.join(config.S3_ADDRESS, audioPathInBucket)
    textPath = os.path.join(config.S3_ADDRESS, textPathInBucket)

    # generate tmep local path
    local_cur_path = os.path.dirname(__file__)
    localImagePath = os.path.join(local_cur_path, imageFileName)
    localAudioPath = os.path.join(local_cur_path,'audio.wav')
    localTextPath = os.path.join(local_cur_path,'text.txt')

    # save image to S3 bucket and load image
    file.save(localImagePath)
    s3.upload_to_s3(localImagePath, config.S3_BUCKETNAME, imagePathInBucket, acl="public-read")
    os.remove(localImagePath)
    
    # load the image from S3
    _,image = sample_loader(imagePath)

    # generate and save the text result
    result = sentence_generator(image, encoder, decoder, vocab)
    with open(localTextPath,'w') as myfile:
        myfile.write(result)
    s3.upload_to_s3(localTextPath,config.S3_BUCKETNAME, textPathInBucket, acl="public-read")
    os.remove(localTextPath)

    # save info to dynamodb
    dynamodb.put_image_item(session['username'], cur_time, PureImageName, imagePath, audioPath, textPath, 0, 0, 'public')
    
    # text to speech and save audio to S3
    text2Speech(localAudioPath, audioPathInBucket, result)

    # put the rating into rating table
    # dynamodb.update_rating_item(session['username'],cur_time,session['username'],0)
    
    return redirect(url_for('upload',uploadTime = cur_time))


# rating one image
@webapp.route('/rating_submit/<string:info>', methods = ['POST','GET'])
def image_rating_homepage(info):
    userName = session['username']
    uploadTime = info
    currentUserName = session['username']
    rating = request.form['rating']
    dynamodb.update_rating_item(userName,uploadTime,currentUserName,rating)
    return redirect(url_for('user_homepage', userName = session['username']))


# rating just uploaded image
@webapp.route('/homepage/upload/rating_submit/<string:uploadTime>', methods = ['POST','GET'])
def image_rating_upload(uploadTime):
    imagePath = None
    audioPath = None
    text = None
    rating = None
    if uploadTime != ' ':
        image = dynamodb.get_image_item(session['username'],uploadTime)
        imagePath = image['imagePath']
        audioPath = image['audioPath']
        text = [i for i in urllib.request.urlopen(image['textPath'])][0].decode("utf-8")
        rating = image['myRating']
    rating = request.form['rating']
    userName = session['username']
    currentUserName = session['username']
    dynamodb.update_rating_item(userName ,uploadTime, currentUserName, rating)
    return redirect(url_for('upload', uploadTime = uploadTime))
