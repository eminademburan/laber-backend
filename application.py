from datetime import datetime

from flask import Flask, jsonify, request
from flask_restful import Api, Resource, reqparse
from flask_cors import CORS, cross_origin
from flask_pymongo import PyMongo
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os
import requests
import json
import scrapper
import time
import atexit

import voicechat

from apscheduler.schedulers.background import BackgroundScheduler

from utils import date_diff_secs

from voicechat.tokenizer import generate_token

application = Flask(__name__)
load_dotenv()
application.config["JWT_SECRET_KEY"] = os.getenv('JWT_SECRET_KEY')
jwt = JWTManager(application)
mongo = PyMongo(application,
                uri="mongodb+srv://ademburan:proje1234@cluster0.9k20l.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = mongo.db
CORS(application)
api = Api(application)


# define the function which will be scheduled
def auto_distribute_task():
    all_users = db.users.find({})
    names = []
    ids = []
    for user in all_users:
        names.append(user["_id"])
    all_tweets = db.tweets.find({})
    for tweet in all_tweets:
        ids.append(tuple([tweet["_id"], tweet['owner_id'], tweet['task_id']]))

    for x in names:
        for y in ids:

            query = {'tweet_id': y[0], 'responser': x, 'owner_id': y[1], 'task_id': y[2]}
            result = db.answers.find_one(query)
            query2 = {'customerEmail': y[1], '_id': y[2]}
            query_result = db.tasks.find_one(query2)
            responser_age_query_result = db.users.find_one({'_id': x})
            user_age = responser_age_query_result['age']
            if query_result is not None:
                min_age = query_result['minAge']
                max_age = query_result['maxAge']
            if result is None and int(max_age) >= int(user_age) >= int(min_age):
                db.answers.insert_one(
                    {'tweet_id': y[0], 'responser': x,
                     'owner_id': y[1], 'task_id': y[2], 'status': 'Waiting'})


scheduler = BackgroundScheduler()
scheduler.add_job(func=auto_distribute_task, trigger="interval", seconds=60)
scheduler.start()


@application.route("/message")
@cross_origin()
def get_user2():
    return jsonify(message="hello")


@application.route('/form-example', methods=['POST'])
@cross_origin()
def form_example():
    data = request.json
    if (data["firstName"] == "Fred"):
        return jsonify(message="success")
    else:
        return jsonify(message="bok")


@application.route("/add_user", methods=['POST'])
@cross_origin()
def add_user():
    try:
        data = request.json
        query = {'_id': data["email"]}
        result = db.users.find_one(query)
        if result is None:
            db.users.insert_one(
                {'_id': data["email"], 'name': data["name"], 'surname': data["surname"], 'phone': data["phone"],
                 'age': data["age"], 'region': data["region"], 'language': data["language"],
                 'password': data["password"], 'invlink': data["link"]})
            return jsonify(message="success")
        else:
            return jsonify(message="failed")
    except:
        return jsonify(message="failed")


@application.route("/add_customer", methods=['POST'])
@cross_origin()
def add_customer():
    try:
        data = request.json
        query = {'_id': data["email"]}
        result = db.customers.find_one(query)
        if result is None:
            db.customers.insert_one(
                {'_id': data["email"], 'name': data["name"], 'username': data["username"], 'phone': data["phone"],
                 'password': data["password"], 'companyName': data["companyName"]})
            return jsonify(message="success")
        else:
            return jsonify(message="failed")
    except:
        return jsonify(message="failed")


# Create a route to authenticate your users and return JWTs. The
# create_access_token() function is used to actually generate the JWT.
@application.route("/get_customer", methods=['POST'])
@cross_origin()
def get_customer():
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    # if email != "test" or password != "test":
    #     return jsonify({"msg": "Bad username or password"}), 401

    data = request.json
    try:
        print("buraya geldim")
        print(data)
        user = db.customers.find_one({"_id": data["email"], "password": data["password"]})
        if user is None:
            print("User does not exist")
            return jsonify(None)
        else:
            print("User exists")
            access_token = create_access_token(identity=email)
            print("access_token: ", access_token)
            return jsonify(access_token=access_token)
            # return jsonify(True)
    except:
        return jsonify(None)


# @application.route("/get_customer", methods=['POST'])
# @cross_origin()
# def get_customer():
#     data = request.json
#     try:
#         print("buraya geldim")
#         print(data)
#         userWithPassword = db.customers.find_one({"_id": data["email"], "password": data["password"]})
#         if userWithPassword is None:
#             print("None")
#             return jsonify(None)
#         else:
#             print("True")
#             return jsonify(True)
#     except:
#         return jsonify(None)

@application.route("/add_task", methods=['POST'])
@jwt_required()
@cross_origin()
def add_task():
    data = request.json

    # get who is making a request
    # requestor_email = get_jwt_identity()
    # print("request owner ", requestor_email)
    print("data: ", data)

    # TODO: check whether all the required fields are supplied by the customer

    try:
        task_find = db.tasks.find_one({"_id": data["taskName"], "customerEmail": data['customerEmail']})
        if task_find is None:
            print("inside if")
            db.tasks.insert_one({
                "_id": data["taskName"],
                'customerEmail': data['customerEmail'],
                'keywords': data['keywords'],
                'hashtags': data['hashtags'],
                'scalarMetrics': data['scalarMetrics'],
                'nonScalarMetrics': data['nonScalarMetrics'],
                'isTwitterSelected': data['isTwitterSelected'],
                'isFacebookSelected': data['isFacebookSelected'],
                'startDate': data['startDate'],
                'endDate': data['endDate'],
                'minAge': data['minAge'],
                'maxAge': data['maxAge'],
                'isFemale': data['isFemale'],
                'isMale': data['isMale'],
                'isTransgender': data['isTransgender'],
                'isGenderNeutral': data['isGenderNeutral'],
                'isNonBinary': data['isNonBinary'],
                'languages': data['languages']
            })
            print("after insert")
            search_keys = [*data['keywords'], *data['hashtags']]
            get_tweets_by_keyword_and_assign(search_keys, data['customerEmail'], data['taskName'])
            return jsonify(None)
        else:
            print("task could not be created!")
            return jsonify(task_find)
    except:
        return jsonify(None)


@application.route("/add_tweet/<string:tweet_id>/<string:text>/<int:noOfLike>/<string:tweetGroup>")
@cross_origin()
def add_tweet(tweet_id, text, noOfLike, tweetGroup):
    try:
        db.tweets.insert_one({'_id': tweet_id, 'text': text, 'likes': noOfLike, 'owner_id': tweetGroup})
        return jsonify(message="success")
    except:
        return jsonify(message="failed")


@application.route("/get_tweet/<string:tweet_id>/<string:task_id>")
@cross_origin()
def get_tweet(tweet_id, task_id):
    try:
        query = {'_id': tweet_id, 'task_id': task_id}
        tweet = db.tweets.find_one(query)
        if tweet is None:
            return jsonify(None)
        else:
            return jsonify(tweet)
    except:
        return jsonify(None)

@application.route("/get_task/<string:task_id>")
@cross_origin()
def get_task(task_id):
    print(task_id)
    try:
        query = {'_id': task_id}
        task = db.tasks.find_one(query)
        if task is None:
            return jsonify(None)
        else:
            return jsonify(task)
    except:
        return jsonify(None)

@application.route("/add_response", methods=['POST'])
@cross_origin()
def add_response():
    data = request.json
    try:

        query = {'status': "Waiting", 'tweet_id': data["tweet_id"], 'responser': data["mail"], 'task_id' : data["task_id"]}
        if db.answers.find_one(query) is None:
            return jsonify(message="failed")
        else:
            query = {'tweet_id': data["tweet_id"], 'responser': data["mail"], 'task_id' : data["task_id"]}
            new_values = {"$set": {'answers': data["answers"], 'status': 'Answered'}}
            db.answers.update_one(query, new_values)
            return jsonify(message="true")
    except:
        return jsonify(message="failed")


# creates an agora channel with given name
# adds the necessary documents to the voicechats collection for the given mails
def assign_voicechat(channel_name, mails):
    channel_name = str(channel_name)
    token = generate_token(channel_name)
    dt = datetime.now()
    q_list = [{'name': channel_name, 'token': token, 'mail': mail, 'date': dt} for mail in mails]
    db.voicechats.insert_many(q_list)


# clears the channels older than 5 minutes from the collection
def clear_voicechat():
    projection = {'_id': 1, 'token': 0, 'mail': 0, 'date': 1}
    res = db.voicechats.find({}, projection)
    dt = datetime.now()
    to_delete = [{'_id': _id} for _id in res if date_diff_secs(res.date, dt) > 300]
    db.voicechats.delete_many(to_delete)

# checks if there is a pending voicechat for a given responser, if there is returns channel name and token
@application.route("/check_voicechat/<string:responser>")
@cross_origin()
def check_voicechat(responser):
    query = {'mail': responser}
    projection = {'_id': 0, 'name': 1, 'token': 1}
    channel = db.voicechats.find_one(query, projection)
    if channel is None:
        return jsonify(None)
    else:
        return jsonify(channel)




@application.route("/get_tweet_to_answer/<string:responser>")
@cross_origin()
def getTweet2(responser):
    query = {'responser': responser, 'status': 'Waiting'}
    projection = {'_id': 0, 'tweet_id': 1, "task_id" : 1 }
    tweet = db.answers.find_one(query, projection)

    if tweet is None:
        return jsonify(None)
    else:
        assign_voicechat(tweet['tweet_id'], [responser])
        return jsonify(tweet)



@application.route("/assign_user/<string:tweet_id>/<string:responser>")
@cross_origin()
def assignUser(tweet_id, responser):
    try:
        query = {'tweet_id': tweet_id, 'responser': responser}
        if db.answers.find_one(query) is not None:
            return jsonify(message="failed")
        else:
            db.answers.insert_one(
                {'tweet_id': tweet_id, 'responser': responser, 'sentiment': '', 'sarcasm': '',
                 'status': 'Waiting'})
            return jsonify(message="success")
    except:
        return jsonify(message="failed")


@application.route("/get_user", methods=['POST'])
@cross_origin()
def get_user():
    data = request.json
    try:
        userWithPassword = db.users.find_one({"_id": data["email"]})
        if userWithPassword is None:
            return jsonify(None)
        else:
            return jsonify(userWithPassword)
    except:
        return jsonify(None)


@application.route("/fetch_tweets/<string:search_key>")
@cross_origin()
def get_tweets_by_keyword(search_key):
    tweet_attributes = scrapper.get_tweets(search_key)

    for tweet_id, tweet in tweet_attributes.items():
        is_tweet_exist = db.tweets.find_one({"_id": tweet_id})
        if is_tweet_exist is None:
            db.tweets.insert_one({'_id': str(tweet_id), 'url': tweet, 'owner_id': "ademsan0606@gmail.com"})
    return jsonify(message="true")


def get_tweets_by_keyword_and_assign(search_key, owner_id, task_id):
    for key in search_key:
        tweet_attributes = scrapper.get_tweets(key)

        for tweet_id, tweet in tweet_attributes.items():
            is_tweet_exist = db.tweets.find_one({"_id": tweet_id, 'owner_id': owner_id, 'task_id': task_id})
            if is_tweet_exist is None:
                db.tweets.insert_one({'_id': str(tweet_id), 'url': tweet, 'owner_id': owner_id, 'task_id': task_id})


if __name__ == '__main__':
    application.run(host="0.0.0.0", port=5000)
