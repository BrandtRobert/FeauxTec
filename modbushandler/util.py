def stringify_bytes(bytes):
    return ''.join('\\x{:02x}'.format(b) for b in bytes)

