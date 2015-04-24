#!/usr/bin/python

'''
Created on Mar 16, 2015

@author: selly
'''

import RPIO as GPIO #@UnresolvedImport 
from RPIO import PWM #@UnresolvedImport
import time
import threading
import BB8Server

class BB8Controller(object):
    '''
    classdocs
    '''

    
    def __init__(self):
        '''
        Constructor
        '''
        
        #Speed changing parameters -100 - +100 for speed, 0-2000 Us for Servo
        self.maxSpeedShift = 2
        self.maxServoShiftUs = 40
        
        # Servo hardware configuration 
        self.servoPin = 24
        # 20 ms in units of us -- this is the default
        self.servoRange = 80
        # 80% of the total servo range is addressable.
        self.servoDMAChannel = 0

        # Speed changing hardware configuration
        self.speedDMAChannel = 0
        self.pulseWidthUs = 10
        # With a PWM Width of 10 us and a cycle of 1 ms, there are exactly 100 increments in the duty pulse cycle.
        
        # With a frequency of 1000, the entire PWM cycle will be 1 ms, with 100, cycle = 10 ms
        self.speedPWMFrequency = 50
        
        self.speedPWMCycleTime = (1000000) /self.speedPWMFrequency
        self.servoCycle = self.speedPWMCycleTime
        # Cycle time is in units of us (hence the multiplication by 1,000,000)
        
        self.loopFrequency = 50
        # The frequency of the control loop for smoothing position/speed
        
        self.leftSpeed = 0
        # Range is -100 - +100
        self.rightSpeed = 0
        # Range is -100 - +100
        
        #Target speeds--where we're trying to go
        self.leftTargetSpeed = 0
        self.rightTargetSpeed = 0
        
        self.shutdown = False
        self.motorRightPinA = 11
        self.motorRightPinB = 9
        self.motorRightSpeedPin = 10

        self.motorLeftPinA = 7
        self.motorLeftPinB = 8
        self.motorLeftSpeedPin = 25
        
        # The actual Us
        self.servoUs = 1500
        # The target Us -- we use a smoothing algorithm to bring the actual Us to the Target Us over a curve.
        self.servoTargetUs = 1500

    def getUsForServoPosition(self, position):
        '''
        Logic to translate a position in the range of -100 to +100 to the correct PWM settings
        -100 should create a pulse width = 0.5ms, 0 should be 1.5ms and +100 should be 2.5ms
        Us = Ms * 1000
        '''
        targetUs = 1500 + (round(position) * 10);
        print "position {} = targetUs {}".format(position, targetUs)
        return targetUs;

    '''
    ServoPosition is 
    '''
    def setServoPosition(self, position):
        #Adjust for the total addressable range 
        targetUs = round(self.getUsForServoPosition(position * self.servoRange / 100))
        print "Setting ServoUs: {} TargetUs: {}".format(self.servoUs, targetUs)
        if (abs(targetUs - self.servoUs) >= 10):
            self.servoTargetUs = targetUs
        
    def controlProgram(self):
        '''
        The logic which should be run in a separate thread to turn the wheels
        '''
        while 1:
            if (self.shutdown):
                self.leftThread.stop();
                self.rightThread.stop();
                return

            try:
                servoDiff = self.servoTargetUs - self.servoUs;
                if (servoDiff != 0):
                    if abs(servoDiff) > self.maxServoShiftUs:
                        # We have a big shift in position--move the max.
                        self.servoUs = self.servoUs + self.maxServoShiftUs * (servoDiff / abs(servoDiff))
                    else:
                        self.servoUs = self.servoTargetUs
                    self.servo.set_servo(self.servoPin, self.servoUs)

                leftDiff = self.leftTargetSpeed - self.leftSpeed
                rightDiff = self.rightTargetSpeed - self.rightSpeed
                if (leftDiff != 0):
                    if (abs(leftDiff) > self.maxSpeedShift):
                        self.leftSpeed = self.leftSpeed + self.maxSpeedShift * (leftDiff / abs(leftDiff))
                    else:
                        self.leftSpeed = self.leftTargetSpeed

                    self.changeDutyCycle(self.motorLeftSpeedPin, abs(self.leftSpeed))
                    if (self.leftSpeed >= 0):
                        GPIO.output(self.motorLeftPinA, True)
                        GPIO.output(self.motorLeftPinB, False)
                    else:
                        GPIO.output(self.motorLeftPinA, False)
                        GPIO.output(self.motorLeftPinB, True)
                
                if (rightDiff != 0):
                    if (abs(rightDiff) > self.maxSpeedShift):
                        self.rightSpeed = self.rightSpeed + self.maxSpeedShift * (rightDiff / abs(rightDiff))
                    else:
                        self.rightSpeed = self.rightTargetSpeed

                    self.changeDutyCycle(self.motorRightSpeedPin, abs(self.rightSpeed))
                    if (self.rightSpeed >= 0):
                        GPIO.output(self.motorRightPinA, True)
                        GPIO.output(self.motorRightPinB, False)
                    else:
                        GPIO.output(self.motorRightPinA, False)
                        GPIO.output(self.motorRightPinB, True)
                    
                time.sleep(1.0/self.loopFrequency)
        
            except KeyboardInterrupt:
                break
    
    def changeDutyCycle(self, pin, speedIn):
        speed = round(speedIn)
        if (speed == 100):
            speed = 99
        print "changing duty cycle"
        PWM.clear_channel_gpio(channel=self.speedDMAChannel, gpio=pin)
        width = int(round((1.0 * self.speedPWMCycleTime) /self.pulseWidthUs * (speed / 100.0)))
        # speed/ 100.0 = the percent of total speed
        # speedPWMCycleTime / pulseWidthUs = the number of pwm subcycles in 1 cycle of PWM  (the number of subcycles of RPIO.PWM) 
        # width is therefore in units of the number of subcycles.
        print "setting duty cycle for pin {} to {} = speed {}".format(pin, width, speed)
        PWM.add_channel_pulse(dma_channel=self.speedDMAChannel, gpio=pin, start=0, width=width)
        #if (speedIn > 30):
        #    GPIO.output(pin, True)
        #else:
        #    GPIO.output(pin, False)

    def initMotors(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.motorLeftPinA, GPIO.OUT)
        GPIO.setup(self.motorLeftPinB, GPIO.OUT)
        GPIO.setup(self.motorLeftSpeedPin, GPIO.OUT)
        GPIO.setup(self.motorRightPinA, GPIO.OUT)
        GPIO.setup(self.motorRightPinB, GPIO.OUT)
        GPIO.setup(self.motorRightSpeedPin, GPIO.OUT)
        GPIO.output(self.motorLeftPinA, True)
        GPIO.output(self.motorLeftPinB, False)
        GPIO.output(self.motorRightPinA, True)
        GPIO.output(self.motorRightPinB, False)

        GPIO.setup(self.servoPin, GPIO.OUT)
        PWM.setup(pulse_incr_us = self.pulseWidthUs)
        
        # Initialize servo
        self.servo = PWM.Servo(dma_channel = self.servoDMAChannel, subcycle_time_us = self.servoCycle)
        self.setServoPosition(0)
        #PWM.init_channel(channel = self.servoDMAChannel, subcycle_time_us = self.servoCycle)
        
        # Initialize motor speed control
        PWM.init_channel(channel = self.speedDMAChannel, subcycle_time_us = self.speedPWMCycleTime)
        
        # Add a pulse then pull it off just to initiate.
        PWM.add_channel_pulse(self.speedDMAChannel, self.motorLeftSpeedPin, start=0, width=1)
        PWM.clear_channel_gpio(self.speedDMAChannel, self.motorLeftSpeedPin)
        PWM.add_channel_pulse(self.speedDMAChannel, self.motorRightSpeedPin, start=0, width=1)
        PWM.clear_channel_gpio(self.speedDMAChannel, self.motorRightSpeedPin)
        
    def setSpeed(self, motor, speed):
        if ("left" == motor):
            self.leftTargetSpeed = speed
        
        if ("right" == motor):
            self.rightTargetSpeed = speed
                
        print "setting {} to {}, and current {}, {}".format(motor, speed, self.leftSpeed, self.rightSpeed)
        return
        
    def startServer(self):
        t = threading.Thread(target=self.controlProgram)
        t.daemon = True
        t.start()
        server = BB8Server.BB8ServerContainer()
        server.startServer(self)

bb8 = BB8Controller();
t = threading.Thread(target=bb8.controlProgram)
t.daemon = True
bb8.initMotors();
bb8.startServer();
t.start()

