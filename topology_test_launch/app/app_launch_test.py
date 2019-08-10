import os
import json
import commands
import requests
import ConfigParser
import pika

from flask import Flask,make_response, url_for,redirect
from flask import (render_template,jsonify,request,flash)
from flask_bootstrap import Bootstrap
import logging
import logging.handlers

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY']='dfsfsadhakhdka'
bootstrap = Bootstrap(app)

rabbitmq_host = os.environ.get('RABBITMQ_HOST')
if not rabbitmq_host:
    print "RABBITMQ_HOST unset"
    sys.exit(1)
rabbitmq_port = os.environ.get('RABBITMQ_PORT')
if not rabbitmq_port:
    print "RABBITMQ_PORT unset"
    sys.exit(1)
rabbitmq_vhost = os.environ.get('RABBITMQ_VHOST')
if not rabbitmq_vhost:
    print "DATA_REST_URL RABBITMQ_VHOST"
    sys.exit(1)
rabbitmq_user = os.environ.get('RABBITMQ_USER')
if not rabbitmq_user:
    print "RABBITMQ_USER unset"
    sys.exit(1)
rabbitmq_passwd = os.environ.get('RABBITMQ_PASSWORD')
if not rabbitmq_passwd:
    print "RABBITMQ_PASSWORD unset"
    sys.exit(1)
rabbitmq_queue = os.environ.get('RABBITMQ_QUEUE')
if not rabbitmq_queue:
    print "RABBITMQ_QUEUE unset"
    sys.exit(1)

LOG_FILE = '/tmp/runtest-topo-launch.log'
  
handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes = 1024*1024, backupCount = 5) 
fmt = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'  
  
formatter = logging.Formatter(fmt)
handler.setFormatter(formatter)  
  
logger = logging.getLogger('svc')  
logger.addHandler(handler)  
logger.setLevel(logging.DEBUG)


@app.route('/')
def draw_result():
    return redirect(url_for('draw_main'))
    
@app.route('/runtest-topo/api/v1.0/launch', methods=['GET', 'POST'])
def draw_main():
    logger.debug("got request %s" % request)

    if request.method == "POST":
        logger.debug(" ",request.form["selValue"],request.form["TypeValue"],
                  request.form["hostbuild"],request.form["vcbuild"],
                  request.form["legacytoolsbuild"],request.form["toolsbuild"])

        credentials = pika.PlainCredentials(rabbitmq_user,rabbitmq_passwd)
        parameters = pika.ConnectionParameters(rabbitmq_host,rabbitmq_port,rabbitmq_vhost,credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        parms = {}
        parms['x-max-priority']=10
        channel.queue_declare(queue=rabbitmq_queue,durable=True,arguments=parms)
        prop=pika.spec.BasicProperties()
        prop.delivery_mode=2
        prop.priority=2
        channel.basic_publish(exchange='',routing_key=rabbitmq_queue,body=json.dumps(request.form),properties=prop)
        connection.close()
        logger.debug("got request message %s" % json.dumps(request.form) )
        return 'request has been added to message queue', 200
		
    #typeList = ["both", "install","upgrade"]
    #modeList = ["both","triple host","single host"]
    typeList = ["both"]
    modeList = ["both"]
    return render_template('main.html',ModeList=modeList,TypeList=typeList)

@app.route('/runtest-topo/api/v1.0/ping', methods=['GET', 'POST'])
def ping():
    logger.info("got request message to ping this server")
    return "ping success", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

