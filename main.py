from flask import Flask, jsonify, request
from flask_restful import Api, Resource, reqparse
from flask_cors import CORS, cross_origin
from flask_pymongo import PyMongo


import time
import atexit

from apscheduler.schedulers.background import BackgroundScheduler

#define the function whic will be scheduled

#scheduler = BackgroundScheduler()
#scheduler.add_job(func=print_date_time, trigger="interval", seconds=20)
#scheduler.start()

app = Flask(__name__)
mongo = PyMongo(app, uri="mongodb+srv://ademburan:proje1234@cluster0.9k20l.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = mongo.db
CORS(app)
api = Api(app)

@app.route("/message")
@cross_origin()
def get_user2():
    return jsonify(message="hello")

@app.route("/add_user/<string:email>/<string:name>/<string:surname>/<string:phone>/<int:age>/<string:region>/<string:language>/<string:password>/<int:invlink>")
@cross_origin()
def add_user(email,name,surname,phone,age,region,language,password,invlink):
    try:
        db.users.insert_one({'_id': email, 'name': name, 'surname': surname, 'phone': phone,'age': age,'region': region,'language': language, 'password': password,'invlink': invlink})
        return jsonify(message="success")
    except:
        return jsonify(message="failed")


@app.route("/add_tweet/<int:tweet_id>/<string:text>/<int:noOfLike>/<string:tweetGroup>")
@cross_origin()
def add_tweet(tweet_id,text,noOfLike,tweetGroup):
    try:
        db.tweets.insert_one({ '_id': tweet_id, 'text': text, 'likes': noOfLike, 'owner_id': tweetGroup })
        return jsonify(message="success")
    except:
        return jsonify(message="failed")

@app.route("/get_tweet/<int:tweet_id>")
@cross_origin()
def get_tweet(tweet_id):
    try:
        query = {'_id': tweet_id}
        tweet = db.tweets.find_one(query)
        if tweet is None:
            return jsonify(None)
        else:
            return jsonify(tweet)
    except:
        return jsonify(None)



@app.route("/add_response/<int:tweet_id>/<string:responser>/<string:sentiment>/<string:sarcasm>")
@cross_origin()
def add_response(tweet_id, responser, sentiment, sarcasm):
    try:
        query = { 'status': "Waiting", 'tweet_id': tweet_id, 'responser' :responser }
        if db.answers.find_one( query) is None:
            return jsonify(message="failed")
        else:
            query = { 'tweet_id': tweet_id, 'responser' : responser }
            new_values = { "$set": { 'sentiment': sentiment, 'sarcasm': sarcasm, 'status': 'Answered'}}
            db.answers.update_one( query, new_values)
            return jsonify(message="true")
    except:
        return jsonify(message="failed")

@app.route("/get_tweet_to_answer/<string:responser>")
@cross_origin()
def getTweet2(responser):
    try:
        query = { 'responser': responser, 'status': 'Waiting' }
        projection = { '_id':0, 'tweet_id':1}
        tweet = db.answers.find_one( query, projection)
        if tweet is None:
            return jsonify(None)
        else:
            return jsonify(tweet)
    except:
        return jsonify(None)

@app.route("/assign_user/<int:tweet_id>/<string:responser>")
@cross_origin()
def assignUser(tweet_id, responser):
    try:
        query = { 'tweet_id': tweet_id, 'responser' : responser }
        if db.answers.find_one( query) is not None:
            return jsonify(message="failed")
        else:
            db.answers.insert_one(
                {'tweet_id': tweet_id, 'responser': responser, 'sentiment': '', 'sarcasm': '',
                 'status': 'Waiting'})
            return jsonify(message="success")
    except:
        return jsonify(message="failed")


@app.route("/get_user/<string:email>")
@cross_origin()
def get_user(email):
    try:
        userWithPassword = db.users.find_one({"_id": email})
        if userWithPassword is None:
            return jsonify(None)
        else:
            return jsonify(userWithPassword)
    except:
        return jsonify(None)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)

