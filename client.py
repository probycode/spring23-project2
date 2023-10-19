#!/usr/bin/env python3

import argparse
import os
import socket
import sys

import confundo
from confundo import GLOBAL_TIMEOUT, MAX_SEQNO

parser = argparse.ArgumentParser("Parser")
parser.add_argument("host", help="Set Hostname")
parser.add_argument("port", help="Set Port Number", type=int)
parser.add_argument("file", help="Set File Directory")
args = parser.parse_args()

def start():
    try:
        with confundo.Socket() as sock:
            sock.settimeout(GLOBAL_TIMEOUT)
            sock.connect((args.host, int(args.port)))

            with open(args.file, "rb") as f:
                data = f.read(MAX_SEQNO)
                while data:
                    total_sent = 0
                    while total_sent < len(data):
                        sent = sock.send(data[total_sent:])
                        total_sent += sent
                        data = f.read(MAX_SEQNO)
    except RuntimeError as e:
        sys.stderr.write(f"ERROR: {e}\n")
        sys.exit(1)

if __name__ == '__main__':
    start()
