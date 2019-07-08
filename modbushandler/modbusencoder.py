import struct
from typing import Dict


# Set's all the needed fields or puts in default values
def _get_header_contents_or_default(header) -> Dict:
    transaction_id = int(header.get('transaction_id', 0))
    protocol_id = int(header.get('protocol_id', 0))
    unit_id = int(header.get('unit_id', 0))
    function_code = int(header.get('function_code', 0x80))
    return {
        'transaction_id': transaction_id,
        'protocol_id': protocol_id,
        'unit_id': unit_id,
        'function_code': function_code
    }


def _pack_header(header, endian_char):
    return struct.pack(endian_char + 'hhhbb', header['transaction_id'],
                       header['protocol_id'], header['length'], header['unit_id'], header['function_code'])


def respond_read_registers(header, registers, endianness='BIG'):
    endian_char = '>' if endianness == 'BIG' else '<'
    # get header contents or default
    header = _get_header_contents_or_default(header)
    header['length'] = 3 + 2 * len(registers)

    header = _pack_header(header, endian_char)
    register_count = struct.pack(endian_char + 'b', len(registers) * 2)

    response = header + register_count
    for register in registers:
        response += struct.pack(endian_char + 'h', register)
    return response


def respond_write_registers(header, start_register, num_registers, endianness='BIG'):
    endian_char = '>' if endianness == 'BIG' else '<'
    header = _get_header_contents_or_default(header)
    header['length'] = 6
    header = _pack_header(header, endian_char)
    body = struct.pack(endian_char + 'hh', start_register, num_registers)
    return header + body

