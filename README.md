# CNT-4731 Project 2 (Confundo)

## Provided Files

`server.py` and `client.py` are the entry points for the server and client part of the project.

## Academic Integrity Note

You are encouraged to host your code in private repositories on [GitHub](https://github.com/), [GitLab](https://gitlab.com), or other places.  At the same time, you are PROHIBITED to make your code for the class project public during the class or any time after the class.  If you do so, you will be violating academic honestly policy that you have signed, as well as the student code of conduct and be subject to serious sanctions.

## Wireshark dissector

For debugging purposes, you can use the wireshark dissector from `confundo.lua`. The dissector requires
at least version 1.12.6 of Wireshark with LUA support enabled.

To enable the dissector for Wireshark session, use `-X` command line option, specifying the full
path to the `confundo.lua` script:

    wireshark -X lua_script:./confundo.lua

To dissect tcpdump-recorded file, you can use `-r <pcapfile>` option. For example:

    wireshark -X lua_script:./confundo.lua -r confundo.pcap

## Team Information
Name: `Avraham Moshe`
UID: `6283545`

Name: `Shawna-Lee Pommells`
UID: ``

Name: `Josias Chevalier`
UID: `6209275`

Contribution: As the sole member of this project, Avraham was responsible for all aspects of the project, including design, implementation, testing, and debugging.
High-Level Design Server Design

Initialization Phase: On startup, the server establishes a connection, initializes necessary resources, and waits for incoming client connections.

Processing Phase: For each client connection, the server processes the received packets, performs necessary computations, and sends back the results.

Termination Phase: Upon completing a session, the server closes the client connection and releases any utilized resources.

## Client Design
Setup Phase: The client establishes a connection to the server and exchanges initial handshake messages to ensure compatibility.

Data Transfer Phase: Once a connection is set up, the client sends data packets to the server and waits for the server's response. It implements error-checking mechanisms to ensure data integrity.

Closure Phase: After data exchange is completed, the client terminates the connection and finalizes any remaining processes.

## Challenges and Solutions
Challenge: Initial difficulties in establishing a stable connection between the server and client.

Solution: Reviewed and modified the connection settings, ensuring both the client and server used the same configuration.
Challenge: Inconsistent data transfer rates leading to occasional packet loss.

Solution: Implemented a retransmission strategy for the client to request lost packets, ensuring data consistency.
Challenge: Ensuring compatibility between different versions of the software.

Solution: Introduced a version-check during the handshake phase, prompting users to update if there's a mismatch.

