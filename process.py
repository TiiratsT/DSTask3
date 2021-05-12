from threading import Thread
import time

class Process(Thread):

    def __init__(self, processID):
        Thread.__init__(self)
        self.running = True

        self.start()

    def setRunning(self, bool):
        self.running = bool

    def run(self):
        while self.running:
            pass

        print("Process starting exiting!")