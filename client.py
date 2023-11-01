#!/usr/bin/env python3

import argparse
import sys
import socket
import time
from confundo.header import Header
from confundo.common import DEFAULT_TIMEOUT, FIN_WAIT_TIMEOUT, MAX_SEQNO


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
        self.last_sent_data = None

    def update_cwnd(self):
        if self.cwnd < self.ss_thresh:
            self.cwnd *= 2
        else:
            self.cwnd += 412  # Increment linearly in the congestion avoidance phase

    def send_packet(self, syn=False, ack=False, fin=False, payload=b''):
        header = Header(self.seq_number, 0, self.conn_id, ack, syn, fin)
        packet = header.encode() + payload
        self.sock.sendto(packet, (self.server_ip, self.server_port))
        self.last_sent_data = (header, payload)  # Store the last sent data for potential retransmission
        print_msg = f"SEND {self.seq_number} {header.acknowledgment_number} {self.conn_id} {self.cwnd} {self.ss_thresh}"
        flags = [flag for flag, is_set in [("ACK", ack), ("SYN", syn), ("FIN", fin), ("DUP", False)] if is_set]
        print(f"{print_msg} {' '.join(flags)}")

    def recv_packet(self):
        try:
            data, _ = self.sock.recvfrom(424)
            header = Header.decode(data[:12])
            print_msg = f"RECV {header.sequence_number} {header.acknowledgment_number} {header.connection_id} {self.cwnd} {self.ss_thresh}"
            flags = [flag for flag, is_set in [("ACK", header.ack), ("SYN", header.syn), ("FIN", header.fin), ("DUP", False)] if is_set]
            print(f"{print_msg} {' '.join(flags)}")
            return header, data[12:]
        except socket.timeout:
            # Handle the retransmission logic here
            if self.last_sent_data:
                header, payload = self.last_sent_data
                self.send_packet(syn=header.syn, ack=header.ack, fin=header.fin, payload=payload)
            raise

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

    def update_sequence_number(self, increment_by=1):
        self.seq_number = (self.seq_number + increment_by) % (MAX_SEQNO + 1)

    def send_file(self):
        with open(self.filename, 'rb') as file:
            while True:
                data = file.read(self.cwnd)
                if not data:
                    break
                self.send_packet(ack=True, payload=data)
                while True:
                    header, _ = self.recv_packet()
                    if header.ack:
                        self.update_sequence_number(len(data))
                        self.update_cwnd()
                        break

    def close(self):
        self.send_packet(fin=True)
        start_time = time.time()
        while time.time() - start_time < FIN_WAIT_TIMEOUT:
            header, _ = self.recv_packet()
            if header.fin:
                self.send_packet(ack=True)

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



parser = argparse.ArgumentParser("Parser")
parser.add_argument("host", help="Set Hostname")
parser.add_argument("port", help="Set Port Number")
parser.add_argument("file", help="Set File Directory")
args = parser.parse_args()

client = ConfundoClient(args.host, int(args.port), args.file)
client.run()
