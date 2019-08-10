import sys
import signal
import time
import re
import os

CRS_URL='http://crs.jenkins.com:8080'


class CRS_Package_Info:

    setupPkg = ("POTS_GC_Topology_testbed-setup-CPD",)
    crsTriplepackages= (
                      'POTS_GC_Topology_triple_host_linux-CPD',
                      'POTS_GC_Topology_triple_host_windows-CPD',
                  )
    crsSiglepackages= (
                      'POTS_GC_Topology_single_host_linux-CPD',
                      'POTS_GC_Topology_single_host_windows-CPD',
                  )


    linGosTripleParams = [
                {
                    "HOST_01_VM_01_VMNAME": "111395_RHEL6.8_NUM01",
                    "HOST_01_VM_02_VMNAME": "111395_RHEL6.8_NUM02",
                    "HOST_01_VM_03_VMNAME": "111395_RHEL6.8_NUM03",
                    "HOST_01_VM_04_VMNAME": "111395_RHEL6.8_NUM04",
                    "HOST_02_VM_01_VMNAME": "111395_RHEL6.8_NUM11",
                    "HOST_02_VM_02_VMNAME": "111395_RHEL6.8_NUM12",
                    "HOST_02_VM_03_VMNAME": "111395_RHEL6.8_NUM13",
                    "HOST_02_VM_04_VMNAME": "111395_RHEL6.8_NUM14",
                    "HOST_03_VM_01_VMNAME": "111395_RHEL6.8_NUM21",
                    "HOST_03_VM_02_VMNAME": "111395_RHEL6.8_NUM22",
                    "HOST_03_VM_03_VMNAME": "111395_RHEL6.8_NUM23",
                    "HOST_03_VM_04_VMNAME": "111395_RHEL6.8_NUM24",
                    "HOST_01_VM_01_VMLIBRARY_ID": "111395",
                },
                {
                    "HOST_01_VM_01_VMNAME": "111388_Ubuntu16.04_NUM01",
                    "HOST_01_VM_02_VMNAME": "111388_Ubuntu16.04_NUM02",
                    "HOST_01_VM_03_VMNAME": "111388_Ubuntu16.04_NUM03",
                    "HOST_01_VM_04_VMNAME": "111388_Ubuntu16.04_NUM04",
                    "HOST_02_VM_01_VMNAME": "111388_Ubuntu16.04_NUM11",
                    "HOST_02_VM_02_VMNAME": "111388_Ubuntu16.04_NUM12",
                    "HOST_02_VM_03_VMNAME": "111388_Ubuntu16.04_NUM13",
                    "HOST_02_VM_04_VMNAME": "111388_Ubuntu16.04_NUM14",
                    "HOST_03_VM_01_VMNAME": "111388_Ubuntu16.04_NUM21",
                    "HOST_03_VM_02_VMNAME": "111388_Ubuntu16.04_NUM22",
                    "HOST_03_VM_03_VMNAME": "111388_Ubuntu16.04_NUM23",
                    "HOST_03_VM_04_VMNAME": "111388_Ubuntu16.04_NUM24",
                    "HOST_01_VM_01_VMLIBRARY_ID": "111388",
                }
                ]
    linGosSingleParams = [
                {
                    "HOST_01_VM_01_VMNAME": "111395_RHEL6.8_NUM01",
                    "HOST_01_VM_02_VMNAME": "111395_RHEL6.8_NUM02",
                    "HOST_01_VM_03_VMNAME": "111395_RHEL6.8_NUM03",
                    "HOST_01_VM_04_VMNAME": "111395_RHEL6.8_NUM04",
                    "HOST_01_VM_01_VMLIBRARY_ID": "111395",
                },
                {
                    "HOST_01_VM_01_VMNAME": "111388_Ubuntu16.04_NUM01",
                    "HOST_01_VM_02_VMNAME": "111388_Ubuntu16.04_NUM02",
                    "HOST_01_VM_03_VMNAME": "111388_Ubuntu16.04_NUM03",
                    "HOST_01_VM_04_VMNAME": "111388_Ubuntu16.04_NUM04",
                    "HOST_01_VM_01_VMLIBRARY_ID": "111388",
                }
                ]

    winGosTripleParams = [
                {
                    "HOST_01_VM_01_VMNAME": "111326_Windows2012_NUM01",
                    "HOST_01_VM_02_VMNAME": "111326_Windows2012_NUM02",
                    "HOST_02_VM_01_VMNAME": "111326_Windows2012_NUM11",
                    "HOST_02_VM_02_VMNAME": "111326_Windows2012_NUM12",
                    "HOST_03_VM_01_VMNAME": "111326_Windows2012_NUM21",
                    "HOST_03_VM_02_VMNAME": "111326_Windows2012_NUM22",
                    "HOST_01_VM_01_VMLIBRARY_ID": "111326",
                },
                {
                    "HOST_01_VM_01_VMNAME": "111122_Windows7_32bit_NUM01",
                    "HOST_01_VM_02_VMNAME": "111122_Windows7_32bit_NUM02",
                    "HOST_02_VM_01_VMNAME": "111122_Windows7_32bit_NUM11",
                    "HOST_02_VM_02_VMNAME": "111122_Windows7_32bit_NUM12",
                    "HOST_03_VM_01_VMNAME": "111122_Windows7_32bit_NUM21",
                    "HOST_03_VM_02_VMNAME": "111122_Windows7_32bit_NUM22",
                    "HOST_01_VM_01_VMLIBRARY_ID": "111326", #should 111121, but all windows none core-gos is blocked in vmlibrary for security issue.
                }
                ]
    winGosSingleParams = [
                {
                    "HOST_01_VM_01_VMNAME": "111326_Windows2012_NUM01",
                    "HOST_01_VM_02_VMNAME": "111326_Windows2012_NUM02",
                    "HOST_01_VM_01_VMLIBRARY_ID": "111326",
                },
                {
                    "HOST_01_VM_01_VMNAME": "111122_Windows7_32bit_NUM01",
                    "HOST_01_VM_02_VMNAME": "111122_Windows7_32bit_NUM02",
                    "HOST_01_VM_01_VMLIBRARY_ID": "111326",#should 111121
                }
                ]

    def __init__(self):
        pass

    def getPakcages(self,mode,type):
        bothpkg = []
        bothpkg += CRS_Package_Info.setupPkg
        bothpkg += CRS_Package_Info.crsTriplepackages
        bothpkg += CRS_Package_Info.crsSiglepackages
        return bothpkg

    def getTestSetID(self,mode,type,gos):
        ''' only for the full matrix run, using the enhanced mode, ie, run install and upgrade in same test bed,
            other scenario, useing the defalut one in the package'''
        if mode== "triple" and type == "both":
            if gos == "lin":
                return 69486
            if gos == "win":
                return 69487
        if mode== "single" and type == "both":
            if gos == "lin":
                return 69484
            if gos == "win":
                return 69485
        if mode== "triple" and type == "install":
            if gos == "lin":
                return 60083
            if gos == "win":
                return 62329
        if mode== "single" and type == "install":
            if gos == "lin":
                return 62233
            if gos == "win":
                return 62332
        if mode== "triple" and type == "upgrade":
            if gos == "lin":
                return 69478
            if gos == "win":
                return 69479
        if mode== "single" and type == "upgrade":
            if gos == "lin":
                return 69480
            if gos == "win":
                return 69481
        return 0

    def getVMTag(self,vmName):
        print("vmname is ", vmName)
        if vmName.find('111395') != -1:
            return "rhel6.8"
        elif vmName.find('111388') != -1:
            return "ubuntu1604"
        elif vmName.find('111326') != -1:
            return "windows2012"
        elif vmName.find('111122') != -1:
            return "windows7_32bit"
        else:
            return ""

    def getParams(self,mode,gostype):
        if mode== "triple" and gostype == "lin":
            return CRS_Package_Info.linGosTripleParams
        elif mode== "triple" and gostype == "win":
            return CRS_Package_Info.winGosTripleParams
        elif mode== "single" and gostype == "lin":
            return CRS_Package_Info.linGosSingleParams
        elif mode == "single" and gostype == "win":
            return CRS_Package_Info.winGosSingleParams


if  __name__ == '__main__':
    pkg = CRS_Package_Info()
    pkgtest = pkg.getPakcages("triple","install")
    print(pkgtest)
    pkgtest = pkg.getPakcages("triple","upgrade")
    print(pkgtest)
    pkgtest = pkg.getPakcages("triple","both")
    print(pkgtest)
    pkgtest = pkg.getPakcages("single","install")
    print(pkgtest)
    pkgtest = pkg.getPakcages("single","upgrade")
    print(pkgtest)
    pkgtest = pkg.getPakcages("single","both")
    print(pkgtest)
    pkgtest = pkg.getPakcages("both","install")
    print(pkgtest)
    pkgtest = pkg.getPakcages("both","upgrade")
    print(pkgtest)
    pkgtest = pkg.getPakcages("both","both")
    print(pkgtest)

    params = pkg.getParams("triple","lin")
    print(params)
    params = pkg.getParams("triple","win")
    print(params)
    params = pkg.getParams("single","lin")
    print(params)
    params = pkg.getParams("single","win")
    print(params)






