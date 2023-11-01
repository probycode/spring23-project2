import argparse
import socket
import sys
from confundo.header import Header

class ConfundoServer:

    def __init__(self, ip, port):
        self.server_ip = ip
        self.server_port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip, port))

        self.conn_id = None
        self.expected_seq_number = None

    def send_packet(self, syn=False, ack=False, fin=False, ack_num=0, conn_id=0, client_address=None):
        header = Header(0, ack_num, conn_id, ack, syn, fin)
        packet = header.encode()
        self.sock.sendto(packet, client_address)
        print(f"SEND 0 {ack_num} {conn_id} - -", end=" ")
        if ack: print("ACK", end=" ")
        if syn: print("SYN", end=" ")
        if fin: print("FIN", end=" ")
        print()

    def recv_packet(self):
        data, client_address = self.sock.recvfrom(424)
        header = Header.decode(data[:12])
        print(f"RECV {header.sequence_number} {header.acknowledgment_number} {header.connection_id} - -", end=" ")
        if header.ack: print("ACK", end=" ")
        if header.syn: print("SYN", end=" ")
        if header.fin: print("FIN", end=" ")
        print()
        return header, data[12:], client_address

    def handle_connection(self):
        header, flags, client_address= self.recv_packet()
        if header.syn:
            self.conn_id = header.connection_id + 1
            self.expected_seq_number = header.sequence_number + 1
            self.send_packet(syn=True, ack=True, ack_num=self.expected_seq_number, conn_id=self.conn_id, client_address=client_address)

    def handle_data_transfer(self):
        while True:
            header, data, client_address = self.recv_packet()
            if header.sequence_number == self.expected_seq_number:
                # expected data received
                self.expected_seq_number += len(data)
                self.send_packet(ack=True, ack_num=self.expected_seq_number, conn_id=self.conn_id, client_address=client_address)
            if header.fin:
                break

    def run(self):
        print(f"Server listening on {self.server_ip}:{self.server_port}")
        while True:
            self.handle_connection()
            self.handle_data_transfer()

if __name__ == "__main__":
    server = ConfundoServer("0.0.0.0", 5000)
    server.run()
