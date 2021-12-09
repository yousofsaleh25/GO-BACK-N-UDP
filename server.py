import hashlib
import pickle
import socket
import time
import threading
import random

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
        elif event == "not_send":
            pass




PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.settimeout(None)
serverSocket.bind(ADDR)
file_type = '.csv'
file_name = "out2000" + file_type
file_object = open(file_name, 'wb')


def start():
    serverSocket.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = serverSocket.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTION] {threading.activeCount() - 1}")


def handle_client(conn, addr):
    ack_type = {"POS": 1, "NEG": 0}
    window_size = 7  # 0 --> 6
    expected_frame = 1
    starttime = time.time()
    last_file_rec = time.time()
    end_of_file = False
    while not end_of_file:
        rcvpkt = []
        packet = conn.recv(4096)
        rcvpkt = pickle.loads(packet)
        c = rcvpkt[-1]
        del rcvpkt[-1]
        h = hashlib.md5()
        h.update(pickle.dumps(rcvpkt))
        if c == h.digest():
            if rcvpkt[0] == expected_frame:
                if type(rcvpkt[-1]) is not int and rcvpkt[-1] == True:
                    print("END OF FILE")
                    break
                data = rcvpkt[1]
                file_object.write(data)
                print(f"RECIEVED packet_seq: {rcvpkt[0]}, data_len: {len(rcvpkt[1])}")
                ack = [expected_frame, ack_type["POS"]]
                h = hashlib.md5()
                h.update(pickle.dumps(ack))
                ack.append(h.digest())
                BadNet.transmit(conn, pickle.dumps(ack))
                print(f"SEND POS ACK for {rcvpkt[0]}")
                expected_frame = expected_frame + 1
            else:
                # default? discard packet and resend ACK for most recently received inorder pkt
                print("Received out of order ", rcvpkt[0])
                sndpkt = [expected_frame]
                sndpkt.append(ack_type["NEG"])
                h = hashlib.md5()
                h.update(pickle.dumps(sndpkt))
                sndpkt.append(h.digest())
                # time.sleep(0.001)
                BadNet.transmit(conn, pickle.dumps(sndpkt))
                print("SEND NEG Ack", expected_frame)
        else:
            print(f"Error Detected in {rcvpkt[0]}")
    endtime = time.time()
    file_object.close()
    print('FILE TRANFER SUCCESSFUL')
    conn.close()
    print("TIME TAKEN ", str(endtime - starttime))


start()