import cv2
import socket
import multiprocessing as mp
import time
import pickle
import math
import struct

def f(jpgBin):
    
    
    framerate = 30
    stream = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    stream.connect(("127.0.0.1", 9999))
    print(stream.getsockname())
    fr_prev_time = 0
    i = 0
    while True:
        time.sleep(0.05)
        i += 1
        if i % 30 == 0:
            print(str(i/30), end="\r")

        car_id = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        car_idBin = car_id.encode("utf-8")
        
        jpgBin_size = len(jpgBin)
        nof = math.ceil(jpgBin_size / (9216 - 64))
        start_pos = 0

        stream.send(car_idBin)

        while nof:
            end_pos = min(jpgBin_size, start_pos + (9216 - 64))
            fg = struct.pack("B", nof) + jpgBin[start_pos:end_pos]
            stream.send(fg)
            start_pos = end_pos
            nof -= 1

    

if __name__=="__main__":
    print("how many processes? ", end="")
    pn = int(input())

    # VC = cv2.VideoCapture(0)
    # ret, cap = VC.read()
    # ret, jpgImg = cv2.imencode(".jpg", cap, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
    # jpgBin = pickle.dumps(jpgImg)
    # out_file = open('testjpgBin', 'wb')
    # out_file.write(jpgBin)
    # out_file.close()
    # VC.release()

    file = open('testjpgBin', 'rb')
    jpgBin = file.read()
    file.close()

    p = mp.Pool(processes=pn)
    args = [jpgBin] * pn
    p.map(f, args)
    p.close()
    p.join()
