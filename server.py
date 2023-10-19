#!/usr/bin/env python3

import argparse
import os
import socket
import sys
import time

from confundo import Socket, GLOBAL_TIMEOUT, MAX_SEQNO

parser = argparse.ArgumentParser("Parser")
parser.add_argument("port", help="Set Port Number", type=int)
args = parser.parse_args()

def start():
    try:
        with Socket() as sock:
            sock.settimeout(GLOBAL_TIMEOUT)
            sock.bind(("0.0.0.0", int(args.port)))
            sock.listen(5)

            while True:
                client_sock = sock.accept()
                handle_client(client_sock)

    except RuntimeError as e:
        sys.stderr.write(f"ERROR: {e}\n")
        sys.exit(1)

def handle_client(client_sock):
    try:
        with client_sock:
            while True:
                data = client_sock.recv(MAX_SEQNO)
                if not data:
                    break
                # Handle received data (e.g., store it or process it)
                client_sock.settimeout(GLOBAL_TIMEOUT)

    except RuntimeError as e:
        sys.stderr.write(f"ERROR: {e}\n")

if __name__ == '__main__':
    start()
