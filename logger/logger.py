import logging


def set_up_logger(logger_name, filename):
    # Set up a specific logger with our desired output level
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename, mode='w')
    handler.setLevel(logging.DEBUG)
    # create formatter
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s")
    # add formatter to ch
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
