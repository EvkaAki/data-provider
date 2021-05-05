import os
import pymongo

host = os.getenv('MONGODB_HOST', 'localhost')
port = os.getenv('MONGODB_PORT', '27017')

connection = pymongo.MongoClient("mongodb://" + host + ":" + port + "/")


def get_db(db):
    return connection[db]
