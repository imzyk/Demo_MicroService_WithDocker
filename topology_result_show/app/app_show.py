import os
import sys
import json
import commands
import requests
import ConfigParser

from flask import Flask,make_response, url_for,redirect
from flask import (render_template,jsonify,request,flash)
from flask_bootstrap import Bootstrap
from pymongo import MongoClient
from TopologyData import TopologyData
import logging  
import logging.handlers

from bson import json_util
from bson.json_util import dumps, loads
import pdb
import pprint

app = Flask(__name__)
app.debug = True

app.config['SECRET_KEY']='dfsfsadhakhdka'
bootstrap = Bootstrap(app)


build_REST_URL = os.environ.get('BUILD_REST_URL')
if not build_REST_URL:
    print "BUILD_REST_URL unset"
    sys.exit(1)
ESX_REST_URL = os.environ.get('ESX_REST_URL')
if not ESX_REST_URL:
    print "ESX_REST_URL unset"
    sys.exit(1)
data_REST_URL = os.environ.get('DATA_REST_URL')
if not data_REST_URL:
    print "DATA_REST_URL unset"
    sys.exit(1)



LOG_FILE = '/tmp/topo-result-draw.log'
  
handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes = 1024*1024, backupCount = 5) 
fmt = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'  
  
formatter = logging.Formatter(fmt)
handler.setFormatter(formatter)  
  
logger = logging.getLogger('draw')  
logger.addHandler(handler)  
logger.setLevel(logging.DEBUG)  

rest_head = {'Content-type':'application/json',
            'Accept':'application/json'}


@app.route('/result/')
def draw_result():
    return redirect(url_for('draw_main'))
    
@app.route('/result/main', methods=['GET', 'POST'])
def draw_main():
    logger.debug(request)

    if request.method == "POST":
        logger.debug("form submitted")
        logger.debug(request.form)
        return redirect(url_for('canvas_draw',build=request.form["buildValue"],esxbuild=request.form["esxValue"],
            type=request.form["typeValue"],legacybuild=request.form["legacyValue"],legacyesxbuild=request.form["legacyEsxValue"],
            mode=request.form["modeValue"]))
		
    ret = requests.get(build_REST_URL)
    #ESX build should changed based on the selected tools build!
    #should get the data and get the return value.
    #!!!!! Also need get the host build number for newer build and legacy build!!!!
    logger.debug(ret.text)

    esxList = []
    tools_list = json.loads(ret.text)
    if len(tools_list) > 0:
        esxList = get_hostbuild(tools_list[0])

    typeList = ["install","upgrade"]
    modeList = ["single&tripe Host","single Host","triple Host"]
    return render_template('main.html',buildList=json.loads(ret.text),esxList=esxList,
         legacyList=json.loads(ret.text),legacyEsxList=esxList,TypeList=typeList,ModeList=modeList)

@app.route('/result/host_builds', methods=['GET'])
def draw_hostbuild():

    logger.debug("got request for builds ")
    #tools_build = request.data
    tools_build = request.args.get('tools_build')
    logger.debug(request.data)
    if not tools_build:
        logger.debug("got null tools build number, return blank host build list")
        return jsonify([])

    logger.debug("got request for esx build list on tools build %s" % tools_build)


    payload = {"buildNum": tools_build.replace("\"","")}
    payld = json.dumps(payload)
    result = requests.post(ESX_REST_URL,headers=rest_head,data=payld)
    #ret = requests.get(ESX_REST_URL)
    logger.debug("got esx build list %s" % result.text)

    bld_list=json.loads(result.text)  #load json string as a python list object

    #host_build = ['12345','67890']
    #ESX build should changed based on the selected tools build!
    #should get the data and get the return value.
    #!!!!! Also need get the host build number for newer build and legacy build!!!!

    return  jsonify(bld_list)
    #return jsonify(host_build) #workable


@app.route('/result/canvasdraw', methods=['GET', 'POST'])
def canvas_draw():
    try:
        logger.debug("got redirect")
        toolsbuild = request.args.get('build')
        topotype = request.args.get('type')
        legacybuild = request.args.get('legacybuild')
        mode = request.args.get('mode')

        esxbuild = request.args.get('esxbuild')
        legacyesxbuild = request.args.get('legacyesxbuild')
        logger.info ("get tools build %s, legacy build %s, topotype %s, mode %s esxbuild %s legacyesxbuild %s" % 
            (toolsbuild, legacybuild, topotype, mode, esxbuild, legacyesxbuild))
        
        baselineData = TopologyData(legacybuild,mode=mode,server_build=legacyesxbuild,type=topotype,restDataUrl=data_REST_URL).tp
        newlineData = TopologyData(toolsbuild,mode=mode,server_build=esxbuild,type=topotype,restDataUrl=data_REST_URL).tp
        

        htmlData={}
        htmlData["mark"] = topotype #install or upgrade

        htmlData["toolsbuild"] = newlineData.build
        htmlData["toolsbuildold"] = baselineData.build

        legacytoolsclass={};

        esxbuild = ''
        esxversion=''
        toolsbuild = ''
        toolsversion=''
        legacytoolsbuild = ''
        legacytoolsverion=''

        esxbuildold = ''
        esxversionold=''
        toolsbuildold = ''
        toolsversionold=''
        legacytoolsbuildold = ''
        legacytoolsverionold=''


        oldFailPingarray= []
        newFailPingarray= []

            
        htmlData["gosList"] = []
        goslist = []
        for k,v in baselineData.vmsDict.items():
            goslist.append(k)
            legacytoolsclass[k] = {}
            legacytoolsclass[k]["installTime"] = v.average_installTime/1000
            legacytoolsclass[k]["upgradeTime"] = v.average_upgradeTime/1000
            legacytoolsclass[k]["cpuUsage"] = v.average_cpuStats
            legacytoolsclass[k]["memUsage"] = v.average_memStats
            legacytoolsclass[k]["gosCNT"] = v.gosCNT
            if topotype=="upgrade":
                legacytoolsclass[k]["pingFailCNT"] = v.average_pingFailCNT
                pass
            pprint.pprint('data stats for GOS %s' % k)
            pprint.pprint(legacytoolsclass[k])
        
        esxbuildold = baselineData.hostBuild
        esxversionold=baselineData.hostVersion
        toolsbuildold = baselineData.toolsBuild
        toolsversionold=baselineData.toolsVersion
        legacytoolsbuildold=baselineData.legacyToolsBuild
        legacytoolsverionold=baselineData.legacyToolsVersion

        htmlData["gosList"] = goslist
        newtoolsclass={};

            
        for k,v in newlineData.vmsDict.items():
            newtoolsclass[k] = {}
            newtoolsclass[k]["installTime"] = v.average_installTime/1000
            newtoolsclass[k]["upgradeTime"] = v.average_upgradeTime/1000
            newtoolsclass[k]["cpuUsage"] = v.average_cpuStats
            newtoolsclass[k]["memUsage"] = v.average_memStats
            newtoolsclass[k]["gosCNT"] = v.gosCNT
            if topotype=="upgrade":
                newtoolsclass[k]["pingFailCNT"] = v.average_pingFailCNT
                pass
            pprint.pprint('data stats for GOS %s' % k)
            pprint.pprint(newtoolsclass[k])


        esxbuild = newlineData.hostBuild
        esxversion=newlineData.hostVersion
        toolsbuild = newlineData.toolsBuild
        toolsversion=newlineData.toolsVersion
        legacytoolsbuild=newlineData.legacyToolsBuild
        legacytoolsverion=newlineData.legacyToolsVersion

        installoldtimearray= []
        installnewtimearray= []
        installGosLabelExt = []


        statData = []
        #for cup/mem verage

        oldMemarray= []
        newMemarray= []
        oldCpuarray= []
        newCpuarray= []

        for k,v in newtoolsclass.items():
            timediff='(0.0%)'
            if topotype=="install":
                installnewtimearray.append(v["installTime"])
            elif topotype=="upgrade":
                installnewtimearray.append(v["upgradeTime"])
                newFailPingarray.append( round(v["pingFailCNT"],2)) 
            tmp = {}
            tmp["newcpu"]=v["cpuUsage"]
            tmp["newmem"]=v["memUsage"]
            if k in legacytoolsclass:
                tmp["oldcpu"]=legacytoolsclass[k]["cpuUsage"]
                tmp["oldmem"]=legacytoolsclass[k]["memUsage"]
                if topotype=="install":
                    installoldtimearray.append(legacytoolsclass[k]["installTime"])
                elif topotype=="upgrade":
                    installoldtimearray.append(legacytoolsclass[k]["upgradeTime"])
                    oldFailPingarray.append( round(legacytoolsclass[k]["pingFailCNT"],2)) 
                if installoldtimearray[-1] < installnewtimearray[-1]:
                    #increase
                    timediff="(+{:.2%})".format(float(installnewtimearray[-1]-installoldtimearray[-1])/installoldtimearray[-1])
                elif installoldtimearray[-1] > installnewtimearray[-1]:
                    #drop
                    timediff="(-{:.2%})".format(float(installoldtimearray[-1]-installnewtimearray[-1])/installoldtimearray[-1])
            else:
                tmp["oldcpu"]=[]
                tmp["oldmem"]=[]
                installoldtimearray.append(0)


            
            clabel = [interval*5 for interval in range(len(tmp["newcpu"]))]
            tmp["cpulabel"]=clabel
            tmp["gosname"]=k
            installGosLabelExt.append(k+timediff)


            oldmemtmp = filter(lambda x: x!=0,tmp["oldmem"])
            newmemtmp = filter(lambda x: x!=0,tmp["newmem"])
            oldcputmp = filter(lambda x: x!=0,tmp["oldcpu"])
            newcputmp = filter(lambda x: x!=0,tmp["newcpu"])
            print 'sum is %d, len is %d' % (sum(oldmemtmp),len(oldmemtmp) )
            arrvalue = sum(oldmemtmp)/len(oldmemtmp) if len(oldmemtmp) !=0 else 0
            oldMemarray.append( arrvalue )
            arrvalue = sum(newmemtmp)/len(newmemtmp) if len(newmemtmp) !=0 else 0
            newMemarray.append( arrvalue)
            arrvalue = sum(oldcputmp)/len(oldcputmp) if len(oldcputmp) !=0 else 0
            oldCpuarray.append( arrvalue )
            arrvalue = sum(newcputmp)/len(newcputmp) if len(newcputmp) != 0 else 0
            newCpuarray.append( arrvalue)

            statData.append(tmp)
            

        htmlData["gosList"] = goslist
        htmlData["newinstalltime"] = installnewtimearray
        htmlData["oldinstalltime"] = installoldtimearray
        htmlData["gosinstallTimeDiff"] = installGosLabelExt

        #for test purpose
        htmlData["newcpuAve"] = newCpuarray #USED to gen the bar chart

        htmlData["newcpuAve"] = newCpuarray
        htmlData["oldcpuAve"] = oldCpuarray
        htmlData["newMemAve"] = newMemarray
        htmlData["oldMemAve"] = oldMemarray


        installGosLabel=goslist
        memcmpLabel =[]
        cpucmpLabel = []
        #calculate the difference for mem/cpu usage, and setinto the label
        for idx,gos in enumerate(installGosLabel):
            oldmem = oldMemarray[idx]
            newmem = newMemarray[idx]
            memdiff='(0.00%)'
            if oldmem < newmem:
                memdiff="(+{:.2%})".format(float(newmem-oldmem)/newmem)
            elif oldmem > newmem:
                memdiff="(-{:.2%})".format(float(oldmem-newmem)/newmem)
            memcmpLabel.append(gos+memdiff)
            oldcpu = oldCpuarray[idx]
            newcpu = newCpuarray[idx]
            cpudiff='(0.00%)'
            if oldcpu < newcpu:
                cpudiff="(+{:.2%})".format(float(newcpu-oldcpu)/newcpu)
            elif oldcpu > newcpu:
                cpudiff="(-{:.2%})".format(float(oldcpu-newcpu)/newcpu)
            cpucmpLabel.append(gos+cpudiff)


        htmlData["memCmpLabel"] = memcmpLabel
        htmlData["cpuCmpLabel"] = cpucmpLabel


        wingos = []
        
        if topotype=="upgrade":
            print("gos ping reuslt", installGosLabel,newFailPingarray,oldFailPingarray)
            gosLen = len(installGosLabel)
            for idx,gos in enumerate(installGosLabel[::-1]):
                if gos.find("win") == -1:  #linux
                   print("pop index at ", gosLen-1-idx)
                   newFailPingarray.pop(gosLen-1-idx)
                   oldFailPingarray.pop(gosLen-1-idx)
                else:
                    wingos.append(gos)
            wingos.reverse()
            print("win gos and ping reuslt", wingos,newFailPingarray,oldFailPingarray)
        
        htmlData["newfailPing"] = newFailPingarray
        htmlData["oldfailPing"] = oldFailPingarray
        htmlData["wingosList"] = wingos


        install_time_sub_title="ESX {0}({1}): VMTools {2}({3}) VS ESX {4}({5}): VMTools {6}({7})".format(esxversionold,esxbuildold,
            toolsversionold,toolsbuildold,esxversion,esxbuild,toolsversion,toolsbuild)

        upgrade_time_sub_title="ESXi {0}({1}): VMTools {2}({3}) -> {4}({5}) VS ESXi {6}({7}): VMTools {8}({9}) -> {10}({11})".format(esxversionold,esxbuildold,
            legacytoolsverionold,legacytoolsbuildold,toolsversionold,toolsbuildold,esxversion,esxbuild,legacytoolsverion,legacytoolsbuild,toolsversion,toolsbuild)
        if topotype=="install":
            htmlData["mark"] = "install"
            htmlData["timesubtitle"] = install_time_sub_title
        elif topotype=="upgrade":
            htmlData["mark"] = "upgrade"
            htmlData["timesubtitle"] = upgrade_time_sub_title
            htmlData["upgrade"] = "upgrade"

        htmlData["cpuList"] = statData

        topology_summary_fmt = 'This report generated on two VMtools/Esx build:<br> \
                                The legacy ESX:{esxVerOld}({esxBuildOld}),legacy tools: {toolsVerOld}({toolsBuildOld}) <br> \
                               The new ESX:{esxVersion}({esxBuild}),new tools: {toolsVersion}({toolsBuild})'
        topology_summary=topology_summary_fmt.format(esxVerOld=esxversionold,esxBuildOld=esxbuildold,toolsVerOld=toolsversionold,toolsBuildOld=toolsbuildold,
                                                     esxVersion=esxversion,esxBuild=esxbuild,toolsVersion=toolsversion,toolsBuild=toolsbuild)
        if topotype == "upgrade":
            upg_fmt = '<br><br>For upgrade:<br> \
                      on legacy ESX, the tools build upgrade from {legacyToolsVersionOld}({legacyToolsBuildOld}) to {toolsVersionOld}({toolsBuildOld})<br> \
                      on new ESX, the tools build upgrade from {legacyToolsVersion}({legacyToolsBuild}) to {toolsVersion}({toolsBuild})'
            upg_summary = upg_fmt.format(legacyToolsVersionOld=legacytoolsverionold,legacyToolsBuildOld=legacytoolsbuildold,toolsVersionOld=toolsversionold,toolsBuildOld=toolsbuildold,
                                        legacyToolsVersion=legacytoolsverion,legacyToolsBuild=legacytoolsbuild,toolsVersion=toolsversion,toolsBuild=toolsbuild)
            topology_summary+=upg_summary
        print("got summary string ",topology_summary )
        htmlData["summary"] = topology_summary

        newGOSCountSummary='For New Tools:' + topotype + ' runs on:<br>'
        for k,v in newtoolsclass.items():
            newGOSCountSummary+='{count} {vmnane} VMs, '.format(vmnane=k,count=v["gosCNT"])
        newGOSCountSummary+='<br>'
        oldGOSCountSummary='For Old Tools:'+ topotype + ' runs on:<br>'
        for k,v in legacytoolsclass.items():
            oldGOSCountSummary+='{count} {vmnane} VMs, '.format(vmnane=k,count=v["gosCNT"])
        runFrequencyStats = 'Test runs on following GOSes: <br><br>' + newGOSCountSummary
        runFrequencyStats += oldGOSCountSummary
        htmlData["runFrequencySummary"] = runFrequencyStats

        htmlData["toolsInfo"] = {}
        htmlData["toolsInfo"]["toolsVersionOld"]=toolsversionold
        htmlData["toolsInfo"]["toolsVersion"]=toolsversion

        return render_template('draw.html',htmlData=htmlData)
    except Exception as e:
        raise
        print("error:" ,e)
        return e,404


def get_hostbuild(tools_build):

    logger.debug("got request for esx build list on tools build %s" % tools_build)


    payload = {"buildNum": tools_build.replace("\"","")}
    payld = json.dumps(payload)
    result = requests.post(ESX_REST_URL,headers=rest_head,data=payld)
    logger.debug("got esx build list %s" % result.text)

    bld_list=json.loads(result.text)  #load json string as a python list object

    #host_build = ['12345','67890']
    #ESX build should changed based on the selected tools build!
    #should get the data and get the return value.
    #!!!!! Also need get the host build number for newer build and legacy build!!!!
    return bld_list

    #return jsonify(host_build) #workable
if __name__ == '__main__':
    port = int(os.environ.get('APP_SERVICE_PORT', 5000))
    app.run(host='0.0.0.0', port=port)

