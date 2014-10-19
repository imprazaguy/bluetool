import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())

def _log_to_handler(hdlr_type, *args):
    logger = getLogger(__name__)
    logger.setLevel(logging.INFO)
    hdlr = hdlr_type(*args)
    hdlr.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    logger.addHandler(hdlr)

    logger = logger.getLogger('{}.core.HCIWorker'.format(__name__))
    logger.propagate = False
    hdlr = hdlr_type(*args)
    hdlr.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] $(processName)s - $(message)s'))
    logger.addHandler(hdlr)

def log_to_stream(stream=None):
    _log_to_handler(logging.StreamHandler, stream)

def log_to_file(filename, mode='a'):
    _log_to_handler(logging.FileHandler, filename, mode)
