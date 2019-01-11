import boto3
import json
from boto3.dynamodb.conditions import Key, Attr
import time

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')


# put rating to one imageInfo table
def update_rating_item(
        userName,
        uploadTime,
        currentUserName,
        rating):
    imageId = userName+'_'+uploadTime
    ratingTable = dynamodb.Table("ratingTable")
    user2ImageTable = dynamodb.Table('user2Image')

    # update rating information
    response1 = ratingTable.update_item(
       Key={
            'imageId': imageId,
            'ratingUser': currentUserName,
        },
        UpdateExpression = "set rating = :r",
        ExpressionAttributeValues = {
           ':r': rating,
        }
    )

    # get all rating data of this image from rating table
    response2 = ratingTable.scan(
        FilterExpression = Key('imageId').eq(imageId),
        ProjectionExpression='rating',
    )

    records = []
    for i in response2['Items']:
        records.append(i['rating'])

    while 'LastEvaluatedKey' in response2:
        response = ratingTable.scan(
            FilterExpression = Key('imageId').eq(imageId),
            ProjectionExpression='rating',
            ExclusiveStartKey=response2['LastEvaluatedKey']
            )

        for i in response['Items']:
            records.append(i['rating'])
    
    # update average rating for this image in user2Image table
    # if: user are rating his/her own image, then also update 'myRating'
    # else: just update averRating 
    if userName == currentUserName:
        response3 = user2ImageTable.update_item(
            Key={
                'userName': userName,
                'uploadTime': uploadTime
            },
            UpdateExpression = "set averRating = :r, myRating = :mr",
            ExpressionAttributeValues = {
            ':r' : sum(records)/len(records),
            ':mr' : rating,
            }
        )
    else: 
        response3 = user2ImageTable.update_item(
            Key={
                'userName': userName,
                'uploadTime': uploadTime
            },
            UpdateExpression = "set averRating = :r",
            ExpressionAttributeValues = {
            ':r': sum(records)/len(records),
            }
        )


"""
# create table to store the rating for each image
def create_rating_table(userName,
                        uploadTime):
    tableName = userName+'_'+uploadTime+'_'+'Info'
    table = dynamodb.create_table(
        TableName=tableName,
        KeySchema=[
            {
                'AttributeName': 'userName',
                'KeyType': 'HASH'  #Partition key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'userName',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )
    #time.sleep(15)


# put rating to one imageInfo table
def update_rating_item(
        userName,
        uploadTime,
        currentUserName,
        rating):
    tableName = userName+'_'+uploadTime+'_'+'Info'
    ratingTable = dynamodb.Table(tableName)
    user2ImageTable = dynamodb.Table('user2Image')

    # update rating information
    response1 = ratingTable.update_item(
       Key={
            'userName': currentUserName
        },
        UpdateExpression = "set rating = :r",
        ExpressionAttributeValues = {
           ':r': rating,
        }
    )

    # get all rating data of this image from rating table
    response2 = ratingTable.scan(
        ProjectionExpression='rating',
    )

    records = []
    for i in response2['Items']:
        records.append(i['rating'])

    while 'LastEvaluatedKey' in response2:
        response = ratingTable.scan(
            ProjectionExpression='rating',
            ExclusiveStartKey=response2['LastEvaluatedKey']
            )

        for i in response['Items']:
            records.append(i['rating'])
    
    # update average rating for this image in user2Image table
    # if: user are rating his/her own image, then also update 'myRating'
    # else: just update averRating 
    if userName == currentUserName:
        response3 = user2ImageTable.update_item(
            Key={
                'userName': userName,
                'uploadTime': uploadTime
            },
            UpdateExpression = "set averRating = :r, myRating = :mr",
            ExpressionAttributeValues = {
            ':r' : sum(records)/len(records),
            ':mr' : rating,
            }
        )
    else: 
        response3 = user2ImageTable.update_item(
            Key={
                'userName': userName,
                'uploadTime': uploadTime
            },
            UpdateExpression = "set averRating = :r",
            ExpressionAttributeValues = {
            ':r': sum(records)/len(records),
            }
        )
"""


# get rating information
def get_rating_information(
        userName,
        uploadTime):
    total = 0
    saver = {}
    saver[0] = 0
    saver[1] = 0
    saver[2] = 0
    saver[3] = 0
    saver[4] = 0
    saver[5] = 0
    imageId = userName+'_'+uploadTime
    table = dynamodb.Table("ratingTable")
    response = table.scan(
        FilterExpression = Key('imageId').eq(imageId),
        ProjectionExpression = "rating",
    )
    for i in response['Items']:
        saver[i['rating']] += 1
        total += 1

    while 'LastEvaluatedKey' in response:
        response = table.scan(
            ProjectionExpression = "rating",
            )

        for i in response['Items']:
            saver[i['rating']] += 1
            total += 1
    
    return saver, total



# put record tp userInfo table
def put_user(userName,
             userEmail,
             userPassword,
             userSalt):
    table = dynamodb.Table('userInfo')
    response = table.put_item(
       Item={
            'userName': userName,
            'userEmail': userEmail,
            'userPassword': userPassword,
            'userSalt': userSalt,
        }
    )

# get record from userInfo table
def get_user(userName):
    table = dynamodb.Table('userInfo')
    response = table.get_item(
       Key={
            'userName': userName
        },
        ProjectionExpression = "userName, userEmail, userPassword, userSalt",
    )

    data = {}

    if 'Item' in response:
        item = response['Item']
        data.update(item)
    
    return data


# get record from userInfo table by email address
def get_item_by_email(userEmail):
    table = dynamodb.Table('userInfo')
    response = table.scan(
        FilterExpression = Attr('userEmail').eq(userEmail),
        ProjectionExpression = "userName, userEmail, userPassword, userSalt",
    )

    records = []

    for i in response['Items']:
        records.append(i)

    while 'LastEvaluatedKey' in response:
        response = table.scan(
            FilterExpression = Attr('userEmail').eq(userEmail),
            ProjectionExpression = "userName, userEmail, userPassword, userSalt",
            ExclusiveStartKey=response['LastEvaluatedKey']
            )

        for i in response['Items']:
            records.append(i)
    
    return records

# put record to user2Image table
def put_image_item(userName,
                   uploadTime,
                   imageName,
                   imagePath,
                   audioPath,
                   textPath,
                   averRating,
                   myRating,
                   pubPriv):
    table = dynamodb.Table('user2Image')
    response = table.put_item(
       Item={
            'userName': userName,
            'uploadTime': uploadTime,
            'imageName': imageName,
            'imagePath': imagePath,
            'audioPath': audioPath,
            'textPath': textPath,
            'averRating': averRating,
            'myRating': myRating,
            'pubPriv': pubPriv,
        }
    )


# get record from user2Image table
def get_image_item(userName,
                   uploadTime):
    table = dynamodb.Table('user2Image')
    response = table.get_item(
       Key={
            'userName': userName,
            'uploadTime': uploadTime
        },
        ProjectionExpression = "imageName, imagePath, audioPath, textPath, myRating, averRating",
    )

    data = {}

    if 'Item' in response:
        item = response['Item']
        data.update(item)
    
    return data


# get record from user2Image table per user
def get_all_image_by_user(userName):
    table = dynamodb.Table('user2Image')
    response = table.query(
        KeyConditionExpression = Key('userName').eq(userName),
        ProjectionExpression = 'userName, uploadTime, imageName, imagePath, audioPath, textPath, averRating, myRating, pubPriv',
        ScanIndexForward = False,
    )

    records = []

    if 'Items' in response:
        for i in response['Items']:
            records.append(i)

    return records
    

# search all records from user2Image table
def search_all_by_imagename(imageName):
    table = dynamodb.Table('user2Image')
    response = table.query(
        IndexName = 'imageName-uploadTime-index',
        KeyConditionExpression = Key('imageName').eq(imageName),
        ProjectionExpression ='userName, imageName, uploadTime, imagePath, audioPath, textPath, averRating, pubPriv',
        ScanIndexForward = False,
        )

    records = []

    if 'Items' in response:
        for i in response['Items']:
            records.append(i)

    return records


# get all public image 
def get_all_pub_image():
    table = dynamodb.Table('user2Image')
    response = table.scan(
        #FilterExpression = Attr('pubPriv').eq('public'),
        ProjectionExpression = 'userName, imageName, uploadTime, imagePath, audioPath, textPath, averRating',
    )

    records = []

    for i in response['Items']:
        records.append(i)

    while 'LastEvaluatedKey' in response:
        response = table.scan(
            #FilterExpression = Attr('pubPriv').eq('public'),
            ProjectionExpression = 'userName, imageName, uploadTime, imagePath, audioPath, textPath, averRating',
            ExclusiveStartKey=response['LastEvaluatedKey']
            )

        for i in response['Items']:
            records.append(i)

    return records
