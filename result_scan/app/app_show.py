import os
import json
import commands
import requests
import ConfigParser
import pprint
import sys
import re
import pdb

from flask import Flask,make_response, url_for,redirect
from flask import (render_template,jsonify,request,flash)
from flask_bootstrap import Bootstrap
from pymongo import MongoClient
from TopologyData import TopologyData

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY']='dfsfsadhakhdka'
bootstrap = Bootstrap(app)

dataFolder = './'
dataType = 'install'


@app.route('/')
def draw_result():
    return 'hello'
    
@app.route('/main', methods=['GET', 'POST'])
def draw_main():
    print(request)

    if request.method == "POST":
        return redirect(url_for('canvas_draw',build=request.form["selValue"],type=request.form["TypeValue"]))
		
    ret = requests.get(buildUrl)
    print(ret.text)
    typeList = ["install","upgrade"]
    return render_template('main.html',buildList=json.loads(ret.text),TypeList=typeList)

@app.route('/canvasdraw', methods=['GET', 'POST'])
def canvas_draw():
    try:
        htmlData={}
        htmlData["mark"] = dataType #install or upgrade
        tpdata=TopologyData(dataFolder,dataType)
        if len(tpdata.resultList) < 1:
            return 'data size less than 1'
        sorted(tpdata.resultList, lambda x,y:cmp(x.build,y.build))
        pdb.set_trace()
        #the lesser build is the baseline
        if int(tpdata.resultList[0].build) < int(tpdata.resultList[1].build):
            baselineData = tpdata.resultList[0]
            newlineData = tpdata.resultList[1]
        else:
            baselineData = tpdata.resultList[1]
            newlineData = tpdata.resultList[0]

        htmlData["toolsbuild"] = newlineData.build

        #since the result is based on 2 tools build, and upgrade also involoves old tools. 
        #old/legacy make the logic mess!
        #so, legacy used for only for upgrade.
        #old/new used for the tools for comparation!

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
            if dataType=="upgrade":
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
            if dataType=="upgrade":
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
            if dataType=="install":
                installnewtimearray.append(v["installTime"])
            elif dataType=="upgrade":
                installnewtimearray.append(v["upgradeTime"])
                newFailPingarray.append( round(v["pingFailCNT"],2)) 
            tmp = {}
            tmp["newcpu"]=v["cpuUsage"]
            tmp["newmem"]=v["memUsage"]
            if k in legacytoolsclass:
                tmp["oldcpu"]=legacytoolsclass[k]["cpuUsage"]
                tmp["oldmem"]=legacytoolsclass[k]["memUsage"]
                if dataType=="install":
                    installoldtimearray.append(legacytoolsclass[k]["installTime"])
                elif dataType=="upgrade":
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


            
            clabel = [interval*15 for interval in range(len(tmp["newcpu"]))]
            tmp["cpulabel"]=clabel
            tmp["gosname"]=k
            installGosLabelExt.append(k+timediff)


            oldmemtmp = filter(lambda x: x!=0,tmp["oldmem"])
            newmemtmp = filter(lambda x: x!=0,tmp["newmem"])
            oldcputmp = filter(lambda x: x!=0,tmp["oldcpu"])
            newcputmp = filter(lambda x: x!=0,tmp["newcpu"])
            oldMemarray.append( sum(oldmemtmp)/len(oldmemtmp))
            newMemarray.append( sum(newmemtmp)/len(newmemtmp))
            oldCpuarray.append( sum(oldcputmp)/len(oldcputmp))
            newCpuarray.append( sum(newcputmp)/len(newcputmp))

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
        
        if dataType=="upgrade":
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
        if dataType=="install":
            htmlData["mark"] = "install"
            htmlData["timesubtitle"] = install_time_sub_title
        elif dataType=="upgrade":
            htmlData["mark"] = "upgrade"
            htmlData["timesubtitle"] = upgrade_time_sub_title
            htmlData["upgrade"] = "upgrade"

        htmlData["cpuList"] = statData

        topology_summary_fmt = 'This report generated on two VMtools/Esx build:<br> \
                                The legacy ESX:{esxVerOld}({esxBuildOld}),legacy tools: {toolsVerOld}({toolsBuildOld}) <br> \
                               The new ESX:{esxVersion}({esxBuild}),new tools: {toolsVersion}({toolsBuild})'
        topology_summary=topology_summary_fmt.format(esxVerOld=esxversionold,esxBuildOld=esxbuildold,toolsVerOld=toolsversionold,toolsBuildOld=toolsbuildold,
                                                     esxVersion=esxversion,esxBuild=esxbuild,toolsVersion=toolsversion,toolsBuild=toolsbuild)
        if dataType == "upgrade":
            upg_fmt = '<br><br>For upgrade:<br> \
                      on legacy ESX, the tools build upgrade from {legacyToolsVersionOld}({legacyToolsBuildOld}) to {toolsVersionOld}({toolsBuildOld})<br> \
                      on new ESX, the tools build upgrade from {legacyToolsVersion}({legacyToolsBuild}) to {toolsVersion}({toolsBuild})'
            upg_summary = upg_fmt.format(legacyToolsVersionOld=legacytoolsverionold,legacyToolsBuildOld=legacytoolsbuildold,toolsVersionOld=toolsversionold,toolsBuildOld=toolsbuildold,
                                        legacyToolsVersion=legacytoolsverion,legacyToolsBuild=legacytoolsbuild,toolsVersion=toolsversion,toolsBuild=toolsbuild)
            topology_summary+=upg_summary
        print("got summary string ",topology_summary )
        htmlData["summary"] = topology_summary

        newGOSCountSummary='For New Tools:' + dataType + ' runs on:<br>'
        for k,v in newtoolsclass.items():
            newGOSCountSummary+='{count} {vmnane} VMs, '.format(vmnane=k,count=v["gosCNT"])
        newGOSCountSummary+='<br>'
        oldGOSCountSummary='For Old Tools:'+ dataType + ' runs on:<br>'
        for k,v in legacytoolsclass.items():
            oldGOSCountSummary+='{count} {vmnane} VMs, '.format(vmnane=k,count=v["gosCNT"])
        runFrequencyStats = 'Test runs on following GOSes: <br><br>' + newGOSCountSummary
        runFrequencyStats += oldGOSCountSummary
        htmlData["runFrequencySummary"] = runFrequencyStats

        htmlData["toolsInfo"] = {}
        htmlData["toolsInfo"]["toolsVersionOld"]=toolsversionold
        htmlData["toolsInfo"]["toolsVersion"]=toolsversion

        '''
        toolsbuild = request.args.get('build')
        topotype = request.args.get('type')
        print ("get tools build %s and topotype %s" % (toolsbuild, topotype))
        #step 1: query all data pertains to this build
        #step 2: query all data pertains for tools build 4449150
        #step 3: build all the query data to draw chart
        
        oldData = TopologyData(legacyBuild,type=topotype,restDataUrl=dataUrl)
        newData = TopologyData(toolsbuild,type=topotype,restDataUrl=dataUrl)
        #if ret.status != 202 error
        
        #### install time may different on same gos in the same run, so the stadata length usually not the same
        #### find the the longest one and expand the others!!!
        statStart = 0
        installoldtimearray= []
        installnewtimearray= []
        installGosLabel = []

        installGosLabelExt = []
        
        newtoolsclass={};
        legacytoolsclass={};

        esxversion=''
        legacytoolsverion=''
        toolsversion=''

        esxversionold=''
        legacytoolsverionold=''
        toolsversionold=''

            
        for k,v in newData.data.items():
            newtoolsclass[k] = {}
            newtoolsclass[k]["installTime"] = v["installTime"]
            newtoolsclass[k]["upgradeTime"] = v["upgradeTime"]
            newtoolsclass[k]["cpuUsage"] = v["cpuUsage"]
            newtoolsclass[k]["memUsage"] = v["memUsage"]
            esxversion=v["hostVersion"]
            toolsversion=v["toolsVersion"]
            if topotype=="upgrade":
                newtoolsclass[k]["pingFailCNT"] = v["pingFailCNT"]
                legacytoolsverion=v["legacyToolsVersion"]
            
        for k,v in oldData.data.items():
            legacytoolsclass[k] = {}
            legacytoolsclass[k]["installTime"] = v["installTime"]
            legacytoolsclass[k]["upgradeTime"] = v["upgradeTime"]
            legacytoolsclass[k]["cpuUsage"] = v["cpuUsage"]
            legacytoolsclass[k]["memUsage"] = v["memUsage"]
            legacytoolsclass[k]["pingFailCNT"] = 0#v["pingFailCNT"] if v["pingFailCNT"] else 0
            esxversionold=v["hostVersion"]
            toolsversionold=v["toolsVersion"]
            if topotype=="upgrade":
                legacytoolsclass[k]["pingFailCNT"] = v["pingFailCNT"]
                legacytoolsverionold=v["legacyToolsVersion"]if v["legacyToolsVersion"] else ''
        
        #build html data on new tools. if new tools has the gos, get the result from legacy data.
        #labelvalue should on different GOS


        oldMemarray= []
        newMemarray= []
        oldCpuarray= []
        newCpuarray= []
        oldFailPingarray= []
        newFailPingarray= []
    
        #all the data can set into statData
        statData = []
        
        for k,v in newtoolsclass.items():
            timediff='(0.0%)'
            installGosLabel.append(k)
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
            
            clabel = [interval*15 for interval in range(len(tmp["newcpu"]))]
            tmp["cpulabel"]=clabel
            tmp["gosname"]=k
            installGosLabelExt.append(k+timediff)


            #for cup/mem verage
            oldmemtmp = filter(lambda x: x!=0,tmp["oldmem"])
            newmemtmp = filter(lambda x: x!=0,tmp["newmem"])
            oldcputmp = filter(lambda x: x!=0,tmp["oldcpu"])
            newcputmp = filter(lambda x: x!=0,tmp["newcpu"])
            oldMemarray.append( sum(oldmemtmp)/len(oldmemtmp))
            newMemarray.append( sum(newmemtmp)/len(newmemtmp))
            oldCpuarray.append( sum(oldcputmp)/len(oldcputmp))
            newCpuarray.append( sum(newcputmp)/len(newcputmp))

            statData.append(tmp)
        
        esxbuild = newData.hostBuild
        oldesxbuild = oldData.hostBuild
        print("get both host build:", esxbuild, oldesxbuild)

       
        install_time_sub_title=""
        
        upgrade_time_sub_title=""
        print("install time title ", install_time_sub_title)
        print("upgrade time title ", upgrade_time_sub_title)
 
        
        htmlData={}
        if topotype=="install":
            htmlData["mark"] = "install"
            htmlData["timesubtitle"] = install_time_sub_title
        elif topotype=="upgrade":
            htmlData["mark"] = "upgrade"
            htmlData["timesubtitle"] = upgrade_time_sub_title
            htmlData["upgrade"] = "upgrade"
        htmlData["cpuList"] = statData
        htmlData["gosList"] = installGosLabel
        htmlData["newinstalltime"] = installnewtimearray
        htmlData["oldinstalltime"] = installoldtimearray
        htmlData["toolsbuild"] = toolsbuild
        htmlData["gosinstallTimeDiff"] = installGosLabelExt


        htmlData["newcpuAve"] = newCpuarray
        htmlData["oldcpuAve"] = oldCpuarray
        htmlData["newMemAve"] = newMemarray
        htmlData["oldMemAve"] = oldMemarray

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

        topology_summary_fmt = 'This report generated on two VMtools/Esx build:<br> \
                                The legacy ESX:{legacyEsxVer}({legacyEsxBuild}),legacy tools: {legacyToolsVer}({legacyToolsBuild}) <br> \
                               The new ESX:{newEsxVer}({newEsxBuild}),new tools: {newToolsVer}({newToolsBuild})'
        topology_summary=topology_summary_fmt.format(legacyEsxVer=esxversionold,legacyEsxBuild=oldesxbuild,legacyToolsVer=toolsversionold,legacyToolsBuild=4449150,
                                                     newEsxVer=esxversion,newEsxBuild=esxbuild,newToolsVer=toolsversion,newToolsBuild=toolsbuild)
        if topotype == "upgrade":
            upg_fmt = '<br><br>For upgrade:<br> \
                      on legacy ESX, the tools build upgrade from {oldlegacyToolsVer}({oldlegacyToolsBuild}) to {legacyToolsVer}({legacyToolsBuild})<br> \
                      on new ESX, the tools build upgrade from {oldnewToolsVer}({oldnewToolsBuild}) to {newToolsVer}({newToolsBuild})'
            upg_summary = upg_fmt.format(oldlegacyToolsVer=legacytoolsverionold,oldlegacyToolsBuild=3000743,legacyToolsVer=toolsversionold,legacyToolsBuild=4449150,
                                        oldnewToolsVer=toolsversionold,oldnewToolsBuild=newData.legacyBuild,newToolsVer=toolsversion,newToolsBuild=toolsbuild)
            topology_summary+=upg_summary
        print("got summary string ",topology_summary )
        htmlData["summary"] = topology_summary

        newGOSCountSummary='For New Tools:' + topotype + ' runs on:<br>'
        for k,v in newData.data.items():
            newGOSCountSummary+='{count} {vmnane} VMs, '.format(vmnane=k,count=v["gosCNT"])
        newGOSCountSummary+='<br>'
        oldGOSCountSummary='For Old Tools:'+ topotype + ' runs on:<br>'
        for k,v in oldData.data.items():
            oldGOSCountSummary+='{count} {vmnane} VMs, '.format(vmnane=k,count=v["gosCNT"])
        runFrequencyStats = 'Test runs on following GOSes: <br><br>' + newGOSCountSummary
        runFrequencyStats += oldGOSCountSummary
        htmlData["runFrequencySummary"] = runFrequencyStats
                           
        '''
        return render_template('draw.html',htmlData=htmlData)
    except Exception as e:
        raise
        print("error:" ,e)
        return e,404

if __name__ == '__main__':
    print sys.argv, len(sys.argv)
    if len(sys.argv) == 4:
        port = sys.argv[1]
        dataType = sys.argv[2]
        dataFolder = sys.argv[3]
    else:
        print '''Usage: python sys.argv[0] port type dataFolder
               python sys.argv[0] 5000 install /tmp'''
        sys.exit(1)
    # Bind to PORT if defined, otherwise default to 5000.
    #port = int(config.get('serverinfo', 'server_port'))
    port = int(port)
    app.run(host='0.0.0.0', port=port)

