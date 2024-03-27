import logging
import sys 

def set_logger(log_path: str) -> None:
    ''' Enable logging to file & console '''
    # Empty old run
    with open(log_path, 'w') as lf:
        lf.write('New run.')
    log_fmt = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()
    file_handler = logging.FileHandler(log_path)
    rootLogger.setLevel(logging.INFO)
    file_handler.setFormatter(log_fmt)
    rootLogger.addHandler(file_handler)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(log_fmt)
    rootLogger.addHandler(stdout_handler)