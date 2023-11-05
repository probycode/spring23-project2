# -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-
# Copyright 2019 Alex Afanasyev
#
#!/usr/bin/env python3
import unittest
import struct

from .common import Header

class Packet(Header):
    '''Abstraction to handle the whole Confundo packet (e.g., with payload, if present)'''

    def __init__(self, payload=b"", isDup=False, **kwargs):
        super(Packet, self).__init__(**kwargs)
        self.payload = payload
        self.isDup = isDup # only for printing flags

    @classmethod
    def decode(cls, fullPacket):
        # First, decode the header part of the packet
        header = super(Packet, cls).decode(fullPacket[:12])
        # Create a new Packet instance with the payload
        return cls(sequence_number=header.sequence_number,
                   acknowledgment_number=header.acknowledgment_number,
                   connection_id=header.connection_id,
                   ack=header.ack, syn=header.syn, fin=header.fin,
                   payload=fullPacket[12:])

    def encode(self):
        return super(Packet, self).encode() + self.payload



# class TestPacket(unittest.TestCase):
    
#     def test_packet_encode(self):
#         """Test the Packet encoding."""
#         packet = Packet(sequence_number=12345, acknowledgment_number=67890, connection_id=12,
#                         ack=True, syn=False, fin=True, payload=b'Hello', isDup=False)
#         encoded = packet.encode()
#         # The expected byte format is: sequence number (4 bytes), acknowledgment number (4 bytes),
#         # connection_id (2 bytes), flags (2 bytes), followed by payload.
#         # Flags: ACK = 0b100, SYN = 0b000, FIN = 0b001
#         expected_flags = (1 << 2) | (1)  # ACK + FIN
#         self.assertEqual(encoded, struct.pack('!I I H H', 12345, 67890, 12, expected_flags) + b'Hello')

#     def test_packet_decode(self):
#         """Test the Packet decoding."""
#         # Flags: ACK = 0b100, SYN = 0b000, FIN = 0b001
#         flags = (1 << 2) | (1)  # ACK + FIN
#         raw_packet = struct.pack('!I I H H', 12345, 67890, 12, flags) + b'Hello'
#         packet = Packet.decode(raw_packet)
#         self.assertEqual(packet.sequence_number, 12345)
#         self.assertEqual(packet.acknowledgment_number, 67890)
#         self.assertEqual(packet.connection_id, 12)
#         self.assertTrue(packet.ack)
#         self.assertFalse(packet.syn)
#         self.assertTrue(packet.fin)
#         self.assertEqual(packet.payload, b'Hello')

#     def test_packet_payload(self):
#         """Test the Packet payload handling."""
#         payload = b"Test Payload"
#         packet = Packet(sequence_number=1, payload=payload)
#         self.assertEqual(packet.payload, payload)
#         encoded = packet.encode()
#         decoded_packet = Packet.decode(encoded)
#         self.assertEqual(decoded_packet.payload, payload)

#     def test_packet_str(self):
#         """Test the __str__ method for correct flag representation."""
#         packet = Packet(sequence_number=1, ack=True, syn=True, fin=False)
#         self.assertIn('A', str(packet))
#         self.assertIn('S', str(packet))
        
#         packet.isDup = True  # isDup should not affect the string representation of the flags
#         self.assertIn('A', str(packet))
#         self.assertIn('S', str(packet))

# # To run the tests
# if __name__ == '__main__':
#     unittest.main()