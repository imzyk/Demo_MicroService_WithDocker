import sys
import signal
import time
import re
import os
import errno
import logging
import traceback
import xmlrpclib
import threading
import httplib, urllib, urllib2
from urllib2 import HTTPError,URLError
from socket import error as SocketError
from multiprocessing.pool import ThreadPool
import pprint
from jenkinsapi import api
from CRS_Package_Info import CRS_Package_Info

CRS_URL='http://crs.jenkins.com:8080'
Debug=False


class CRSBuildTask:
    def __init__(self, debugMode, logger, testIDs,params,pkgName):
        self.logger = logger
        self.jobParams = params
        self.packageName = pkgName

    def buildCrsPackage(self,event):
        try:
            self.logger.debug('jobParams: %s, %s' % (self.jobParams, self.packageName))
        except AttributeError:
            self.logger.error('Get error %s when fetching parameters ' % traceback.format_exc())
            return
        req_data = urllib.urlencode(self.jobParams)
        self.logger.debug("request data : %s" % req_data)
        crsPackage = self.packageName
        crsUrl = CRS_URL + '/job/' + crsPackage + '/buildWithParameters'
        self.logger.debug('CRS URL used is ' ,crsUrl)
        req = urllib2.Request(crsUrl,req_data)
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        count = 0
        queueIDCount = 0
        if Debug:
            return

        # Firstly try to push it into queue
        while count < 3:

            self.logger.debug(count,' time build with link ',crsUrl,  " ",req_data)

            try:
                response = urllib2.urlopen(req)
                if response.code == 201:
                    self.logger.debug('Build response successfully')
                else:
                    self.logger.error('Not expected response code %s ' % response.code)
                    return
                self.logger.debug('Build parameter response %s ' % response.info())
                queueLocation = response.info().get('Location')
                queueUrl = queueLocation + 'api/json'

                jobId = None

                while True:
                    try:
                        queueResp = urllib2.urlopen(queueUrl)
                        queueInfo = queueResp.read()
                        self.logger.debug(queueInfo)
                        time.sleep(5) # wait till it past quiet period
                        if re.search('"why":null', queueInfo, re.I):
                            jobGrp = re.search('"executable":{"number":(\d+),', queueInfo, re.I)
                            if jobGrp:
                                jobId = jobGrp.groups()[0]
                                self.logger.info('Get jobId %s for package %s' % (jobId, crsPackage))
                                break
                            elif re.search('"cancelled":true', queueInfo, re.I):
                                self.logger.info('******** One job cancelled during quieting...*******')
                                return
                        else:
                            #1. "why":"In the quiet period. Expires in ..."
                            #2. "why":"Waiting for next available executor on..."
                            self.logger.debug('wait till past quieting or waiting for executor...')
                    except SocketError as se:
                        if se.errno != errno.ECONNRESET and se.errno != errno.ETIMEDOUT:
                            raise
                        self.logger.warning('Server too busy. Torture it a little bit later')
                        time.sleep(5)
                    except URLError as ue:
                        if re.search('Errno 104', ue.reason, re.I) \
                                or re.search('Errno 110', ue.reason, re.I):
                            self.logger.warning('Server too busy. Access it a little bit later')
                            time.sleep(5)
                        else:
                            raise

                # Now I got a jobId
                jenkins = api.Jenkins(CRS_URL)
                job = jenkins.get_job(crsPackage)
                currentBuild = job.get_build(int(jobId))
                self.logger.debug(currentBuild)
                jobLink = CRS_URL + '/job/' + crsPackage + '/' + jobId

                while True:
                    try:
                        while currentBuild.is_running() :
                           self.logger.info('Build %s for package %s is running' % (jobId, crsPackage))
                           time.sleep(30)
                        break
                    except Exception as ex:
                        if hasattr(ex, 'message'):
                            msg = repr(ex.message)
                            self.log.debug('Got exception of %s' % msg)
                            if re.search('JenkinsAPIException', msg, re.I):
                                self.logger.debug('Temp error from message %s , ignore it' % msg)
                            else:
                                raise
                        elif re.search('JenkinsAPIException', repr(ex), re.I):
                            self.logger.debug('Temp error from ex %s, ignore it' % ex)
                        else:
                            info = traceback.format_exc()
                            if re.search('JenkinsAPIException', info, re.I):
                                self.logger.debug('Temp error from stacktrace %s, ignore it' % info)
                            else:
                                raise
                self.logger.info('current job status %s' % currentBuild.get_status() )
                jobStatus = currentBuild.get_status().strip().upper()

                self.logger.info('Build %s completed with status %s.' % (jobLink, jobStatus))
                if jobStatus == 'SUCCESS':
                    self.logger.info('job success,  run next job')
                else:
                    self.logger.info('job failure,  run next job')
                return

            except HTTPError as err:
                errMsg = err.read()
                self.logger.debug('Get HTTP error %s ' % errMsg)
                #Ignore other 500 error
                if err.code == 500 and re.search('IllegalArgumentException', errMsg, re.I):
                    self.logger.info('!!!HTTP 500 error!!! Caused by illegal argument and \
                            check configuration of %s !!!' % crsUrl)
                    return
                elif err.code == 404:
                    self.logger.info('!!!HTTP 404 error!!! Which is usually caused by unmatched packagename!!!')
                    return
            except xmlrpclib.Fault as xmlErr:
                self.logger.error("A fault occurred: Fault code: "
                        "%s Fault string: %s. Retry until success."
                        % (err.faultCode, err.faultString))
            except Exception as ex:
                if re.match('HTTPSConnectionPool', repr(ex), re.I):
                    self.logger.info('Temp https connection issue %s. Retry until success.' % ex)
                else:
                    self.logger.error('!!!Hitting abnormal and exit %s:%s !!!' % (ex, traceback.format_exc()))
                    return
class CRSBuildLauncher:
    def __init__(self):
        pass

    def submitCrsPackageJob(self,pkgInfo,paramInfo,logger):
        #logger = logging.getLogger('Launcher')
        logger.setLevel(logging.DEBUG)
        #logger.setLevel(logging.INFO)
        logging.basicConfig()
        crsPkgInfo = CRS_Package_Info();
        crspackages = crsPkgInfo.getPakcages(pkgInfo["mode"],pkgInfo["type"])

        for crsPkg in crspackages:
            logger.debug("got crs package %s to run" % crsPkg)
            #continue
            if crsPkg.find('_linux') != -1 and crsPkg.find("_triple_")!=-1 :
                testsetid = crsPkgInfo.getTestSetID("triple",pkgInfo["type"],"lin")
                logger.debug("got testset ID ",testsetid)
                for param in crsPkgInfo.getParams("triple","lin"):  #each mode/type have two gos to tun
                    params = {}
                    params.update(param)
                    params.update(paramInfo)
                    params.update({"VM_TAG":crsPkgInfo.getVMTag(param['HOST_01_VM_01_VMNAME'])})
                    if testsetid > 0 :
                        params.update({"qc.testset.ids":testsetid})
                    logger.debug("run pkg %s ---------------------------" % crsPkg )
                    build = CRSBuildTask(None,logger,None,params,crsPkg)
                    build.buildCrsPackage(None)

            elif crsPkg.find('_linux') != -1 and crsPkg.find("_single_")!=-1 :
                testsetid = crsPkgInfo.getTestSetID("single",pkgInfo["type"],"lin")
                logger.debug("got testset ID ",testsetid)
                for param in crsPkgInfo.getParams("single","lin"):
                    params = {}
                    params.update(param)
                    params.update(paramInfo)
                    params.update({"VM_TAG":crsPkgInfo.getVMTag(param['HOST_01_VM_01_VMNAME'])})
                    if testsetid > 0 :
                        params.update({"qc.testset.ids":testsetid})
                    logger.debug("run pkg %s ---------------------------" % crsPkg )
                    build = CRSBuildTask(None,logger,None,params,crsPkg)
                    build.buildCrsPackage(None)
            elif crsPkg.find('_windows') != -1 and crsPkg.find("_triple_")!=-1:
                testsetid = crsPkgInfo.getTestSetID("triple",pkgInfo["type"],"win")
                logger.debug("got testset ID ",testsetid)
                for param in crsPkgInfo.getParams("triple","win"):
                    params = {}
                    params.update(param)
                    params.update(paramInfo)
                    params.update({"VM_TAG":crsPkgInfo.getVMTag(param['HOST_01_VM_01_VMNAME'])})
                    if testsetid > 0 :
                        params.update({"qc.testset.ids":testsetid})
                    logger.debug("run pkg %s ---------------------------" % crsPkg )
                    build = CRSBuildTask(None,logger,None,params,crsPkg)
                    build.buildCrsPackage(None)
            elif crsPkg.find('_windows') != -1 and crsPkg.find("_single_")!=-1:
                testsetid = crsPkgInfo.getTestSetID("single",pkgInfo["type"],"win")
                logger.debug("got testset ID ",testsetid)
                for param in crsPkgInfo.getParams("single","win"):
                    params = {}
                    params.update(param)
                    params.update(paramInfo)
                    params.update({"VM_TAG":crsPkgInfo.getVMTag(param['HOST_01_VM_01_VMNAME'])})
                    if testsetid > 0 :
                        params.update({"qc.testset.ids":testsetid})
                    logger.debug("run pkg %s ---------------------------" % crsPkg )
                    build = CRSBuildTask(None,logger,None,params,crsPkg)
                    build.buildCrsPackage(None)
            elif crsPkg.find('setup') != -1:
                logger.debug("run pkg %s ---------------------------" % crsPkg )
                build = CRSBuildTask(None,logger,None,paramInfo,crsPkg)
                build.buildCrsPackage(None)



if  __name__ == '__main__':
    logger = logging.getLogger('Launcher')
    logger.setLevel(logging.DEBUG)
    logging.basicConfig()
    #Debug=True

    launcher = CRSBuildLauncher();

    jobParams = {
                    'HOST_01_BUILDNUM':"6306755",
                    'VMTOOLS_BUILDNUM': "ob-6082533",
                    'VMTOOLS_LEGACY_BUILDNUM': "ob-4449150",
                    'VC_01_BUILDNUM': "ob-6306719",
                    'ALPS_BUILD_NUM': "sb-10425232"
                }
    launcher.submitCrsPackageJob({"mode":"both","type":"both"}, jobParams)






