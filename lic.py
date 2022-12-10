import requests
import json
from itertools import zip_longest
import difflib
import yaml
import re
import time
import csv


from auth_header import Authentication as auth
from operations import Operation
from license_class import getData
from license_class import postData
from query import queryPayload
#from clean_class import parseData

#  data= '{\"query\":{\"condition\":\"AND\",\"rules\":[{\"value\":[\"'+start_time+'\",\"'+end_time+'\"],\"field\":\"entry_time\",\"type\":\"date\",\"operator\":\"between\"}]}}'


if __name__=='__main__':

    while True:

        """ open the yaml file where the constant data is stored"""

        with open("vmanage_login1.yaml") as f:
            config = yaml.safe_load(f.read())


        """ extracting info from Yaml file"""

        vmanage_host = config['vmanage_host']
        vmanage_port = config['vmanage_port']
        username = config['vmanage_username']
        password = config['vmanage_password']


        """ GET the TOKEN from Authnetication call"""
        header= auth.get_header(vmanage_host, vmanage_port,username, password)


        """ """

        deviceInfo_data = {}

        deviceInfo = getData.getDeviceIP(vmanage_host,vmanage_port,header)

        for iter_deviceInfo in deviceInfo:

            if iter_deviceInfo["device-type"] == "vedge":

                if iter_deviceInfo["site-id"] not in deviceInfo_data:
                    deviceInfo_data[iter_deviceInfo["site-id"]] = { "uuid":[],  "Aggregate" : 0,  "license Tier" : 'T0' }

                if iter_deviceInfo["uuid"] not in deviceInfo_data[iter_deviceInfo["site-id"]]["uuid"]:
                    deviceInfo_data[iter_deviceInfo["site-id"]]["uuid"].append(iter_deviceInfo["uuid"])
                    deviceInfo_data[iter_deviceInfo["site-id"]][iter_deviceInfo["system-ip"]] = {}




                #deviceInfo_data[iter_deviceInfo["site-id"]]["uuid"].append(iter_deviceInfo["uuid"])
                #deviceInfo_data[iter_deviceInfo["site-id"]][iter_deviceInfo["system-ip"]]



            if iter_deviceInfo["device-type"] == "vedge" and iter_deviceInfo["reachability"] == "reachable":



                wanIFName = getData.getWANIfName(vmanage_host,vmanage_port,header,iter_deviceInfo["system-ip"])

                print(f' Gathering the data from {iter_deviceInfo["uuid"]} - {iter_deviceInfo["system-ip"]} ')

                cumBW = 0

                for iter_wanIFName in wanIFName:

                    TransportIfName = re.split(r"\.", iter_wanIFName["interface"])[0]

                    data = queryPayload.statsIFAgg(iter_deviceInfo["system-ip"] , TransportIfName)

                    interfaceStats = postData.getInterfaceStats(vmanage_host,vmanage_port,header,data)

                    maxagg = max(interfaceStats, key=lambda x: x["tx_kbps"]+ x["rx_kbps"])

                    deviceInfo_data[iter_deviceInfo["site-id"]][iter_deviceInfo["system-ip"]][TransportIfName] = maxagg["tx_kbps"]+maxagg["rx_kbps"]

                    cumBW += (maxagg["tx_kbps"]+maxagg["rx_kbps"])


                deviceInfo_data[iter_deviceInfo["site-id"]]["Aggregate"] += cumBW



        for iter_deviceInfo_data in deviceInfo_data:

            AggMbps = deviceInfo_data[iter_deviceInfo_data]["Aggregate"]/1000
            #print(AggMbps)

            if AggMbps <= 50:
                deviceInfo_data[iter_deviceInfo_data]["license Tier"] = "T0"
            elif 50 < AggMbps <= 400:
                deviceInfo_data[iter_deviceInfo_data]["license Tier"] = "T1"
            elif 400 < AggMbps <= 2000:
                deviceInfo_data[iter_deviceInfo_data]["license Tier"] = "T2"
            elif 2000 < AggMbps <= 20000:
                deviceInfo_data[iter_deviceInfo_data]["license Tier"] = "T3"


        #print(deviceInfo_data)
        with open('lic1.csv','w') as f:
            w = csv.writer(f)
            w.writerows(deviceInfo_data.items())



        exit()
