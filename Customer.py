import grpc
import example_pb2
import example_pb2_grpc
import ast
import json
import os, signal
from concurrent import futures
import subprocess
import re
from itertools import chain
from operator import itemgetter
import shutil

class Customer:
    def __init__(self, id, events):
        # unique ID of the Customer
        self.id = id
        # events from the input
        self.events = events

    # TODO: students are expected to create the Customer stub
    def createStub(self):
        trans_spec = 50047 + self.id
        channel = grpc.insecure_channel('localhost:' + str(trans_spec))
        # create a stub (client)
        self.stub = example_pb2_grpc.RPCStub(channel)
    
    # TODO: students are expected to send out the events to the Bank
    def executeEvents(self):
        # create a valid request message
        validrequest = str(self.events)
        string = example_pb2.ExampleRequest(inmessage=validrequest)
        # make the call
        response = self.stub.MsgDelivery(string)
        return response.outmessage

        
if __name__ == "__main__":
    with open("input.json") as example_file:
        example_data = json.load(example_file)
        id_list = []
        message_list = []              
        for i in range(len(example_data)):
            if example_data[i]['type'] == 'customer':
                id_list.append(example_data[i]['id'])
                pathTofolder = "Branch"+ str(example_data[i]['id'])
                message_list.append(pathTofolder)
                customerrun = Customer(int(example_data[i]['id']), example_data[i]['events'][0])
                customerrun.createStub()
                customerrun.executeEvents()
        # Creating of output file
        outcontent = []
        counter = 1
        for x in  message_list:
            datanam = []
            if len(os.listdir(x)) == 1:
                fileB = x + "/" + os.listdir(x)[0]
                with open(fileB) as f:
                    datanam.append(ast.literal_eval((f.read())))
            else:
                listit = os.listdir(x)
                for i in listit:
                    q = re.search('A.txt$', i)
                    if q != None:
                        with open(x + "/" + i) as f:
                            datanam.append(ast.literal_eval((f.read())))
                for i in listit:
                    q = re.search('B.txt$', i)
                    if q != None:
                        with open(x + "/" + i) as f:
                            datanam.append(ast.literal_eval((f.read())))
                for i in listit:
                    q = re.search('C.txt$', i)
                    if q != None:
                        with open(x + "/" + i) as f:
                            datanam.append(ast.literal_eval((f.read())))
            dataapp = list(chain(*datanam))
            #print(dataapp)
            counter += 1
            outcontent.append(dataapp)
        #print(outcontent)
        depositevent = []
        withdrawevent = []
        for x in outcontent:
            for i in x:
                b = i["name"]
                if b.startswith("deposit"):
                    depositevent.append({"clock": i["clock"], "name": i["name"]})
                    depositID = i["id"]
                else:
                    withdrawevent.append({"clock": i["clock"], "name": i["name"]})
                    withdrawID = i["id"]
        clockname =itemgetter("clock")
        depositevent.sort(key=clockname)
        withdrawevent.sort(key=clockname)
        finallist = []
        counter = 1
        for x in outcontent:
            x.sort(key=clockname)
            finallist.append({"pid":counter, "data": x})
            counter += 1
        finallist.append({"eventid": withdrawID, "data": withdrawevent})
        finallist.append({"eventid": depositID, "data": depositevent})
        with open('output.json', 'w', encoding='utf-8') as json_file:
            json.dump(finallist, json_file, ensure_ascii=False, indent=1)
        for z in message_list:
            shutil.rmtree(z, ignore_errors=True)
        # Closing of approriate server after writing to output file. 
        for i in id_list:
            pidX1 = 50047 + i
            pidX2 = str(pidX1)+'/tcp'
            pidX3 = subprocess.run(['fuser', '-k', pidX2], capture_output=True)