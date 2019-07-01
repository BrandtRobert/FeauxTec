def read_coils(data):
    data = data[1:]
    is_error = False

    start_coil = (data[0] << 8) | (data[1])
    num_coils = (data[2] << 8) | (data[3])

    if start_coil < 0:
        is_error = True
        return is_error, _invalid_register_addr(data)
        # return is_error,
    elif num_coils < 0:
        is_error = True
        return is_error, _invalid_data_value(data)
    else:
        return is_error, {
            'start_coil': start_coil,
            'num_coils': num_coils
        }


def read_discrete_inputs(data):
    data = data[1:]
    is_error = False

    start_input = (data[0] << 8) | (data[1])
    num_inputs = (data[2] << 8) | (data[3])

    if start_input < 0:
        is_error = True
        return is_error, _invalid_register_addr(data)
        # return is_error,
    elif num_inputs < 0:
        is_error = True
        return is_error, _invalid_data_value(data)
    else:
        return is_error, {
            'start_discrete_input': start_input,
            'num_discrete_inputs': num_inputs
        }


def read_holding_registers(data):
    data = data[1:]
    is_error = False

    start_register = (data[0] << 8) | (data[1])
    num_registers = (data[2] << 8) | (data[3])

    if start_register < 0:
        is_error = True
        return is_error, _invalid_register_addr(data)
        # return is_error,
    elif num_registers < 0:
        is_error = True
        return is_error, _invalid_data_value(data)
    else:
        return is_error, {
            'start_holding_register': start_register,
            'num_holding_registers': num_registers
        }


def read_input_registers(data):
    data = data[1:]
    is_error = False

    start_register = (data[0] << 8) | (data[1])
    num_registers = (data[2] << 8) | (data[3])

    if start_register < 0:
        is_error = True
        return is_error, _invalid_register_addr(data)
        # return is_error,
    elif num_registers < 0:
        is_error = True
        return is_error, _invalid_data_value(data)
    else:
        return is_error, {
            'start_register': start_register,
            'num_registers': num_registers
        }


def write_single_coil(data):
    data = data[1:]
    is_error = False

    coil_address = (data[0] << 8) | (data[1])
    value_to_write = (data[2] << 8) | (data[3])

    if coil_address < 0:
        is_error = True
        return is_error, _invalid_register_addr(data)

    if value_to_write == 0:
        switch = 'off'
    elif value_to_write == 0xFF00:
        switch = 'on'
    else:
        is_error = True
        return is_error, _invalid_data_value(data)

    return is_error, {
        'coil_address': coil_address,
        'switch': switch
    }


def write_single_holding_register(data):
    is_error = False
    data = data[1:]
    register_address = (data[0] << 8) | (data[1])
    value_to_write = (data[2] << 8) | (data[3])

    if register_address < 0:
        is_error = True
        return is_error, _invalid_register_addr(data)
    elif value_to_write < 0:
        is_error = True
        return is_error, _invalid_data_value(data)

    return is_error, {
        'register_address': register_address,
        'value_to_write': value_to_write
    }


def write_multiple_coils(data):
    data = data[1:]
    is_error = False

    first_coil = (data[0] << 8) | (data[1])
    num_coils_to_write = (data[2] << 8) | (data[3])
    num_bytes_of_coils = data[4]
    coil_values = data[5:5 + num_bytes_of_coils]

    if first_coil < 0:
        is_error = True
        return is_error, _invalid_register_addr(data)

    for val in coil_values:
        if val < 0:
            return is_error, _invalid_data_value(data)

    return is_error, {
        'start_coil': first_coil,
        'coil_values': coil_values,
        'num_coils': num_coils_to_write
    }


def write_multiple_holding_registers(data):
    data = data[1:]
    is_error = False

    first_register = (data[0] << 8) | (data[1])
    num_regs_to_write = (data[2] << 8) | (data[3])
    num_bytes_of_registers = data[4]
    print(data[5:])
    register_values = [0] * (num_bytes_of_registers // 2)
    # Each register value is 16 bits, decode every 2 bytes of data into one 16 bit value
    for i in range(0, num_bytes_of_registers // 2):
        idx = 5 + i * 2
        register_values[i] = (data[idx] << 8) | (data[idx + 1])

    if first_register < 0:
        is_error = True
        return is_error, _invalid_register_addr(data)

    for val in register_values:
        if val < 0:
            return is_error, _invalid_data_value(data)

    return is_error, {
        'start_register': first_register,
        'register_values': register_values,
        'num_registers': num_regs_to_write
    }


def invalid_function_code(data):
    code = data[0]
    is_error = True
    response_code = 0x80 | code
    error_code = 0x01
    response = (response_code << 8) | error_code
    return is_error, response.to_bytes(2, byteorder='big')


def _invalid_register_addr(data):
    function_code = data[0]
    error_code = 0x02
    return (((function_code | 0x80) << 8) | error_code).to_bytes(2, byteorder='big')


def _invalid_data_value(data):
    function_code = data[0]
    error_code = 0x03
    return (((function_code | 0x80) << 8) | error_code).to_bytes(2, byteorder='big')
