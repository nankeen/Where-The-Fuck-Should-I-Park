# app.py
import atexit
import requests
import pymongo
import base64

from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask import Flask, jsonify, abort, request, render_template
from config import BaseConfig
from bson import Binary, Code, ObjectId
from bson.json_util import dumps
from bson.errors import InvalidId
from bson.son import SON
from random import randint

app = Flask(__name__)
app.config.from_object(BaseConfig)

client = pymongo.MongoClient('localhost', 27017)
db = client.wtfsip


def poll_nodes():
    nodes = db.nodes.find({'lora': True})
    current_time = datetime.now()
    for node in nodes:
        resp = requests.get('https://guestnet-malaysia.orbiwise.com/rest/nodes/{}/payloads/ul/latest'.format(node['deveui']),
                            auth=requests.auth.HTTPBasicAuth(app.config['ORBIWISE_USER'], app.config['ORBIWISE_PASS']))
        if resp.status_code != 200:
            app.logger.error('Unable to retrieve node info for node: {}, deveui: {}'.format(node['_id'], node['deveui']))
        else:
            resp_json = resp.json()
            dev_taken = int.from_bytes(base64.b64decode(resp_json['dataFrame']), byteorder='little')
            if dev_taken != node['number_taken']:
                db.nodes.update_one({'_id': node['_id']},
                                    {'$set': {'last_change': current_time, 'number_taken': dev_taken,
                                              'available': node['number'] - dev_taken}})
                app.logger.info('Updated {}\'s status to {} taken'.format(node['deveui'], dev_taken))


def log_history():
    app.logger.info('Performing logs for all nodes')
    current_time = datetime.now()
    for node in db.nodes.find():
        db.nodes.update({'_id': node['_id']},
                        {'$push': {
                            'history': {
                                'available': node['available'],
                                'timestamp': current_time
                            }}})

scheduler = BackgroundScheduler(daemon=True)
# Explicitly kick off the background thread
scheduler.start()
scheduler.add_job(
    func=poll_nodes,
    trigger=IntervalTrigger(seconds=5),
    id='nodes_polling',
    name='Polls all node status every 5 seconds',
    replace_existing=True)

scheduler.add_job(
    func=log_history,
    trigger=IntervalTrigger(minutes=15),
    id='history_logging',
    name='Logging the status of the nodes every 15 minutes',
    replace_existing=True)


# Shutdown your cron thread if the web process is stopped
def shutdown():
    scheduler.shutdown(wait=False)
    client.close()
atexit.register(shutdown)


def make_geojson(nodes):
    geojson = {'type': 'FeatureCollection',
               'features': []}
    for node in nodes:
        feature = {'type': 'Feature',
                   'geometry': {'type': 'Point',
                                'coordinates': node['geo']},
                   "properties": {"since": node['last_change'],
                                  'id': int(str(node['_id']), base=16),
                                  "name": node['name'],
                                  "color": '#006400' if (node['available'] > 0) else '#800000',
                                  "number": node['available'],
                                  "available": node['available']}}
        if node['lora'] is False:
            feature['properties']['available'] += randint(-2, 2)
            feature['properties']['color'] = '#006400' if (feature['properties']['available'] > 0) else '#800000'
        geojson['features'].append(feature)
    return geojson


@app.route('/', methods=['get'])
def index():
    return render_template('index.html', title='Where the f#ck should I park')


@app.route('/api/nodes/', methods=['get'])
def get_all_nodes():
    nodes = db.nodes.find()
    return dumps(nodes)


@app.route('/api/nodes/near/<int:distance>/', methods=['get'])
def get_nearby_nodes(distance):
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    try:
        lat = float(lat)
        lng = float(lng)
    except:
        abort(400)
    query = {"geo": SON([("$near", [lng, lat]), ("$maxDistance", distance)])}
    if lat is None or lng is None:
        abort(400)
    # nodes = db.command(SON([('geoNear', 'nodes'), ('near', [1, 2])]))['results']
    nodes = db.nodes.find(query)
    return dumps(nodes)


@app.route('/geojson/nodes/near/<int:distance>/', methods=['get'])
def get_nearby_nodes_geojson(distance):
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    try:
        lat = float(lat)
        lng = float(lng)
    except:
        abort(400)
    query = {"geo": SON([("$near", [lng, lat]), ("$maxDistance", distance)])}
    if lat is None or lng is None:
        abort(400)
    # nodes = db.command(SON([('geoNear', 'nodes'), ('near', [1, 2])]))['results']
    nodes = db.nodes.find(query)
    return jsonify(make_geojson(nodes))


@app.route('/geojson/nodes/', methods=['get'])
def get_all_nodes_geojson():
    nodes = db.nodes.find()
    geojson = make_geojson(nodes)
    return jsonify(geojson)


@app.route('/api/nodes/<node_id>/', methods=['get'])
def get_node(node_id):
    try:
        objectid = ObjectId(node_id)
    except InvalidId:
        abort(404)
    node = db.nodes.find_one({'_id': objectid})
    if node is None:
        abort(404)
    return dumps(node)

if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0', use_reloader=False)
