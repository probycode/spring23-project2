# -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-
#!/usr/bin/env python3
import os


from enum import Enum
import socket
import sys
import time

from .common import *
from .packet import Packet
from .cwnd_control import CwndControl
from .util import *


class State(Enum):
    INVALID = 0
    SYN = 1
    OPEN = 3
    LISTEN = 4
    FIN = 10
    FIN_WAIT = 11
    CLOSED = 20
    ERROR = 21


# class TimeoutError:
#     pass

def incSeqNum(seqNum, amount):
    return (seqNum + amount) % (MAX_SEQNO + 1)

class Socket:
    '''Incomplete socket abstraction for Confundo protocol'''

    def __init__(self, connId=0, inSeq=None, synReceived=False, sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM),
                 noClose=False):
        self.sock = sock
        self.connId = connId
        self.sock.settimeout(RETX_TIME)
        self.timeout = GLOBAL_TIMEOUT

        self.base = MAX_SEQNO  # Last packet from this side that has been ACK'd
        self.seqNum = self.base

        self.inSeq = inSeq

        self.lastAckTime = time.time() # last time ACK was sent / activity timer
        self.cc = CwndControl()
        self.outBuffer = b""
        self.inBuffer = b""
        self.state = State.INVALID
        self.nDupAcks = 0

        self.synReceived = synReceived
        self.finReceived = False

        self.remote = None
        self.noClose = noClose

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.state == State.OPEN:
            self.close()
        if self.noClose:
            return
        self.sock.close()

    def connect(self, endpoint):
        remote = socket.getaddrinfo(endpoint[0], endpoint[1], family=socket.AF_INET, type=socket.SOCK_DGRAM)
        (family, type, proto, canonname, sockaddr) = remote[0]

        return self._connect(sockaddr)

    def bind(self, endpoint):
        if self.state != State.INVALID:
            raise RuntimeError()

        remote = socket.getaddrinfo(endpoint[0], endpoint[1], family=socket.AF_INET, type=socket.SOCK_DGRAM)
        (family, type, proto, canonname, sockaddr) = remote[0]

        self.sock.bind(sockaddr)
        self.state = State.LISTEN

    def listen(self, queue):
        if self.state != State.LISTEN:
            raise RuntimeError("Cannot listen")
        pass

    def accept(self):
        if self.state != State.LISTEN:
            raise RuntimeError("Cannot accept")

        hadNewConnId = True
        while True:
            # just wait forever until a new connection arrives

            if hadNewConnId:
                self.connId += 1 # use it for counting incoming connections, no other uses really
                hadNewConnId = False
            pkt = self._recv()
            if pkt and pkt.isSyn:
                hadNewConnId = True
                ### UPDATE CORRECTLY HERE
                clientSock = Socket(connId=self.connId, synReceived=True, sock=self.sock, inSeq=self.inSeq,
                                    noClose=True)
                # at this point, syn was received, ack for syn was sent, now need to send our SYN and wait for ACK
                clientSock._connect(self.lastFromAddr)
                return clientSock

    def settimeout(self, timeout):
        self.timeout = timeout

    def _send(self, packet):
        '''"Private" method to send packet out'''

        if self.remote:
            self.sock.sendto(packet.encode(), self.remote)
        else:
            self.sock.sendto(packet.encode(), self.lastFromAddr)
        print(format_line("SEND", packet, self.cc.cwnd, self.cc.ssthresh))

    def _recv(self):
        '''"Private" method to receive incoming packets'''

        try:
            (inPacket, self.lastFromAddr) = self.sock.recvfrom(412 + 12)
        except socket.error as e:
            return None

        ### TODO dispatch based on fromAddr... and it can only be done from the "parent" socket

        inPkt = Packet().decode(inPacket)
        print(format_line("RECV", inPkt, self.cc.cwnd, self.cc.ssthresh))

        outPkt = None
        if inPkt.isSyn:
            ### UPDATE CORRECTLY HERE
            self.inSeq = incSeqNum(inPkt.seqNum, 1)
            if inPkt.connId != 0:
                self.connId = inPkt.connId
            self.synReceived = True
            outPkt = Packet(seqNum=self.seqNum, ackNum=self.inSeq, connId=self.connId, isAck=True)

        elif inPkt.isFin:
            if self.inSeq == inPkt.seqNum: # all previous packets has been received, so safe to advance
                ### UPDATE CORRECTLY HERE
                self.inSeq = incSeqNum(self.inSeq, 1)
                self.finReceived = True
            else:
                # don't advance, which means we will send a duplicate ACK
                pass

            outPkt = Packet(seqNum=self.seqNum, ackNum=self.inSeq, connId=self.connId, isAck=True)

        elif len(inPkt.payload) > 0:
            if not self.synReceived:
                raise RuntimeError("Receiving data before SYN received")

            if self.finReceived:
                raise RuntimeError("Received data after getting FIN (incoming connection closed)")

            if self.inSeq == inPkt.seqNum: # all previous packets has been received, so safe to advance
                ### UPDATE CORRECTLY HERE
                self.inSeq = incSeqNum(self.inSeq, len(inPkt.payload))
                self.inBuffer += inPkt.payload
            else:
                # don't advance, which means we will send a duplicate ACK
                pass

            outPkt = Packet(seqNum=self.seqNum, ackNum=self.inSeq, connId=self.connId, isAck=True)

        if outPkt:
            self._send(outPkt)

        return inPkt

    def _connect(self, remote):
        self.remote = remote

        if self.state != State.INVALID:
            raise RuntimeError("Trying to connect, but socket is already opened")

        self.sendSynPacket()
        self.state = State.SYN

        self.expectSynAck()

    def close(self):
        if self.state != State.OPEN:
            raise RuntimeError("Trying to send FIN, but socket is not in OPEN state")

        self.sendFinPacket()
        self.state = State.FIN

        self.expectFinAck()

    def sendSynPacket(self):
        # updated
        synPkt = Packet(seqNum=self.seqNum, connId=self.connId, isSyn=True)
        self.seqNum = incSeqNum(self.seqNum, 1)  # Incrementing the sequence number correctly
        self._send(synPkt)

    def expectSynAck(self):
        ### MAY NEED FIXES IN THIS METHOD
        startTime = time.time()
        while True:
            pkt = self._recv()
            if pkt and pkt.isAck and pkt.ackNum == self.seqNum:
                self.base = self.seqNum
                self.state = State.OPEN
                if self.synReceived:
                    break
            if time.time() - startTime > GLOBAL_TIMEOUT:
                self.state = State.ERROR
                raise RuntimeError("timeout")

    def sendFinPacket(self):
        synPkt = Packet(seqNum=self.seqNum, connId=self.connId, isFin=True)
        ### UPDATE CORRECTLY HERE
        self.seqNum = incSeqNum(self.seqNum, 1)
        self._send(synPkt)

    def expectFinAck(self):
        ### MAY NEED FIXES IN THIS METHOD
        startTime = time.time()
        tWaitTime = None
        while True:
            pkt = self._recv()
            currentTime = time.time()
            if pkt and pkt.isAck and pkt.ackNum == self.seqNum:
                self.base = self.seqNum
                tWaitTime = currentTime

            if currentTime - startTime > GLOBAL_TIMEOUT:
                self.state = State.ERROR
                raise TimeoutError("timeout")

            if tWaitTime and currentTime - tWaitTime > FIN_WAIT_TIME:
                self.state = State.CLOSED
                return

    def recv(self, maxSize):
        startTime = time.time()
        while len(self.inBuffer) == 0:
            self._recv()
            if self.finReceived:
                return None
            if time.time() - startTime > GLOBAL_TIMEOUT:
                self.state = State.ERROR
                raise RuntimeError("timeout")

        if len(self.inBuffer) > 0:
            actualResponseSize = min(len(self.inBuffer), maxSize)
            response = self.inBuffer[:actualResponseSize]
            self.inBuffer = self.inBuffer[actualResponseSize:]

            return response

    def send(self, data):
        '''
        This is one of the methods that require fixes.  Besides the marked place where you need
        to figure out proper updates (to make basic transfer work), this method is the place
        where you should initate congestion control operations.   You can either directly update cwnd, ssthresh,
        and anything else you need or use CwndControl class, up to you.  There isn't any skeleton code for the
        congestion control operations.  You would need to update things here and in `format_msg` calls
        in this file to properly print values.
        '''

        if self.state != State.OPEN:
            raise RuntimeError("Trying to send FIN, but socket is not in OPEN state")

        self.outBuffer += data

        reTrans = False
        startTime = time.time()
        while len(self.outBuffer) > 0:
            if reTrans:
                self.seqNum = self.base

            dataS = (MOD + (self.seqNum - self.base)) % MOD
            byteS = 0

            while True:
                toSend = self.outBuffer[dataS:dataS+MTU]

                lts = len(toSend)
                if (self.cc.cwnd - dataS) < lts or lts == 0:
                    break
                pkt = Packet(seqNum=self.seqNum, connId=self.connId, payload=toSend, isDup=reTrans)
                ### UPDATE CORRECTLY HERE
                self.seqNum = incSeqNum(self.seqNum, len(pkt.payload))
                self._send(pkt)

                dataS += len(pkt.payload)
                byteS += len(pkt.payload)

            pkt = self._recv()  # if within RTO we didn't receive packets, things will be retransmitted
            # update
            if pkt and pkt.isAck:
                # Handling new ack or duplicate ack correctly
                advanceAmount = (pkt.ackNum - self.base) % MOD
                if advanceAmount == 0:
                    self.nDupAcks += 1
                    # Initiate congestion control if there are three duplicate ACKs
                    if self.nDupAcks == 3:
                        self.cc.on_three_dup_acks()  # This function would handle the congestion control
                else:
                    self.outBuffer = self.outBuffer[advanceAmount:]
                    self.base = pkt.ackNum
                    self.nDupAcks = 0
                    self.cc.on_ack(advanceAmount)  # Congestion control on successful ACK reception

                if advanceAmount > 0 or self.nDupAcks >= 3:
                    # Resetting retransmission timer
                    startTime = time.time()

            if time.time() - startTime > GLOBAL_TIMEOUT:
                self.state = State.ERROR
                raise RuntimeError("timeout")

        return len(data)


# ----------------------- tests
import unittest

# Constants you may need for the tests
TEST_IP = "127.0.0.1"
TEST_PORT = 12345
TEST_DATA = b"Hello, World!"
TEST_TIMEOUT = 5


class TestSocket(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures, if any."""
        self.socket = Socket()

    def tearDown(self):
        """Tear down test fixtures, if any."""
        self.socket.close()

    def test_socket_creation(self):
        """Test socket creation and initial state."""
        self.assertEqual(self.socket.state, Socket.State.INVALID)

    def test_socket_bind(self):
        """Test socket binding to an endpoint."""
        self.socket.bind((TEST_IP, TEST_PORT))
        self.assertEqual(self.socket.state, Socket.State.LISTEN)

    def test_socket_connect(self):
        """Test socket connection to a remote endpoint."""
        try:
            self.socket.connect((TEST_IP, TEST_PORT))
        except Exception as e:
            self.fail(f"Socket connection failed: {e}")

    def test_socket_send(self):
        """Test sending data over socket."""
        self.socket.connect((TEST_IP, TEST_PORT))
        sent_len = self.socket.send(TEST_DATA)
        self.assertEqual(sent_len, len(TEST_DATA))

    def test_socket_recv(self):
        """Test receiving data over socket."""
        self.socket.bind((TEST_IP, TEST_PORT))
        # Here you might need a way to simulate sending data to the socket
        data = self.socket.recv(len(TEST_DATA))
        self.assertEqual(data, TEST_DATA)

    def test_socket_timeout(self):
        """Test socket timeout."""
        self.socket.settimeout(TEST_TIMEOUT)
        self.socket.bind((TEST_IP, TEST_PORT))
        with self.assertRaises(RuntimeError):
            self.socket.recv(1024)  # Assuming this will timeout

    # Add more tests depending on what functionalities you need to test.


if __name__ == '__main__':
    unittest.main()