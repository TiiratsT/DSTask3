import sys
import logging
import process
import random
import time
from multiprocessing import Lock

# Global variables
processes = []
coordinator = ""
historyType = ""
states = []

# Used to print out all processes consistency histories
def printProcessHistory(pool):
    print("")
    for node in pool:
        pool[node].printHistory()

# Main function
def main(argv):
    global processes, states, coordinator, historyType

    # Input file parsing
    f = open(argv[0], "r")
    nextLine = ""
    for line in f:
        if "System" in line:  # Finding all the initial processes
            while True:
                nextLine = f.readline()
                if "State" in nextLine:
                    break
                else:
                    if "Coordinator" in nextLine:
                        strings = nextLine.split(";")
                        coordinator = strings[0]
                        processes.append(coordinator)
                    else:
                        processes.append(nextLine[:-1])

        if "State" in nextLine:  # Saving consistency history
            nextLine = f.readline()
            strings = nextLine.split(";")
            historyType = strings[0]
            for number in strings[1].split(","):
                states.append(int(number))
    f.close()

    # Printing out the system initial state
    print("\nOriginal info from file:")
    print("Processes: " + str(processes))
    print("Coordinator: " + coordinator)
    print(historyType + ": " + str(states))

    # Create threads and lock for printing
    processPool = {}
    lock = Lock()

    for node in processes:
        processPool[node] = process.Process(node, states, node is coordinator, lock)

    # Print out the original history
    printProcessHistory(processPool)

    # Create command line interface and listen it until keyboard error occurs
    try:
        while True:
            text = input("Choose next command (Set-value, Rollback, Add, Remove, Time-failure, Arbitrary-failure)\n")

            # Set-value is used to commit a new value to system
            if "Set-value" in text:
                splitText = text.split()
                value = splitText[1]

                # Start adding the value to system by sending it to coordinator process
                processPool[coordinator].addMessageToQueue(["Add", "Add", str(value), "MainThread"])
                processPool[coordinator].setAddingFinished(False)

                # Wait until the adding is finished and then print the consistency history and wait for new command
                while not processPool[coordinator].getAddingFinished():
                    time.sleep(0.1)

                printProcessHistory(processPool)

            # Rollback is used to restore some previous state the system has been in
            elif "Rollback" in text:
                splitText = text.split()
                positions = int(splitText[1])

                # Check if the rollback is possible
                if positions > len(processPool[coordinator].history) - 1:
                    logging.warning("The system cannot reverse to that long state\n")
                else:

                    # Start rollback procedure by sending it to coordinator process
                    processPool[coordinator].addMessageToQueue(["Rollback", "Rollback", str(positions), "MainThread"])
                    processPool[coordinator].setAddingFinished(False)

                    # Wait it to finish
                    while not processPool[coordinator].getAddingFinished():
                        time.sleep(0.1)

                    printProcessHistory(processPool)

            # Adds new process to the system
            elif "Add" in text:
                splitText = text.split()
                nodeID = splitText[1]

                if nodeID in processPool:
                    logging.warning("There already is a process with given ID \n")
                else:

                    # The new node gets the same consistency history as the coordinator node, because we assume that
                    # the system is consistent and all the nodes have the same history and state
                    processPool[nodeID] = process.Process(nodeID, processPool[coordinator].history,
                                                          nodeID is coordinator, lock)

                    printProcessHistory(processPool)

            # Removes a process from the system
            elif "Remove" in text:
                splitText = text.split()
                nodeID = splitText[1]
                if nodeID in processPool:

                    # Tell thread to start closing and then wait it to close
                    processPool[nodeID].setRunning(False)
                    processPool[nodeID].join()

                    # Delete the process from process pool
                    del processPool[nodeID]

                    # If the deleted node was an coordinator node choose a new coordinator node randomly
                    if nodeID == coordinator:
                        coordinator = random.choice(list(processPool.keys()))
                        processPool[coordinator].setCoordinator(True)

                    printProcessHistory(processPool)
                else:
                    logging.warning("There is no process with given ID to remove\n")

            # Tells the selected thread not to respond to any request or commands for given seconds
            elif "Time-failure" in text:
                splitText = text.split()
                nodeID = splitText[1]

                if nodeID in processPool:
                    processPool[nodeID].timeFailure(int(splitText[2]))

                    printProcessHistory(processPool)

                else:
                    logging.warning("There is no process with given ID\n")

            elif "Arbitrary-failure" in text:
                print("Sorry, not implemented\n")

            else:
                logging.warning("Please enter valid command!\n")

    # Exit the program by keyboard error, eg ctrl+c
    except KeyboardInterrupt:
        print("Start exiting!")
        for node in processPool:
            processPool[node].setRunning(False)
            processPool[node].join()
        print("All processes closed!")

# Start main
if __name__ == "__main__":
    main(sys.argv[1:])
