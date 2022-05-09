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
import random
from datetime import timedelta

import voicechat

from crosscheck import check_conflict, assign_voicechat
from utils import date_diff_secs

from voicechat.tokenizer import generate_token

application = Flask(__name__)
load_dotenv()
application.config["JWT_SECRET_KEY"] = os.getenv('JWT_SECRET_KEY')
application.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
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
        return jsonify(message="fail")


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


    task_find = db.tasks.find_one({"_id": data["taskName"], "customerEmail": data['customerEmail']})
    if task_find is None:
        print("inside if")
        print("inside if data", data)
        if data['taskDataType'] == 0:  # Twitter
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
                'languages': data['languages'],
                'taskDataType': data['taskDataType']
            })
            search_keys = [*data['keywords'], *data['hashtags']]
            get_tweets_by_keyword_and_assign(search_keys, data['startDate'], data['endDate'], data['customerEmail'], data['taskName'])
        elif data['taskDataType'] == 1:  # Image Data
            print("in elif")
            print("data: ", data.keys())
            # add task
            db.tasks.insert_one({
                "_id": data["taskName"],
                'customerEmail': data['customerEmail'],
                'scalarMetrics': data['scalarMetrics'],
                'nonScalarMetrics': data['nonScalarMetrics'],
                'minAge': data['minAge'],
                'maxAge': data['maxAge'],
                'isFemale': data['isFemale'],
                'isMale': data['isMale'],
                'isTransgender': data['isTransgender'],
                'isGenderNeutral': data['isGenderNeutral'],
                'isNonBinary': data['isNonBinary'],
                'languages': data['languages'],
                'taskDataType': data['taskDataType']
            })
            # add images
            images = []
            for index, image_base64 in enumerate(data['zipFile']):
                images.append({
                    '_id': str(random.randint(0, int(1e10)) + int(1e10)),
                    'url': image_base64,
                    'owner_id': data['customerEmail'],
                    'task_id': data['taskName'],
                    'image_name': 'image'+str(index)+".jpg",
                })
            db.tweets.insert_many(images)
            # db.tasks.insert_one({
            #     "_id": data["taskName"],
            #     'customerEmail': data['customerEmail'],
            #     'scalarMetrics': data['scalarMetrics'],
            #     'nonScalarMetrics': data['nonScalarMetrics'],
            #     'minAge': data['minAge'],
            #     'maxAge': data['maxAge'],
            #     'isFemale': data['isFemale'],
            #     'isMale': data['isMale'],
            #     'isTransgender': data['isTransgender'],
            #     'isGenderNeutral': data['isGenderNeutral'],
            #     'isNonBinary': data['isNonBinary'],
            #     'languages': data['languages'],
            #     'dataLink': data['dataLink'],
            #     'taskDataType': data['taskDataType']
            # })
        print("after insert")
        return jsonify(None)
    else:
        print("task could not be created!")
        return jsonify(task_find)


@application.route("/add_tweet/<string:tweet_id>/<string:text>/<int:noOfLike>/<string:tweetGroup>")
@cross_origin()
def add_tweet(tweet_id, text, noOfLike, tweetGroup):
    try:
        db.tweets.insert_one({'_id': tweet_id, 'text': text, 'likes': noOfLike, 'owner_id': tweetGroup})
        return jsonify(message="success")
    except:
        return jsonify(message="failed")


@application.route("/get_jsondata", methods=['POST'])
@cross_origin()
def get_rawData():
    data = request.json
    try:
        query = { "task_id" : data["taskName"]}
        query2 = { "_id" : data["taskName"] }
        db.answers.find({'_id': tweet_id, 'text': text, 'likes': noOfLike, 'owner_id': tweetGroup})
        return jsonify(message="success")
    except:
        return jsonify(message="failed")


@application.route("/get_answers_in_json", methods=['POST'])
@jwt_required()
@cross_origin()
def get_answers_in_json():
    try:
        data = request.json
        print(data)
        query = {"task_id": data["taskName"], "status": "Answered"}
        query2 = {"_id": data["taskName"]}
        projection = { "_id": 0, "owner_id": 0, "status": 0}
        result = db.tasks.find_one(query2)
        dict = {}
        if result["taskDataType"] == 1:
            for task in db.answers.find(query, projection):
                dict[task['image_name']] = task
            print(dict)
            return jsonify(dict)
        else:
            return jsonify(None)
    except:
        return jsonify(None)


@application.route("/get_tweet/<string:tweet_id>/<string:task_id>")
@cross_origin()
def get_tweet(tweet_id, task_id):
    try:
        query = {'_id': tweet_id, 'task_id': task_id}
        tweet = db.tweets.find_one(query)
        if tweet is None:
            return jsonify(None)
        else:
            return tweet["url"]
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


@application.route("/get_min_max_for_task/<string:customer_email>/<string:task_name>/<string:scalar_metric_name>")
@jwt_required()
@cross_origin()
def get_min_max_for_task(customer_email, task_name, scalar_metric_name):
    print("customer email: ", customer_email)
    print("task name: ", task_name)
    print("scalar metric name: ", scalar_metric_name)
    task = db.tasks.find_one({'_id': task_name, 'customerEmail': customer_email})
    print(task)
    for scalar_metric in task['scalarMetrics']:
        print("scalar metric: ", scalar_metric)
        if scalar_metric['name'] == scalar_metric_name:
            print("min: ", scalar_metric['min'])
            print("max: ", scalar_metric['max'])
            min_max = [scalar_metric['min'], scalar_metric['max']]
            return jsonify(min_max)
    return jsonify(None)


@application.route("/get_customer_tasks/<string:customer_email>")
@jwt_required()
@cross_origin()
def get_customer_tasks(customer_email):
    get_customer_tasks_query = {'customerEmail': customer_email}
    atleast_one_customer_task_exists = False
    all_task_answers = {}
    for customer_task in db.tasks.find(get_customer_tasks_query):
        atleast_one_customer_task_exists = True
        task_scalar_answers = {}
        task_nonscalar_answers = {}

        # if we have at least one answer for the task
        an_answer_to_the_task = db.answers.find_one({'task_id': customer_task['_id'], 'status': 'Answered'})
        if an_answer_to_the_task is not None:
            for scalar_answer in customer_task['scalarMetrics']:
                print("scalar answer in for: ", customer_task['_id'], " :: ", scalar_answer)
                task_scalar_answers[scalar_answer['name']] = 0

            for nonscalar_answer in customer_task['nonScalarMetrics']:
                task_nonscalar_answers[nonscalar_answer['name']] = {}
                task_nonscalar_answers_metric_keys = {}
                for nonscalar_metric_key in nonscalar_answer['metricKeys']:
                    task_nonscalar_answers_metric_keys[nonscalar_metric_key] = 0
                task_nonscalar_answers[nonscalar_answer['name']] = task_nonscalar_answers_metric_keys

            scalar_and_nonscalar_combined = {'scalar': task_scalar_answers, 'nonscalar': task_nonscalar_answers}
            all_task_answers[customer_task['_id']] = scalar_and_nonscalar_combined

   # print("all task answers: ", all_task_answers)

    # get answers
    for customer_task in db.tasks.find(get_customer_tasks_query):
        projection = {'_id': 0, 'tweet_id': 0, "owner_id": 0, "status": 0}
        get_task_answers_query = {'task_id': customer_task['_id'], 'status': 'Answered'}
        task_name = customer_task['_id']
        response_count = 0

        # get all answers belonging to the task with the '_id'
        for answer_to_task in db.answers.find(get_task_answers_query, projection):
            # print(answer_to_task)


            # responer, task_name
            # responser_answer_count_to_task_name = db.answers.find({'responser': answer_to_task['responser'], 'task_id': task_name}).count()
            # response_count += responser_answer_count_to_task_name
            print("answer to task: ", answer_to_task)
            # get answers for nonscalar metrics

            if len(answer_to_task['answers']):
                response_count += 1
                nonscalar_metric_count_for_task_name = len(all_task_answers[task_name]['nonscalar'])
                for index in range(nonscalar_metric_count_for_task_name):
                    count = 0
                    for non_scalar_key in all_task_answers[task_name]['nonscalar']:
                        if index == count and len(answer_to_task['answers']):
                            answer = answer_to_task['answers'][index]
                            print("key: ", all_task_answers[task_name]['nonscalar'][non_scalar_key])
                            all_task_answers[task_name]['nonscalar'][non_scalar_key][answer] += 1
                        count += 1



                # get answers for scalar metrics and increment count
                scalar_metric_count_for_task_name = len(all_task_answers[task_name]['scalar'])
                for index in range(nonscalar_metric_count_for_task_name, scalar_metric_count_for_task_name + nonscalar_metric_count_for_task_name):
                    # print("index: ", index)
                    # print("answers: ", answer_to_task['answers'])

                    count = nonscalar_metric_count_for_task_name
                    for scalar_key in all_task_answers[task_name]['scalar']:
                        if index == count:
                            answer = answer_to_task['answers'][index]
                            all_task_answers[task_name]['scalar'][scalar_key] += int(answer)
                        count += 1

                    # print("date type: ", type(answer_to_task['answerDate']))
                    # print("answers type: ", type(answer_to_task['answers']))

        # go through scalar tasks in task with the 'task_name' and
        # divide the results by the responser count
        if response_count != 0:
            for scalar_metric_result in all_task_answers[task_name]['scalar']:
                # print("result key for ", task_name, " :",  scalar_metric_result)
                # print("response_count: ", response_count)
                # print("result before averaging: ", all_task_answers[task_name]['scalar'][scalar_metric_result])
                average_result = all_task_answers[task_name]['scalar'][scalar_metric_result] / response_count
                all_task_answers[task_name]['scalar'][scalar_metric_result] = round(average_result, 1)

    #print("print all task_answers: ", all_task_answers)
    # all_task_answers[task_name]
    # all_task_answers[task_name]['scalar']
    # all_task_answers[task_name]['scalar']['dignity']

    # change_metric_type_from_obj_to_lst
    all_task_answers = change_metric_type_from_obj_to_lst(all_task_answers)

    if atleast_one_customer_task_exists is False:
        return jsonify(message="failed")
    else:
        return jsonify(all_task_answers)


# if the answer is empty remove from the list
def change_metric_type_from_obj_to_lst(all_task_answers):
    lst_result = all_task_answers

    for customer_task_name in all_task_answers:
        scalar_metrics = []
        scalar_metric_results = []


        for scalar_metric in all_task_answers[customer_task_name]['scalar']:
            scalar_metrics.append(scalar_metric)
            scalar_metric_results.append(all_task_answers[customer_task_name]['scalar'][scalar_metric])

        scalar_all_results = [scalar_metrics, scalar_metric_results]
        lst_result[customer_task_name]['scalar'] = scalar_all_results
        for nonscalar_metric in all_task_answers[customer_task_name]['nonscalar']:
            nonscalar_results = []
            nonscalar_metric_keys = []
            nonscalar_metric_key_results = []

            for key in all_task_answers[customer_task_name]['nonscalar'][nonscalar_metric]:
                nonscalar_metric_keys.append(key)
                nonscalar_metric_key_results.append(all_task_answers[customer_task_name]['nonscalar'][nonscalar_metric][key])

            nonscalar_results.append(nonscalar_metric_keys)
            nonscalar_results.append(nonscalar_metric_key_results)

            lst_result[customer_task_name]['nonscalar'][nonscalar_metric] = nonscalar_results
   # print(lst_result)
    return lst_result


@application.route("/add_response", methods=['POST'])
@cross_origin()
def add_response():
    data = request.json
    try:
        query = {'status': "Waiting", 'tweet_id': data["tweet_id"], 'responser': data["mail"], 'task_id' : data["task_id"]}
        if db.answers.find_one(query) is None:
            return jsonify(message="failed")
        else:
            query2 = { "_id" : data["task_id"]}
            result = db.tasks.find_one(query2)

            sum = 0
            if result is not None:
                sum = len(result["scalarMetrics"]) + len(result["nonScalarMetrics"])

            if len(data["answers"]) == 0 or sum != len(data["answers"]):
                return jsonify(message="true")
            for data2 in data["answers"]:
                if data2 is None:
                    return jsonify(message="true")
            query = {'tweet_id': data["tweet_id"], 'responser': data["mail"], 'task_id': data["task_id"]}
            new_values = {"$set": {'answers': data["answers"], 'status': 'Answered', 'answerDate': data["date"]}}
            db.answers.update_one(query, new_values)
            check_conflict(data["tweet_id"])
            return jsonify(message="true")
    except:
        return jsonify(message="failed")



# creates an agora channel with given name
# adds the necessary documents to the voicechats collection for the given mails
def assign_voicechat(channel_name, mails):
    channel_name = str(channel_name)
    # check if channel name exists
    if db.voicechats.find_one({"name": channel_name}) is not None:
        return
    token = generate_token(channel_name)
    dt = datetime.now()
    q_list = [{'name': channel_name, 'token': token, 'mail': mail, 'date': dt} for mail in mails]
    db.voicechats.insert_many(q_list)


# clears the channels older than 5 minutes from the collection
def clear_voicechat():
    now = datetime.now()
    to_delete = []
    try:
        for row in db.vchats.find():
            date = row['date']
            if date_diff_secs(date, now) > 1:
                to_delete.append(row['_id'])
        db.vchats.delete_many({'_id': {'$in' : to_delete}})

    except Exception as e:
        print(e)

# checks if there is a pending voicechat for a given responser, if there is returns channel name and token
@application.route("/check_voicechat/<string:responser>")
@cross_origin()
def check_voicechat(responser):
    query = {'mail': responser}
    projection = {'_id': 0, 'name': 1, 'token': 1}
    channel = db.vchats.find_one(query, projection)
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


def get_tweets_by_keyword_and_assign(search_key, start_date, end_date, owner_id, task_id):
    for key in search_key:
        tweet_attributes = scrapper.get_tweets(key, start_date, end_date)

        for tweet_id, tweet in tweet_attributes.items():
            is_tweet_exist = db.tweets.find_one({"_id": str(tweet_id)})
            if is_tweet_exist is None:
                db.tweets.insert_one({'_id': str(tweet_id), 'url': tweet, 'owner_id': owner_id, 'task_id': task_id})


if __name__ == '__main__':
    application.run(host="0.0.0.0", port=5000)