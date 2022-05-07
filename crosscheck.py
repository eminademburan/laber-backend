import random
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

import numpy as np
from scipy.stats import entropy
from apscheduler.schedulers.background import BackgroundScheduler

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


def z_score(answers):
    mean = np.mean(answers, axis=1, keepdims=True)
    std = np.std(answers, axis=1, keepdims=True)
    return (answers - mean) / std

def get_metrics(task_id):
    query = {"_id": task_id}
    projection = {"_id": 0, "scalarMetrics": 1, "nonScalarMetrics": 1}
    return db.tasks.find_one(query, projection)


def get_answers(tweet_id):
    query = {"tweet_id": tweet_id, "status": "Answered"}
    projection = {"_id": 0, "responser": 1, "answers": 1}
    return db.answers.find(query, projection)


ROOM_SIZE = 5
ENTROPY_THRESHOLD = 0.5

def check_nonscalar(answers):
    entropies = entropy(answers)
    num_metrics = answers.shape[0]
    num_experts = answers.shape[1]

    # No need for a voice chat for metrics without many diversity
    satisfied = np.greater(entropies, ENTROPY_THRESHOLD)

    experts = np.arange(min(ROOM_SIZE, num_experts))
    chosen_experts = np.zeros((num_metrics, num_experts))
    for i in range(num_metrics):
        chosen_experts[i] = experts

    return chosen_experts, satisfied

def check_scalar(answers):
    # all the answers for all the metrics of a tweet are given
    # rows are experts, and columns are answers
    # 1) compute the z-scores of the answers
    # 2) check if any outliers (z-scores between (-inf, -1) and (1, inf))
    # 3) choose <room_size> experts by the following rule:
    #    choose the 2 from leftmost, 2 from rightmost and 1 from middle
    #    if <room_size> is 5

    # compute the z-scores:
    z_scores = z_score(answers)
    mins = np.min(z_scores, axis=1)
    maxes = np.max(z_scores, axis=1)

    # No need for a voice chat for metrics without outliers
    satisfied = np.logical_or(np.less(mins, -1), np.greater(maxes, 1))
    # satisfying_rows = np.flatnonzero(satisfied)

    sorted_experts = np.argsort(z_scores, axis=1)
    leftmosts = sorted_experts[ROOM_SIZE//2:]
    middle = sorted_experts[sorted_experts.shape[0]//2]
    rightmosts = sorted_experts[:ROOM_SIZE//2]

    chosen_experts = np.concatenate((leftmosts, middle, rightmosts), axis=1)

    return chosen_experts, satisfied

def get_response_rate(tweet_id):
    query = {"tweet_id": tweet_id}
    projection = {"_id": 0, "responser": 1}

    num_answers = len(list(get_answers(tweet_id)))
    all = len(list(db.answers.find(query, projection)))

    return num_answers / all

def voicechat_exists(tweet_id):
    query = {'tweet_id': tweet_id}
    projection = {'tweet_id': 1}
    voicechats = db.voice_chats.find_one(query, projection)

    return voicechats is not None

RESPONSE_RATE_THRESHOLD = 0.01

def check_conflict(tweet_id):

    if get_response_rate(tweet_id) < RESPONSE_RATE_THRESHOLD or voicechat_exists(tweet_id):
        return
    
    query = {"_id": tweet_id}
    projection = {"_id": 0, "task_id": 1}
    tweet = db.tweets.find_one(query, projection)
    if tweet is None:
        print("tweet was not found " + tweet_id)
        return
    task_id = tweet["task_id"]

    metrics = get_metrics(task_id)
    scalar_metrics = metrics["scalarMetrics"]
    nonscalar_metrics = metrics["nonScalarMetrics"]
    n = len(scalar_metrics)

    answers_db = list(get_answers(tweet_id))
    answers = [row["answers"] for row in answers_db]
    # scalar_answers = [answer[:n] for answer in answers]
    # nonscalar_answers = [answer[n:] for answer in answers]

    responsers = [row["responser"] for row in answers_db]

    answers = np.array(answers).T
    nonscalar_answers = answers[:, n:]
    scalar_answers = answers[:, :n]

    chosen_experts, satisfied = np.concatenate((check_nonscalar(nonscalar_answers),
                                                check_scalar(scalar_answers)), axis=0)

    for i in range(chosen_experts):
        if satisfied[i]:
            mails = []
            for j in range(chosen_experts[i]):
                mails.append(responsers[j])
                assign_voicechat(mails, tweet_id, metric_id=i)

# creates an agora channel with given name
# adds the necessary documents to the voicechats collection for the given mails
def assign_voicechat(mails, tweet_id, metric_id):
    channel_name = str(random.randint(0, int(1e10)) + int(1e10))
    # check if channel name exists
    for mail in mails:
        if db.voice_chats.find_one({"mail": mail}) is not None:
            return
    if db.voice_chats.find_one({"name": channel_name}) is not None:
        return
    token = generate_token(channel_name)
    dt = datetime.now()
    q_list = [{'name': channel_name, 'tweet_id': tweet_id, 'metric_id': metric_id, 'token': token, 'mail': mail, 'date': dt} for mail in mails]
    db.voice_chats.insert_many(q_list)

def sa():
    tweet_id = "1522567873742393344"
    # check_conflict(tweet_id)
    X = [6, 7, 7, 12, 13, 13, 15, 16, 19, 22]
    print(z_score(X))


def post_conflict(task_id, tweet_id, mails):
    query = {'task_id': task_id, 'tweet_id': tweet_id, 'mails': mails}
    db.conflicts.insert_one(query)


scheduler = BackgroundScheduler()
scheduler.add_job(func=sa, trigger="interval", seconds=2)
scheduler.start()

if __name__ == '__main__':
    application.run(host="0.0.0.0", port=5000)