import os
import sys
import json
import commands
import logging  
import logging.handlers

from flask import Flask,make_response
from flask import jsonify
from flask import request
from pymongo import MongoClient

from bson import BSON
from bson import json_util
from bson.json_util import dumps, loads
import pdb

app = Flask(__name__)
app.debug = True

dbLink = os.environ.get('DATABASE_LINK')
if not dbLink:
	print "dbLink unset"
	sys.exit(1)
dbName = os.environ.get('DATABASE_NAME')
if not dbName:
	print "dbName unset"
	sys.exit(1)
#MongoCollection = os.environ.get('COLLECTION_NAME')
#if not MongoCollection:
#	print "MongoCollection unset"
	sys.exit(1)

LOG_FILE = '/tmp/topo-service.log'
  
handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes = 1024*1024, backupCount = 5) 
fmt = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'  
  
formatter = logging.Formatter(fmt)
handler.setFormatter(formatter)  
  
logger = logging.getLogger('svc')  
logger.addHandler(handler)  
logger.setLevel(logging.DEBUG)

collection_prefix = "topology_result_"

#need add log mechanism.

@app.route('/topo')
def ping():
    return 'topology service is on!'

@app.route('/topo/api/v1.0/results_query', methods=['POST'])
def task_results_query():
    result=""
    result_code = 200

    logger.debug("got request json %s\n" % request.json)
    tools_build = request.json.get('buildNum')
    if not tools_build:
    	return 'parameter buildNum not set\n',201
    topo_type = request.json.get('topologyType')
    if not topo_type:
    	return 'parameter topologyType not set\n',201

    collection_name = collection_prefix+tools_build
    qry_critia = {"buildNum":tools_build,"topologyType":topo_type}

    topo_mode = request.json.get('topologyMode')
    if topo_mode:
        qry_critia["topologyMode"]=topo_mode

    try:
        client = MongoClient(dbLink)
        db = client[dbName]
        collection = db.get_collection(collection_name)
        findResult = collection.find(qry_critia)
        result=dumps(findResult,default=json_util.default)
    except Exception as e:
        logger.error("query error %s" % e)
        result=e.message
        result_code=201
    logger.info("query finish")
    return result,result_code

@app.route('/topo/api/v1.0/esxlist_query', methods=['POST'])
def task_esxlist_query():
    result=""
    result_code = 200

    logger.debug("got request json %s\n" % request.json)
    tools_build = request.json.get('buildNum')
    if not tools_build:
        return 'parameter buildNum not set\n',201

    collection_name = collection_prefix+tools_build
    qry_critia = {"buildNum":tools_build}
    distinct_key = "hostBuild"

    try:
        client = MongoClient(dbLink)
        db = client[dbName]
        collection = db.get_collection(collection_name)
        findResult = collection.distinct(distinct_key,qry_critia)
        result=dumps(findResult,default=json_util.default)
        #result=jsonify(findResult)
        logger.debug("got query result %s" % result)
    except Exception as e:
        logger.error("query error %s" % e)
        result=e.message
        result_code=201
    logger.info("query finish")
    return result,result_code
   
@app.route('/topo/api/v1.0/toolsbuild_query', methods=['GET'])
def task_get_tools_build():

    result_code = 200
    result = ""
    #pdb.set_trace()
    try:
        client = MongoClient(dbLink)
        db = client[dbName]
        collections = db.collection_names(False)
        logger.info("query finish")
        qulified_collections = filter(lambda x: x.startswith(collection_prefix),collections)
        build_numbers = map(lambda x: x[x.rindex("_")+1:],qulified_collections)

        result = dumps(build_numbers,default=json_util.default)
    except Exception, e:
        logger.error("query error ", e)
        result_code=201
    #return jsonify(result),result_code
    return result,result_code

@app.route('/topo/api/v1.0/result_upload', methods=['POST'])
def task_upload():
    result_code = 200
    result = "update success"
    #The db.getCollection() object can access any collection methods.
    #The collection specified may or may not exist on the server. If the collection does not exist, 
    #MongoDB creates it implicitly as part of write operations like db.collection.insertOne().
    try:
        logger.info("got request");
        logger.debug("got request json %s\n" % request.json )
        
        build_num = request.json.get('buildNum')
        if not build_num:
            logger.error("buildNum not set in the request")
            return "buildNum not set",201
        collection_name = collection_prefix+build_num

        client = MongoClient(dbLink)
        db = client[dbName]
        collection = db.get_collection(collection_name)
        updateResult = collection.insert(request.json)
        logger.info("update finish")
    except Exception as e:
        logger.error("update error " , e)
        result=e.message
        result_code=201

    return result,result_code

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('APP_SERVICE_PORT', 5000))
    app.run(host='0.0.0.0', port=port)