from flask import Flask, request, Response, abort
import os
import click

import pprint
import connection
import crypt

app = Flask(__name__)


def data_stream(data):
    return "App Running"

#     for entry in data:
#         yield crypt.decrypt(entry['line'])


@app.route('/stream/<database>/<collection>.csv')
def route_action(database, collection):
    return "App Running"

#     db = connection.get_db(database)
#     if database == "system" or collection == "acl":
#         abort(401)
#
#     try:
#         db.validate_collection(collection)
#         dataset = db[collection]
#         response = Response(data_stream(dataset.find()), mimetype='text/csv')
#         response.headers['Content-Disposition'] = 'attachment; filename=' + collection + '.csv'
#         return response
    except:
        abort(404)


@app.route('/')
def index_action():
    return "App Running"


@app.cli.command('import-csv')
@click.argument('database')
@click.argument('collection')
def import_csv_command(database, collection):
    return "App Running"

#     file_path = "./csv/" + collection + ".csv"
#     if os.path.exists(file_path):
#         db = connection.get_db(database)
#         db[collection].drop()
#         dataset = db[collection]
#
#         with open(file_path) as file:
#             for line in file.readlines():
#                 dataset.insert_one({"line": crypt.encrypt(line)})
#     else:
#         print("File " + collection + ".csv not found in csv directory.")


if __name__ == '__main__':
    app.run()
