import logging
import os

from . import error

logging.getLogger(__name__).addHandler(logging.NullHandler())


def _log_to_handler(hdlr_type, *args):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    hdlr = hdlr_type(*args)
    hdlr.setFormatter(
        logging.Formatter(
            '%(asctime)s [%(levelname)s] (%(processName)s) %(message)s'))
    logger.addHandler(hdlr)


def log_to_stream(stream=None):
    _log_to_handler(logging.StreamHandler, stream)


def log_to_file(filename, mode='a'):
    _log_to_handler(logging.FileHandler, filename, mode)


def log_set_level(level):
    logging.getLogger(__name__).setLevel(level)


def run_config(cfg, dev_list=None):
    coord = cfg['coordinator']()
    if dev_list is not None:
        cfg['device'] = dev_list
    coord.load(cfg)
    coord.run()


def run_bluetest(filename, dev_list=None):
    if not os.path.exists(filename):
        raise error.TestError('file does not exist: {}'.filename)
    fname = os.path.basename(filename)
    mod_name, ext = os.path.splitext(fname)
    if ext != '.py':
        raise error.TestError('test file does not have file extension \'.py\'')

    import imp
    mod = imp.load_source('bluetest', filename)
    cfg = getattr(mod, 'bluetest')
    run_config(cfg, dev_list)
