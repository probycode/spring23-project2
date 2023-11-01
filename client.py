#!/usr/bin/env python3

import argparse
import sys
import socket
import time
from confundo.header import Header
from confundo.common import DEFAULT_TIMEOUT, FIN_WAIT_TIMEOUT


class ConfundoClient:

    def __init__(self, server_ip, server_port, filename):
        self.server_ip = server_ip
        self.server_port = server_port
        self.filename = filename
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(DEFAULT_TIMEOUT)

        self.cwnd = 412
        self.ss_thresh = 12000
        self.conn_id = 0
        self.seq_number = 50000
        self.ack_num = 0

    def send_packet(self, syn=False, ack=False, fin=False, payload=b''):
        header = Header(self.seq_number, 0, self.conn_id, ack, syn, fin)
        packet = header.encode() + payload
        self.sock.sendto(packet, (self.server_ip, self.server_port))
        print(f"SEND {self.seq_number} 0 {self.conn_id} {self.cwnd} {self.ss_thresh}", end=" ")
        if ack: print("ACK", end=" ")
        if syn: print("SYN", end=" ")
        if fin: print("FIN", end=" ")
        self.ack_num = header.acknowledgment_number
        print()

    def recv_packet(self):
        data, _ = self.sock.recvfrom(424)
        header = Header.decode(data[:12])
        print(
            f"RECV {header.sequence_number} {header.acknowledgment_number} {header.connection_id} {self.cwnd} {self.ss_thresh}",
            end=" ")
        if header.ack: print("ACK", end=" ")
        if header.syn: print("SYN", end=" ")
        if header.fin: print("FIN", end=" ")
        print()
        return header, data[12:]

    def connect(self):
        try:
            # Step 1: SYN
            self.send_packet(syn=True)

            # Step 2: Wait for SYN|ACK
            header, _ = self.recv_packet()
            if header.syn and header.ack:
                self.conn_id = header.connection_id
                self.seq_number += 1  # Increment sequence number
                self.send_packet(ack=True)  # Send an ACK packet, not another SYN

            else:
                sys.stderr.write("ERROR: Unexpected server response during handshake.\n")
                sys.exit(1)

        except socket.timeout:
            sys.stderr.write("ERROR: Connection timed out during handshake.\n")
            sys.exit(1)

    def send_file(self):
        with open(self.filename, 'rb') as file:
            while True:
                data = file.read(self.cwnd)
                if not data:
                    break
                self.send_packet(ack=True, payload=data)
                print(f"SEND {self.seq_number} {self.ack_num} {self.conn_id} {self.cwnd} {self.ss_thresh} ACK")
                # Wait for an ACK for this chunk
                while True:
                    header, _ = self.recv_packet()
                    if header.ack:
                        break

    def close(self):
        self.send_packet(fin=True)
        header, _ = self.recv_packet()
        if not header.ack:
            sys.stderr.write("ERROR: Unexpected server response during termination\n")
            sys.exit(1)
        time.sleep(FIN_WAIT_TIMEOUT)

    def run(self):
        try:
            self.connect()
            self.send_file()
            self.close()
        except socket.timeout:
            sys.stderr.write("ERROR: Connection timed out\n")
            sys.exit(1)
        except Exception as e:
            sys.stderr.write(f"ERROR: {str(e)}\n")
            sys.exit(1)
        finally:
            self.sock.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Parser")
    parser.add_argument("host", help="Set Hostname")
    parser.add_argument("port", help="Set Port Number")
    parser.add_argument("file", help="Set File Directory")
    args = parser.parse_args()
    print(args)

    client = ConfundoClient(args.host, int(args.port), args.file)
    client.run()
