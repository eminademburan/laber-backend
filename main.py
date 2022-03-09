from flask import Flask, jsonify, request
from flask_restful import Api, Resource, reqparse
from flask_cors import CORS, cross_origin
from flask_pymongo import PyMongo
import pandas as pd

app = Flask(__name__)
mongo = PyMongo(app, uri="mongodb+srv://ademburan:proje1234@cluster0.9k20l.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = mongo.db
CORS(app)
api = Api(app)

incomes = [{"amount" : 5000}]




@app.route('/incomes')
@cross_origin()
def get_incomes():
    return jsonify(incomes)

@app.route("/add_one")
@cross_origin()
def add_one():
    db.todos.insert_one({'title': "todo title", 'body': "todo body"})
    return jsonify(message="success")

@app.route("/add_user/<string:email>/<string:name>/<string:surname>/<string:phone>/<int:age>/<string:region>/<string:language>/<string:password>/<int:invlink>")
@cross_origin()
def add_user(email,name,surname,phone,age,region,language,password,invlink):
    try:
        db.users.insert_one({'_id': email, 'name': name, 'surname': surname, 'phone': phone,'age': age,'region': region,'language': language, 'password': password,'invlink': invlink})
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
        return jsonify(message="failed")


@app.route("/add_many")
@cross_origin()
def add_many():
    db.todos.insert_many([
        {'_id': 1, 'title': "todo title one ", 'body': "todo body one    "},
        {'_id': 2, 'title': "todo title two", 'body': "todo body two"},
        {'_id': 3, 'title': "todo title three", 'body': "todo body three"},
        {'_id': 4, 'title': "todo title four", 'body': "todo body four"},
        {'_id': 5, 'title': "todo title five", 'body': "todo body five"},
        ])
    return jsonify(message="success")



@app.route("/get_todo/<int:todoId>")
@cross_origin()
def insert_one(todoId):
    todo = db.todos.find_one({"_id": todoId})
    return jsonify(todo)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)

