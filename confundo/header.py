import struct
class Header:
    def __init__(self, sequence_number=0, acknowledgment_number=0,
                 connection_id=0, ack=False, syn=False, fin=False):
        self.sequence_number = sequence_number
        self.acknowledgment_number = acknowledgment_number if ack else 0
        self.connection_id = connection_id
        self.ack = ack
        self.syn = syn
        self.fin = fin

    def encode(self):
        # Create flags
        flags = 0
        if self.ack:
            flags |= (1 << 2)
        if self.syn:
            flags |= (1 << 1)
        if self.fin:
            flags |= 1

        # Pack the header into bytes
        return struct.pack('!I I H H', self.sequence_number,
                           self.acknowledgment_number, self.connection_id,
                           flags)

    @classmethod
    def decode(cls, data):
        # Unpack the header from bytes
        sequence_number, acknowledgment_number, connection_id, flags = \
            struct.unpack('!I I H H', data[:12])

        # Extract flags
        ack = bool(flags & (1 << 2))
        syn = bool(flags & (1 << 1))
        fin = bool(flags & 1)

        return cls(sequence_number, acknowledgment_number,
                   connection_id, ack, syn, fin)

    def __str__(self):
        return f"Seq: {self.sequence_number}, Ack: {self.acknowledgment_number}, " \
               f"ConnID: {self.connection_id}, Flags: {('A' if self.ack else '')}" \
               f"{('S' if self.syn else '')}{('F' if self.fin else '')}"


if __name__ == '__main__':
    # Test the Header class
    header = Header(1000, 2000, 300, True, True, False)
    encoded_data = header.encode()
    decoded_header = Header.decode(encoded_data)
    print(header)

    assert header.sequence_number == decoded_header.sequence_number
    assert header.acknowledgment_number == decoded_header.acknowledgment_number
    assert header.connection_id == decoded_header.connection_id
    assert header.ack == decoded_header.ack
    assert header.syn == decoded_header.syn
    assert header.fin == decoded_header.fin

    print("Test passed!")
