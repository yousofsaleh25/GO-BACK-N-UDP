import socket
import time
import random
import pickle
import hashlib

class BadNet:
    counter = 0
    event_type = ["not_send", "send"]

    @staticmethod
    def transmit(conn, pkt, end_of_file = False):
        # print 'Got a packet' + str(BadNet.counter)
        event = random.choices(BadNet.event_type,  weights=[0.1, 0.9])[0]
        BadNet.counter = BadNet.counter + 1
        #print(event, "   ", BadNet.counter)
        if event == "send":
            conn.send(pkt)
            rcvpkt = pickle.loads(pkt)
            print(f"SEND Packet num: {rcvpkt[0]}")
        elif event == "not_send":
            rcvpkt = pickle.loads(pkt)
            print(f"DROPPED Packet num: {rcvpkt[0]}")






#import pandas as pd

# import threading
filename = input("Enter a file path (protocol frame size in range of 1KB): ")
#filename = r'C:\Users\Dell\Desktop\CDSP\project\dastasets\corona.csv'
# filename = r'G:\movies\Inception.mp4'
# corona = pd.read_csv(filename)


file_object = open(filename, "rb")

PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
timeout = 0.001
clientSocket.settimeout(0.01)
clientSocket.connect(ADDR)

next_seq = 1
last_recieved_packet = time.time()
end_of_file = False
window = []
window_size = 7
base = 1
ack_type = {"POS": 1, "NEG": 0}

while not end_of_file or window:
    # pkt --> (seq_num, data, checksum)
    if (next_seq < base + window_size) and not end_of_file:
        data = file_object.read(500)
        sndpkt = [next_seq, data]
        h = hashlib.md5()
        h.update(pickle.dumps(sndpkt))
        sndpkt.append(h.digest())
        # time.sleep(0.0001)
        # clientSocket.send(pickle.dumps(sndpkt))
        BadNet.transmit(clientSocket, pickle.dumps(sndpkt))
        # threading.Timer(0.01, BadNet.transmit, args=(clientSocket, pickle.dumps(sndpkt))).start()
        next_seq = next_seq + 1
        window.append(sndpkt)
        if len(data) < 500:
            end_of_file = True
            sndpkt = [next_seq, data, end_of_file]
            h = hashlib.md5()
            h.update(pickle.dumps(sndpkt))
            sndpkt.append(h.digest())
            # time.sleep(0.01)
            # clientSocket.send(pickle.dumps(sndpkt))
            # time.sleep(0.0001)
            BadNet.transmit(clientSocket, pickle.dumps(sndpkt), end_of_file)
            # threading.Timer(0.01, BadNet.transmit, args=(clientSocket, pickle.dumps(sndpkt))).start()
            window.append(sndpkt)

    # receive ack
    try:
        rcvpkt = []
        packet = clientSocket.recv(4096)
        try:
            rcvpkt = pickle.loads(packet)
        except:
            break
        c = rcvpkt[-1]
        del rcvpkt[-1]
        h = hashlib.md5()
        h.update(pickle.dumps(rcvpkt))
        if c == h.digest():
            # positive acknolegement
            if rcvpkt[-1] == ack_type["POS"]:
                print(f"Received POS ack for {rcvpkt[0]}")
                while rcvpkt[0] >= (base) and window:
                    last_recieved_packet = time.time()
                    # window_print(window)
                    # print("base", base)
                    del window[0]
                    base = base + 1
            else:
                print(f"Received NEG ack for {rcvpkt[0]}")
                # window_print(window)
                # neg ack.
                for i in window:
                    if i[0] < rcvpkt[0]:
                        # del window[0]
                        # base = base + 1
                        continue
                    BadNet.transmit(clientSocket, pickle.dumps(i))
        #                     if i == window[-1]:
        #                         clientSocket.recv()
        else:
            print("Error Detected")
    # TIMEOUT
    except:
        if (time.time() - last_recieved_packet > 0.1):
            for i in window:
                BadNet.transmit(clientSocket, pickle.dumps(i))