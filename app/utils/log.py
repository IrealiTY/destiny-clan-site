import logging
import sys

def get_logger(logger_name):
    """TODO: move to <project root>/app/utilities.py"""
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    log_stream_handler = logging.StreamHandler(sys.stdout)
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(message)s')
    log_stream_handler.setFormatter(log_formatter)
    logger.addHandler(log_stream_handler)
    return logger
