import os
import pymongo

host = os.getenv('MONGODB_HOST', 'localhost')
port = os.getenv('MONGODB_PORT', '27011')

user = os.getenv('MONGODB_USER', 'admin')
password = os.getenv('MONGODB_PASS', 'password')

# connection = pymongo.MongoClient("mongodb://"+ user +":"+ password +"@" + host + ":" + port + "/")
connection = pymongo.MongoClient("mongodb://" + host + ":" + port + "/")

def get_db(db):

    return connection[db]
