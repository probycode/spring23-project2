#!/usr/bin/env python3
MOD = 50000 + 1

def format_line(command, pkt, cwnd, ssthresh):
    s = f"{command} {pkt.seqNum} {pkt.ackNum} {pkt.connId} {int(cwnd)} {ssthresh}"
    if pkt.isAck: s = s + " ACK"
    if pkt.isSyn: s = s + " SYN"
    if pkt.isFin: s = s + " FIN"
    if pkt.isDup: s = s + " DUP"
    return s

def incSeqNum(seqNumber, bytes):
    seqNumber += bytes
    if seqNumber >= MOD:
        seqNumber %= MOD
    return seqNumber