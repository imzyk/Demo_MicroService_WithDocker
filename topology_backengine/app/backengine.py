import os
import sys
import json
import pika
import commands
import requests
import pdb

from crs_launch import CRSBuildLauncher
import CRS_Package_Info
import logging
import logging.handlers


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
topo_rest_service = os.environ.get('TOPOLOGY_SERVICE')
if not topo_rest_service:
    print "TOPOLOGY_SERVICE unset"
    sys.exit(1)
rabbitmq_queue = os.environ.get('RABBITMQ_QUEUE')
if not rabbitmq_queue:
    print "RABBITMQ_QUEUE unset"
    sys.exit(1)

LOG_FILE = '/tmp/topology_back_engine.log'
  
handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes = 1024*1024, backupCount = 5) 
fmt = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'  
  
formatter = logging.Formatter(fmt)
handler.setFormatter(formatter)  
  
logger = logging.getLogger('svc')  
logger.addHandler(handler)  
logger.setLevel(logging.DEBUG)

credentials = pika.PlainCredentials(rabbitmq_user,rabbitmq_passwd)
parameters = pika.ConnectionParameters(rabbitmq_host,rabbitmq_port,rabbitmq_vhost,credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
parms = {}
parms['x-max-priority']=10
channel.queue_declare(queue=rabbitmq_queue,durable=True,arguments=parms)

def callback(ch, method, properties, body):
   try:
      logger.debug("Received request %r" % body)
      bd = json.loads(body)
      typemode={}
      if bd["selValue"] == "triple host":
         typemode["mode"]="tripe"
      elif bd["selValue"] == "single host":
         typemode["mode"]="single"
      elif bd["selValue"] == "both":
         typemode["mode"]="both"

      if bd["TypeValue"] == "install":
         typemode["type"]="install"
      elif bd["selValue"] == "upgrade":
         typemode["type"]="upgrade"
      elif bd["selValue"] == "both":
         typemode["type"]="both"
      params = {
         'HOST_01_BUILDNUM':bd["hostbuild"],
         'VMTOOLS_BUILDNUM': bd["toolsbuild"],
         'VMTOOLS_LEGACY_BUILDNUM': bd["legacytoolsbuild"],        
         'VC_01_BUILDNUM': bd["vcbuild"],
         'ALPS_BUILD_NUM': bd["alpsbuild"],
         'TOPOLOGY_REST_SERVER': topo_rest_service
         }
      if "TOPO_EMAIL_ADDRESS" in bd:
          #email user
          pass
      crslauncher = CRSBuildLauncher();
      crslauncher.submitCrsPackageJob(typemode, params,logger)
   except Exception as e:
      logger.error(" got exception %s" % e)

channel.basic_consume(callback,queue=rabbitmq_queue,no_ack=True)
channel.start_consuming()

