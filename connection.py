import os
import pymongo

host = os.getenv('MONGODB_HOST', 'localhost')
port = os.getenv('MONGODB_PORT', '27017')

user = os.getenv('MONGODB_USER', 'admin')
password = os.getenv('MONGODB_PASS', 'password')


# connection = pymongo.MongoClient("mongodb://"+ user +":"+ password +"@" + host + ":" + port + "/")


def get_db(db):
#     return connection[db]
