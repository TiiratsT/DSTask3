import sys
import logging
import process
from threading import Event

processes = []
coordinator = ""
historyType = ""
states = []

def main(argv):
    global processes, states, coordinator, historyType

    f = open(argv[0], "r")
    nextLine = ""
    for line in f:
        if "System" in line:
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

        if "State" in nextLine:
            nextLine = f.readline()
            strings = nextLine.split(";")
            historyType = strings[0]
            for number in strings[1].split(","):
                states.append(int(number))
    f.close()

    print("\nProcesses: " + str(processes))
    print("Coordinator: " + coordinator)
    print("History-Type: " + historyType)
    print("States: " + str(states) + "\n")


    # Create threads
    processPool = {}

    for node in processes:
        processPool[node] = process.Process(node)

    # Command line interface
    try:
        while True:
            text = input("Choose next command (Set-value, Rollback, Add, Remove, Time-failure, Arbitrary-failure)\n")

            if "Set-value" in text:
                print("Sorry, not implemented\n")
            elif "Rollback" in text:
                print("Sorry, not implemented\n")
            elif "Add" in text:
                print("Sorry, not implemented\n")
            elif "Remove" in text:
                print("Sorry, not implemented\n")
            elif "Time-failure" in text:
                print("Sorry, not implemented\n")
            elif "Arbitrary-failure" in text:
                print("Sorry, not implemented\n")
            else:
                logging.warning("Please enter valid command!\n")

    except KeyboardInterrupt:
        print("Start exiting!")
        for node in processPool:
            processPool[node].setRunning(False)
            processPool[node].join()
        print("All processes closed!")


if __name__ == "__main__":
    main(sys.argv[1:])