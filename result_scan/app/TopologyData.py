import os
import re
import commands
import json
from collections import defaultdict
from pprint import pprint
import pdb
import itertools
import sys


class TopologyPerVMData:

    def __init__(self,vmTag,buildData):
        self.vmTag = vmTag

        #self.buildData = buildData
        self.installTime = []
        self.upgradeTime = []
        self.cpuStats=[]
        self.memStats=[]
        self.diskStats=[]
        self.pingFailCNT=[]
        self.prepareTime = []

        self.update(buildData)


    def update(self,record):
        if record.get('installTime'):
            self.installTime.append(record['installTime'])
        elif record.get('upgradeTime'):
            self.upgradeTime.append(record['upgradeTime']);
        else:
            raise 'record error'
        #self.installTime.append(record.get('installTime',0));
        #self.upgradeTime.append(record.get('upgradeTime',0));
        self.pingFailCNT.append(record['pingFailCNT']);
        self.prepareTime.append(record['prepareTime']);
        self.cpuStats.append(map(lambda x: x['cpuUsage'], record['statData']));
        self.memStats.append(map(lambda x: x['memUsage'], record['statData']));
        self.diskStats.append(map(lambda x: x['diskUsage'], record['statData']));

        '''self.toolsVersion=record['toolsVersion'];
        self.legacyToolsVersion=record['legacyToolsVersion'];
        self.hostVersion=record['hostVersion'];
        self.hostBuild=record['hostBuild'];'''


class TopologyPerBuildData:

    def __init__(self,build,buildData):
        self.build = build
        self.buildData = buildData

        self.vmsDict = {}
        self.toolsVersion=buildData[0]['toolsVersion'];
        self.toolsBuild=buildData[0]['buildNum'];
        self.legacyToolsBuild=re.sub('[o|s]b-','',buildData[0].get('legacyBuildNum','')); #self.legacyBuild = re.sub("[o|s]b-","",resultobj[0].get("legacyBuildNum"))
        self.legacyToolsVersion=buildData[0]['legacyToolsVersion'];
        self.hostVersion=buildData[0]['hostVersion'];
        self.hostBuild=buildData[0]['hostBuild'];

    def parseBuildData(self):
        for data in self.buildData:
            vmTag = data["vmTag"]
            self.addpenditem(data,vmTag)

    def mergerVMData(self):
        for key,value in self.vmsDict.items():
            if value.installTime:
                value.average_installTime = sum(value.installTime)/len(value.installTime)
                value.average_upgradeTime = 0
                value.gosCNT = len(value.installTime)
            elif value.upgradeTime:
                value.average_upgradeTime = sum(value.upgradeTime)/len(value.upgradeTime)
                value.average_installTime  = 0
                value.average_pingFailCNT  = sum(value.pingFailCNT)/len(value.pingFailCNT)
                value.gosCNT = len(value.upgradeTime)
            value.average_prepareTime = sum(value.prepareTime)/len(value.prepareTime)
            #pdb.set_trace()
            value.average_cpuStats = self.listAverage(value.cpuStats)
            value.average_memStats = self.listAverage(value.memStats)
            value.average_diskStats = self.listAverage(value.diskStats)
    def listAverage(self,statLists):
        result = []
        for entry in itertools.izip_longest(*statLists):
            tmplist = [x for x in entry if x]
            if len(tmplist) > 0:
                result.append(sum(tmplist)/len(tmplist))
            else:
                result.append(0)
        return result


    def addpenditem(self,record,vmTag):
        if not self.vmsDict.get(vmTag):
            self.vmsDict[vmTag] = TopologyPerVMData(vmTag,record)
        else:
            self.vmsDict[vmTag].update(record)


class TopologyData:
    def __init__(self, dataFolder, tptype):
        self.dataFolder = dataFolder
        self.topologyType = tptype
        self.dataFiles = [ path for path in os.listdir(dataFolder) if path.endswith('.data')]
        self.dataList = []
        self.buildDict = defaultdict(list)
        self.resultList = []
        #pdb.set_trace()
        self.readDatas()
        self.parseData()

    def readDatas(self):
        for file in self.dataFiles:
            f = open(os.path.join(self.dataFolder,file),'r')
            self.dataList.append(f.readline()) #one line per file, if merger all data into one file for one build?

    def parseData(self):
        for data in self.dataList:
            jsData = json.loads(data)
            jsRecords = jsData['resultList']
            for rd in jsRecords:
                if self.topologyType != rd['topologyType']:
                    continue
                buildNum = rd['buildNum']
                self.buildDict[buildNum].append(rd)
        #sort the data by build Num, for each build, sort data by vm Tag
        for key,record in self.buildDict.items(): #key is build number
            #for each build 
            #pdb.set_trace()
            tp = TopologyPerBuildData(key,record)
            tp.build = key
            #pdb.set_trace()
            tp.parseBuildData()
            tp.mergerVMData()
            
            self.resultList.append(tp)

    


if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    print ( sys.argv )
    dataFolder = sys.argv[1]# if not sys.argv[1]
    tpdata=TopologyData(dataFolder,'install')
    #pprint(tpdata.buildDict)

