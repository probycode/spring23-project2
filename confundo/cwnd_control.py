#!/usr/bin/env python3
import unittest
from .common import *
# Constants (assuming they are defined somewhere in your code)
# MTU = 412
# CWND_INITIAL = 412
# SS_THRESH_INITIAL = 12000
# MAX_SEQNO = 50000

class CwndControl:
    '''Interface for the congestion control actions'''

    def __init__(self):
        self.cwnd = 1.0 * CWND_INITIAL  # Start with the initial congestion window size
        self.ssthresh = SS_THRESH_INITIAL  # Start with the initial slow-start threshold

    def on_ack(self, ackedDataLen):
        # This should be called for each ACK received that acknowledges new data.
        if self.cwnd < self.ssthresh:
            # Slow start phase
            self.cwnd += ackedDataLen
        else:
            # Congestion avoidance phase
            self.cwnd += (ackedDataLen * ackedDataLen) / self.cwnd
        # Ensure the cwnd does not exceed some max value (optional)
        self.cwnd = min(self.cwnd, MAX_SEQNO)

    def on_timeout(self):
        # This should be called when a timeout occurs, indicating a packet loss (or delay in ACK).
        self.ssthresh = max(self.cwnd / 2.0, MTU)  # Avoid ssthresh being less than one MTU
        self.cwnd = 1.0 * CWND_INITIAL  # Reset cwnd to initial window size

    def __str__(self):
        return f"cwnd: {self.cwnd}, ssthresh: {self.ssthresh}"


class TestCwndControl(unittest.TestCase):

    def test_on_ack_below_ssthresh(self):
        cc = CwndControl()
        cc.on_ack(MTU)
        self.assertEqual(cc.cwnd, CWND_INITIAL + MTU)

    def test_on_ack_above_ssthresh(self):
        cc = CwndControl()
        cc.cwnd = cc.ssthresh + MTU  # Force cwnd above ssthresh
        expected_cwnd = cc.cwnd + (MTU * MTU) / cc.cwnd
        cc.on_ack(MTU)
        self.assertEqual(cc.cwnd, expected_cwnd)

    def test_on_timeout(self):
        cc = CwndControl()
        cc.cwnd = 5000  # Set cwnd to a known value
        cc.on_timeout()
        self.assertEqual(cc.cwnd, CWND_INITIAL)
        self.assertEqual(cc.ssthresh, 2500)  # Should be half of cwnd

    def test_cwnd_not_exceed_max_seqno(self):
        cc = CwndControl()
        cc.cwnd = MAX_SEQNO
        cc.on_ack(MTU)
        self.assertEqual(cc.cwnd, MAX_SEQNO)


if __name__ == '__main__':
    unittest.main()
