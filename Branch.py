import example_pb2
import example_pb2_grpc
import ast
from concurrent import futures
import os
import json
import grpc
import time
import multiprocessing
import shutil

class Branch(example_pb2_grpc.RPCServicer):

    def __init__(self, id, balance, branches):
        # unique ID of the Branch
        self.id = id
        # replica of the Branch's balance
        self.balance = balance
        # the list of process IDs of the branches
        self.branches = branches
        # other branches list
        self.others = self.branches
        self.others.pop((self.id-1))
        #clock start with assumption of clock time from customer as 1
        self.clock = 1
        self.events = list()
        self.pid = list()
        self.prop = list()
        self.repl = list()
        #self.bcast = list()
        self.all = list()
        self.folder = "Branch" + str(self.id)
        os.mkdir(self.folder)
        self.branchfilename = str(self.folder) + "/Branch" + str(self.id) + "A.txt"
        self.branchfilenameP = str(self.folder) + "/Branch" + str(self.id) + "B.txt"
        self.branchfilenameR = str(self.folder) + "/Branch" + str(self.id) + "C.txt"
        
        


        #print("self.branchfilename is : ", self.branchfilename)
        #print("Branch %s server up" % str(self.id))


        # TODO: students are expected to store the processID of the branches
        pass

    # event request
    def eventRequestExecute (self, x):
        self.events.append(ast.literal_eval(x))
        if self.events[0]["interface"] == 'deposit':
            self.pid.append({"id":self.events[0]['id'], "name":"deposit_request", "clock":2})
            self.pid.append({"id":self.events[0]['id'], "name":"deposit_execute", "clock":3})
            self.clock = 3
            with open(self.branchfilename, "a") as g:
                g.write(str(self.pid))    
        elif self.events[0]["interface"] == 'withdraw':
            self.pid.append({"id":self.events[0]['id'], "name":"withdraw_request", "clock":2})
            self.pid.append({"id":self.events[0]['id'], "name":"withdraw_execute", "clock":3})
            self.clock = 3
            with open(self.branchfilename, "w") as g:
                g.write(str(self.pid))
        else:
            pass



    #recieve clock
    def ClockUpdate(self, request, context):
        #print("ClockUpdate")
        #time.sleep(0.5)
        #lock.acquire()
        rcast = ast.literal_eval(request.propout)
        pid = rcast["id"]
        if rcast["name"] == "deposit_propogate_request":
            rcasttime = max(self.clock, rcast["clock"]) + 1
            self.prop.append({'id': pid, 'name': 'deposit_propogate_request', 'clock': rcasttime})
            #print("first prop and id : ", self.prop, self.id)
            clock2 = rcasttime + 1
            self.prop.append({'id': pid, 'name': 'deposit_propogate_execute', 'clock': clock2})
            clock3 = clock2 + 1
            #print("2nd prop : ", self.prop, self.id)
            pushout = {'id': pid, 'name': 'deposit_propogate_response', 'clock': clock3}
            self.clock = clock3
        else:
            rcasttime = max(self.clock, rcast["clock"]) + 1
            self.prop.append({'id': pid, 'name': 'withdraw_propogate_request', 'clock': rcasttime})
            #print("first prop and id : ", self.prop, self.id)
            clock2 = rcasttime + 1
            self.prop.append({'id': pid, 'name': 'withdraw_propogate_execute', 'clock': clock2})
            clock3 = clock2 + 1
            #print("2nd prop : ", self.prop, self.id)
            pushout = {'id': pid, 'name': 'withdraw_propogate_response', 'clock': clock3}
            self.clock = clock3
        with open(self.branchfilenameP, "w") as g:
            g.write(str(self.prop))
        #lock.release()
        #print("r cast sent back is ", pushout, self.id)
        return example_pb2.ExamplePropIn(propin=str(pushout))
    
    
    def propagateRequest(self):
        #print("propagateRequest")
        #propagate 
        lock.acquire()
        if self.events[0]["interface"] == 'deposit':
            for x in self.others:
                sendit = str({"id":self.events[0]['id'], "name":"deposit_propogate_request", "clock":self.clock})
                trans_spec = 50047 + x
                clockit = sendit
                # print("clockit-sendit is ", clockit, x)
                with grpc.insecure_channel('localhost:' + str(trans_spec)) as channel:
                    stub = example_pb2_grpc.RPCStub(channel)
                    response = stub.ClockUpdate(example_pb2.ExamplePropOut(propout=clockit))
                    r2cast = ast.literal_eval(response.propin)
                    if r2cast["name"] == "deposit_propogate_response":
                        maxit = max(self.clock, r2cast["clock"]) + 1
                        r2cast["clock"] = maxit
                        self.clock = maxit
                        self.repl.append(r2cast)    
        elif self.events[0]["interface"] == 'withdraw':
            for x in self.others:
                sendit = str({"id":self.events[0]['id'], "name":"withdraw_propogate_request", "clock":self.clock})
                trans_spec = 50047 + x
                clockit = sendit
                # print("clockit-sendit is ", clockit, x)
                with grpc.insecure_channel('localhost:' + str(trans_spec)) as channel:
                    stub = example_pb2_grpc.RPCStub(channel)
                    response = stub.ClockUpdate(example_pb2.ExamplePropOut(propout=clockit))
                    r2cast = ast.literal_eval(response.propin)
                    if r2cast["name"] == "withdraw_propogate_response":
                        maxit = max(self.clock, r2cast["clock"]) + 1
                        r2cast["clock"] = maxit
                        self.clock = maxit
                        self.repl.append(r2cast) 
        else:
            pass
        self.clock += 1
        if self.events[0]["interface"] == 'deposit':
            self.repl.append({"id":self.events[0]['id'], "name":"deposit_response", "clock":self.clock})       
        elif self.events[0]["interface"] == 'withdraw':
            self.repl.append({"id":self.events[0]['id'], "name":"withdraw_response", "clock":self.clock})
        else:
            pass
        with open(self.branchfilenameR, "w") as g:
                g.write(str(self.repl))
        lock.release()         
        

    # TODO: students are expected to process requests from both Client and Branch
    def MsgDelivery(self,request, context):
        #print("MsgDelivery")
        response = example_pb2.ExampleReply()
        responseIn = example_pb2.ExamplePropIn()
        self.eventRequestExecute(request.inmessage)
        if self.events[0]["interface"] != 'query':
            self.propagateRequest()
        self.pid.append(responseIn.propin)
        #print("self.pid after ClockUpdate is ", self.pid, self.id)
        #self.pid.append(self.id)
        response.outmessage  = "Done"
        return response


def creatServer(id, balance, branches):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    example_pb2_grpc.add_RPCServicer_to_server(Branch(id, balance, branches), server)
    trans_spec = 50047 + int(id)
    server.add_insecure_port('[::]:'+ str(trans_spec))
    server.start()
    server.wait_for_termination()



if __name__ == "__main__":
    lock = multiprocessing.Lock()
    #delete output file if in folder
    if os.path.exists("output.json"):
        os.remove("output.json")
    with open("input.json") as example_file:
        example_data = json.load(example_file)
        processes = []
        branches = []
        for i in range(len(example_data)):
            if example_data[i]['type'] == 'branch':
                branches.append(int(example_data[i]['id']))
                #remove old folders
                pathTofolder = "Branch"+ str(example_data[i]['id'])
                shutil.rmtree(pathTofolder, ignore_errors=True)
        for i in range(len(example_data)):
            if example_data[i]['type'] == 'branch':
                p1 = multiprocessing.Process(target=creatServer, args=(int(example_data[i]['id']), int(example_data[i]['balance']), branches))
                processes.append(p1)
                p1.start()
        for p1 in processes:
            p1.join()






