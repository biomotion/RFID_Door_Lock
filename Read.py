#!/usr/bin/env python

import RPi.GPIO as GPIO
import MFRC522
import signal
import time
import MySQLdb

continue_reading = True
# Capture SIGINT for cleanup when the script is aborted
def end_read(signal,frame):
    global continue_reading
    print "Ctrl+C captured, ending read."
    continue_reading = False
    GPIO.cleanup()

def door_open():
    GPIO.output(29, GPIO.HIGH)
    GPIO.output(31, GPIO.LOW)
    print("Door opened")

def door_close():
    GPIO.output(29, GPIO.LOW)
    GPIO.output(31, GPIO.LOW)
    # GPIO.output(29, GPIO.HIGH)
    print("Door closed")


#setup GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(29, GPIO.OUT)
GPIO.setup(31, GPIO.OUT)
#initialize
GPIO.output(29, GPIO.LOW)
GPIO.output(31, GPIO.LOW)

# Hook the SIGINT
signal.signal(signal.SIGINT, end_read)
# Create an object of the class MFRC522
MIFAREReader = MFRC522.MFRC522()

# Welcome message
print "Welcome to the MFRC522 data read example"
print "Press Ctrl-C to stop."
# This loop keeps checking for chips. If one is near it will get the UID and authenticate
while continue_reading:
    # Scan for cards    
    (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
    # If a card is found
    if status == MIFAREReader.MI_OK:
        print "Card detected"
        # Get the UID of the card
        (status,uid) = MIFAREReader.MFRC522_Anticoll()
        MIFAREReader.AntennaOff()
        # If we have the UID, continue
        if status == MIFAREReader.MI_OK:
            # Print UID
            print "Card read UID: %s,%s,%s,%s" % (uid[0], uid[1], uid[2], uid[3])
            uid_int = 0
            for i in range(4):
                uid_int *= 256
                uid_int += uid[i]
            print(uid_int)
            command = "select * from allowed_uid where uid=%d" %(uid_int)
            try:
                conn = MySQLdb.connect(db="eLock", user="pi", passwd="nctuece")
                try:
                    cur = conn.cursor()
                    cur.execute(command)
                    conn.commit()
                    result = cur.fetchall()
                    if(len(result) != 0):
                        #open the door
                        cur.execute("insert into record(uid, allowed) values(%d, true)" % uid_int)
                        conn.commit()
                        door_open()
                        time.sleep(3)
                        door_close()
                    else:
                        print("wrong uid")
                        cur.execute("insert into record(uid, allowed) values(%d, false)" % uid_int)
                        conn.commit()
                        time.sleep(3)
                except MySQLdb.OperationalError:
                        print "cursor error"
                else:
                        cur.close()
            except MySQLdb.OperationalError:
                    print "connection error"
            else:
                    conn.close()
        MIFAREReader.AntennaOn()

