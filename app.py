from flask import Flask, request, Response, abort, jsonify
from bson import json_util
import os
import click
import csv
import requests
import uuid

import pprint
import connection
import crypt

app = Flask(__name__)

db_core = connection.get_db('dataprovider_core')
password = b"examplePassword"

def get_kubeflow_user(auth_service_session):
    cookies = {'authservice_session': auth_service_session}
    response = requests.get(url='http://dp.host.haus/api/workgroup/env-info', cookies=cookies)

    if response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            print('Decoding JSON has failed')
    else:
        print(f'Request failed with status code {response.status_code}')

    return {}


def is_admin(auth_service_session):
    user = get_kubeflow_user(auth_service_session)
    return user and user['isClusterAdmin'] == True


def data_stream(data):
    for entry in data:
        yield crypt.decrypt(entry['line'])


# @app.route('/stream/<database>/<collection>.csv')
# def route_action(database, collection):
#
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
#     except:
#         abort(404)


@app.route('/access/grant', methods=['POST'])
def grant_access():
    dataset_id = request.json['dataset_id']
    user_id = request.json['user_id']
    token = request.json['token']

    if is_admin(token):
        access = db_core.dataset_access.find_one({"user_id": user_id, "dataset_id": dataset_id})

        if access:
            return jsonify({"message": "Access already exists"}), 400

        result = db_core.dataset_access.insert_one({"user_id": user_id, "dataset_id": dataset_id})
        return jsonify({"message": "Access to dataset granted"}), 201
    else:
        return jsonify({"message": "Unauthorized"}), 401


@app.route('/access/revoke', methods=['POST'])
def revoke_access():
    dataset_id = request.json['dataset_id']
    user_id = request.json['user_id']
    token = request.json['token']
    if is_admin(token):
        db_core.dataset_access.delete_one({"user_id": user_id, "dataset_id": dataset_id})
        return jsonify({"message": "Access revoked"}), 200
    else:
        return jsonify({"message": "Unauthorized"}), 401


@app.route('/user/dataset/get', methods=['GET'])
def dataset_get():
    token = request.json['token']
    dataset_id = request.json['dataset_id']
    user = get_kubeflow_user(token)
    user_id = user['user']
    access = db_core.dataset_access.find_one({"user_id": user_id, "dataset_id": dataset_id})
    if access or is_admin(token):
        dataset = db_core.datasets.find_one({"uuid": dataset_id})
        return Response(json_util.dumps(dataset), mimetype='application/json'), 200
    else:
        return jsonify({"message": "Unauthorized"}), 401


@app.route('/user/dataset/available', methods=['GET'])
def available_datasets():
    token = request.json['token']
    user = get_kubeflow_user(token)
    user_id = user['user']
    # user_id = request.args.get('user_id')
    access_list = list(db_core.dataset_access.find({"user_id": user_id}))
    dataset_ids = [access['dataset_id'] for access in access_list]
    datasets = list(db_core.datasets.find({"uuid": {"$in": dataset_ids}}))

    return Response(json_util.dumps(datasets), mimetype='application/json'), 200


@app.route('/user/dataset/requestable', methods=['GET'])
def requestable_datasets():
    token = request.json['token']
    user = get_kubeflow_user(token)
    user_id = user['user']
    # user_id = request.args.get('user_id')
    access_list = list(db_core.dataset_access.find({"user_id": user_id}))
    user_dataset_ids = [access['dataset_id'] for access in access_list]
    datasets = list(db_core.datasets.find({"uuid": {"$nin": user_dataset_ids}}))
    return Response(json_util.dumps(datasets), mimetype='application/json'), 200


@app.route('/stream/anonymized', methods=['GET'])
def stream_anonymized():
    dataset_id = request.args.get('dataset_id')
    token = request.args.get('token')
    # token = request.json['user_id']
    user = get_kubeflow_user(token)
    user_id = user['user']
    # user_id = request.args.get('user_id')
    access = db_core.dataset_access.find_one({"user_id": user_id, "dataset_id": dataset_id})

    if not access:
        return jsonify({"message": "No access to the dataset"}), 403

    dataset = db_core.datasets.find_one({"uuid": dataset_id})
    if not dataset:
        return jsonify({"message": "Dataset not found"}), 404

    db_anonymized = connection.get_db('datasets_anonymized')
    dataset_data = db_anonymized[dataset['identifier']].find()

    def generate():
        for record in dataset_data:
            yield record['line'] + '\n'

    return Response(generate(), mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=" + dataset['identifier'] + "_anonymized.csv"})


@app.route('/stream/full', methods=['GET'])
def stream_full():
    dataset_id = request.args.get('dataset_id')
    token = request.args.get('token')
    if not is_admin(token):
        return jsonify({"message": "No access to the dataset"}), 403
    #
    # token = request.json['user_id']
    dataset = db_core.datasets.find_one({"uuid": dataset_id})
    if not dataset:
        return jsonify({"message": "Dataset not found"}), 404

    db_full = connection.get_db('datasets_full')
    dataset_data = db_full[dataset['identifier']].find()

    def generate():
        for record in dataset_data:
            yield str(crypt.decrypt(record['line'])) + '\n'

    return Response(generate(), mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=" + dataset['identifier'] + ".csv"})


@app.route('/')
def index_action():
    return "App Running"


@app.cli.command('import-csv')
@click.argument('database')
@click.argument('collection')
def import_csv_command(database, collection):
    file_path = "./csv/" + collection + ".csv"
    if os.path.exists(file_path):
        db = connection.get_db(database)
        db[collection].drop()
        dataset = db[collection]

        with open(file_path) as file:
            for line in file.readlines():
                dataset.insert_one({"line": crypt.encrypt(line, password)})
    else:
        print("File " + collection + ".csv not found in csv directory.")


@app.cli.command('import-dataset')
@click.argument('collection')
@click.argument('name')
def import_csv_command(collection, name):
    full_path = f"./csv/{collection}/full.csv"
    anonymized_path = f"./csv/{collection}/anonymized.csv"

    if os.path.exists(full_path) and os.path.exists(anonymized_path):
        db_full = connection.get_db('datasets_full')
        db_anonymized = connection.get_db('datasets_anonymized')

        db_full[collection].drop()
        with open(full_path, newline='') as file:
            reader = csv.reader(file)
            for line in reader:
                encrypted_line = crypt.encrypt(','.join(line), password)
                db_full[collection].insert_one({"line": encrypted_line})

        db_anonymized[collection].drop()
        with open(anonymized_path, newline='') as file:
            reader = csv.reader(file)
            for line in reader:
                db_anonymized[collection].insert_one({"line": ','.join(line)})

        db_core.datasets.insert_one({"identifier": collection, "name": name, "uuid": str(uuid.uuid4())})
    else:
        print(f"Files full.csv and/or anonymized.csv not found in {collection} directory.")


if __name__ == '__main__':
    app.run()
