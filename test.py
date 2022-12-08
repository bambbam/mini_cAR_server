import cv2

if __name__ == '__main__':
    cap = cv2.VideoCapture(0)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(
        "./tmp/test.mp4", fourcc, 30, (1280,720)
    )
    
    for i in range(100):
        frame, ret = cap.read()
        out.write(ret)
    out.release()
        