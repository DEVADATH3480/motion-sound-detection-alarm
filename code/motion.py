

import threading
import winsound
import cv2
import imutils
import pyaudio
import numpy as np
import time

sound_detected = False
stop_alarm = threading.Event()
alarm_mode = False  # Initialize alarm mode status

def sound_alarm():
    global sound_detected
    while True:
        if sound_detected and alarm_mode:  # Check if alarm mode is active
            print("Sound detected! Press any key to stop the alarm.")
            while not stop_alarm.is_set():
                winsound.Beep(2500, 1000)  # Trigger a beep when sound is detected
            sound_detected = False
            stop_alarm.clear()

def detect_sound():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    global sound_detected
    while True:
        data = np.frombuffer(stream.read(CHUNK), dtype=np.int16)
        if np.abs(data).mean() > 150:  # Adjust this threshold according to your environment
            sound_detected = True

    stream.stop_stream()
    stream.close()
    p.terminate()

# Start the sound detection thread
sound_thread = threading.Thread(target=detect_sound)
sound_thread.daemon = True
sound_thread.start()

# Start the sound alarm thread
alarm_thread = threading.Thread(target=sound_alarm)
alarm_thread.daemon = True
alarm_thread.start()

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

_, start_frame = cap.read()
start_frame = imutils.resize(start_frame, width=500)
start_frame = cv2.cvtColor(start_frame, cv2.COLOR_BGR2GRAY)
start_frame = cv2.GaussianBlur(start_frame, (21, 21), 0)

alarm = False
alarm_mode = False
alarm_counter = 0

def beep_alarm():
    global alarm
    while alarm_mode:  # Run the alarm while alarm mode is active
        print("ALARM")
        winsound.Beep(2500, 1000)
        time.sleep(0)  # Sleep for 1 second between beeps
        if not alarm_mode:  # Check if alarm mode has been deactivated
            break
    alarm = False

while True:
    _, frame = cap.read()
    frame = imutils.resize(frame, width=500)
    
    if alarm_mode:
        frame_bw = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_bw = cv2.GaussianBlur(frame_bw, (5, 5), 0)
        
        difference = cv2.absdiff(frame_bw, start_frame)
        threshold = cv2.threshold(difference, 25, 255, cv2.THRESH_BINARY)[1]
        start_frame = frame_bw   
        
        if threshold.sum() > 1000000:
            print(threshold.sum())
            alarm_counter += 1
        else:
            if alarm_counter > 0:
                alarm_counter -= 1
                
        cv2.imshow("cam", threshold)
    else:
        cv2.imshow("cam", frame)
        
    if alarm_counter > 20:
        if not alarm:
            alarm = True
            threading.Thread(target=beep_alarm).start()
            
    key_pressed = cv2.waitKey(30)
    if key_pressed == ord("t"):
        alarm_mode = not alarm_mode
        alarm_counter = 0
        if not alarm_mode:  # Reset alarm flag when turning off alarm mode
            stop_alarm.set()  # Set the stop alarm event
            alarm = False
    if key_pressed == ord("s"):
        alarm_mode = False
        break

cap.release()
cv2.destroyAllWindows()
