import threading
import queue
from datetime import datetime, timedelta

# Class for processes, who can act as an coordinator or as a participant
class Process(threading.Thread):

    # Thread initialisation
    def __init__(self, processID, previousHistory, isCoordinator, lock):
        threading.Thread.__init__(self)

        # Parameter initialisation
        self.id = processID
        self.history = previousHistory.copy()
        self.setCoordinator(isCoordinator)
        self.lock = lock

        # Variable initialisation
        self.running = True
        self.failure = False
        self.state = "Init"
        self.addOrRollback = "Add"
        self.answers = 0
        self.lastValue = 0
        self.noAbort = True
        self.queue = queue.Queue()
        self.addingFinished = False
        self.timeToBeFailed = datetime.now()

        # Starting the thread
        self.start()

    # Sets the running variable used to check if we have to exit the thread or not
    def setRunning(self, bool):
        self.running = bool

    # Adds a new message to thread queue
    # Message format: ["Command", "Subcommand", "Value", "From"]
    def addMessageToQueue(self, message):
        self.queue.put(message)

    # Sets the thread as a coordinator if necessary
    def setCoordinator(self, bool):
        self.isCoordinator = bool
        if bool:
            self.name = self.name + " (Coordinator)"

    # Getter to get if the adding or rollback has finished
    def getAddingFinished(self):
        return self.addingFinished

    # Sets the adding finished boolean
    def setAddingFinished(self, bool):
        self.addingFinished = bool

    # Sets the time when thread is unavailable and will not respond to any request or commands
    def timeFailure(self, seconds):
        self.timeToBeFailed = datetime.now() + timedelta(0, seconds)
        self.printStatement(self.name + " Time failure for " + str(seconds) + " seconds")

    # Prints out the consistency history of the process
    def printHistory(self):
        if self.isCoordinator:
            self.printStatement(self.id + "-history: " + str(self.history) + " (Coordinator)")
        else:
            self.printStatement(self.id + "-history: " + str(self.history))

    # Function which uses lock to print thread safe
    def printStatement(self, string):
        self.lock.acquire()
        try:
            print(string)
        finally:
            self.lock.release()

    # Thread main function
    def run(self):
        while self.running:
            if datetime.now() > self.timeToBeFailed:  # Check if the process can respond to requests or commands
                if not self.queue.empty():  # If there is a message in queue start processing it
                    message = self.queue.get()  # Get message
                    command = message[0]  # Get command ("Add", "Rollback", "VoteRequest", "VoteCommit", "VoteAbort",
                    # "GlobalCommit", "GlobalAbort", "ACK")
                    subCommand = message[1]  # Get subcommand ("Add", "Rollback")
                    value = message[2]  # Value to add or rollback positions
                    messageFrom = message[3]  # Who's the parent of this message

                    # Start the commit procedure
                    if command == "Add":
                        self.printStatement(self.name + " Received Add")
                        # Initiate variables
                        self.answers = 0
                        self.lastValue = value
                        self.noAbort = True
                        self.addingFinished = False
                        self.addOrRollback = subCommand
                        for thread in threading.enumerate():  # Send message to other threads
                            name = thread.name
                            if ("MainThread" in name) or (self.name in name):  # Only do not send to yourself and to MainThread
                                continue
                            self.printStatement(self.name + " Send voteRequest to " + name)
                            thread.addMessageToQueue(["VoteRequest", "", "", self.name])  # Send VoteRequest to participants
                            self.state = "Wait"  # Change coordinator state to wait

                    # Start the rollback commit procedure
                    elif command == "Rollback":
                        self.printStatement(self.name + " Received Rollback")
                        self.answers = 0
                        self.lastValue = value
                        self.noAbort = True
                        self.addingFinished = False
                        self.addOrRollback = subCommand
                        for thread in threading.enumerate():
                            name = thread.name
                            if ("MainThread" in name) or (self.name in name):
                                continue
                            self.printStatement(self.name + " Send voteRequest to " + name)
                            thread.addMessageToQueue(["VoteRequest", "", "", self.name]) # Send VoteRequest to participants
                            self.state = "Wait"

                    # Participant process receives the vote request and replies to coordinator with VoteCommit or VoteAbort
                    elif command == "VoteRequest":
                        self.printStatement(self.name + " Received voteRequest")
                        if not self.failure and self.state == "Init":  # If process hasn't got error and has state init
                            # then send VoteCommit
                            for thread in threading.enumerate():
                                name = thread.name
                                if messageFrom in name:  # Respond to message parent
                                    self.printStatement(self.name + " Send voteCommit to " + name)
                                    thread.addMessageToQueue(["VoteCommit", "", "", self.name]) # Send VoteCommit to coordinator
                                    self.state = "Ready"  # Change participant state to Ready
                        else:
                            for thread in threading.enumerate():
                                name = thread.name
                                if messageFrom in name:
                                    self.printStatement(self.name + " Send voteAbort to " + name)
                                    thread.addMessageToQueue(["VoteAbort", "", "", self.name]) # Send VoteAbort to coordinator
                                    self.state = "Abort"  # Change participant state to Abort

                    # Coordinator receives VoteCommits from participants
                    elif command == "VoteCommit":
                        self.printStatement(self.name + " Received voteCommit")
                        if self.noAbort:  # If no VoteAbort has yet arrived
                            self.answers += 1  # New VoteCommit has arrived
                            if self.answers == (len(threading.enumerate()) - 2):  # If all the participants have responded with VoteCommit
                                self.answers = 0
                                if self.addOrRollback == "Add":  # If we had adding procedure
                                    self.history.append(int(self.lastValue))  # Add new value
                                else:  # If we had rollback procedure
                                    self.history = self.history[:-int(self.lastValue)]  # Rollback history
                                for thread in threading.enumerate():
                                    name = thread.name
                                    if ("MainThread" in name) or (self.name in name):
                                        continue
                                    self.printStatement(self.name + " Send globalCommit to " + name)

                                    # Send GlobalCommit to all participants
                                    if self.addOrRollback == "Add":
                                        thread.addMessageToQueue(["GlobalCommit", "Add", self.lastValue, self.name])
                                    else:
                                        thread.addMessageToQueue(["GlobalCommit", "Rollback", self.lastValue, self.name])

                                    self.state = "Commit"  # Change coordinator state to commit

                    # Coordinator receives VoteAbort from participants
                    elif command == "VoteAbort":
                        self.printStatement(self.name + " Received voteAbort")
                        self.noAbort = False  # Abort has arrived and no more we listen for VoteCommit
                        self.answers = 0
                        for thread in threading.enumerate():
                            name = thread.name
                            if ("MainThread" in name) or (self.name in name):
                                continue
                            self.printStatement(self.name + " Send globalAbort to " + name)
                            thread.addMessageToQueue(["GlobalAbort", "", "", self.name])  # Send GlobalAbort to all participants
                            self.state = "Abort"  # Change coordinator state to abort

                    # Participants receive GlobalCommit from coordinator process
                    elif command == "GlobalCommit":
                        self.printStatement(self.name + " Received globalCommit")

                        # Add or rollback based on subcommand
                        if subCommand == "Add":
                            self.history.append(int(value))
                        else:
                            self.history = self.history[:-int(value)]

                        for thread in threading.enumerate():
                            name = thread.name
                            if messageFrom in name:
                                self.printStatement(self.name + " Send ACK to " + name)
                                thread.addMessageToQueue(["ACK", "", "", self.name])  # Send ACK to coordinator
                                self.state = "Init"  # Change participant state to init

                    # Participants receive GlobalAbort from coordinator process
                    elif command == "GlobalAbort":
                        self.printStatement(self.name + " Received globalAbort")
                        for thread in threading.enumerate():
                            name = thread.name
                            if messageFrom in name:
                                self.printStatement(self.name + " Send ACK to " + name)  # Send ACK to coordinator
                                thread.addMessageToQueue(["ACK", "", "", self.name])
                                self.state = "Init"  # Change participant state to init

                    # Coordinator receives ACK from participants
                    elif command == "ACK":
                        self.printStatement(self.name + " Received ACK")
                        self.answers += 1
                        if self.answers == (len(threading.enumerate()) - 2):  # If all the ACK have been received
                            self.state = "Init"  # Change coordinator state to init
                            self.addingFinished = True  # Adding or rollback procedure has ended
