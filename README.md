## DSTask3

The code can be run in /dist folder with command `two-phase-program.exe 2PC.txt`. The processes are implemented as threads, 
each thread has its id, history and shared lock for printing.

The program can read the input file and based on that creates all the processes. We implemented Set-value, Rollback, Add,
Remove and Time-failure command. The only command not implemented is Arbitrary-failure. The system right now does not have
error recovery or timeout, but it does every adding and rollback based on 2PC algorithm (prewrite->ACK->commit->ACK).
Time-failure just blocks the communication in the node for given time as it will not respond or read any commands in that time.

The video showing the program running is accessible here: `dummy link`