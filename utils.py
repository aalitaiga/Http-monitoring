from threading import Thread
import time
import logging
import pandas as pd
import re
import init_df


class TailLogFile(Thread):
    """ Thread to keep track of the changes in the log file """
    def __init__(self, file_name, refresh_interval=0.1, log_name="tail.log"):
        Thread.__init__(self)
        if not isinstance(file_name, str):
            raise TypeError("Please enter a correct name for the file")
        self.file_name = file_name
        self.refresh_interval = refresh_interval
        self.log_name = log_name
        self.terminated = False

    def run(self):     
        if not 'df' in globals():
            initiate_dataframe()
        print_log = make_a_log_file(self.log_name, to_terminal=False)
        with open(self.file_name, 'r') as file_:
                # Go to the end of file
                file_.seek(0,2)
                while not self.terminated:
                    curr_position = file_.tell()
                    lines = file_.readlines()
                    if not lines:
                        file_.seek(curr_position)
                    else:
                        for line in lines:
                            if line is not None:
                                print_log.info(line)
                    time.sleep(self.refresh_interval)
    def stop(self):
        self.terminated = True

class WriteRandomStuff(Thread):
    """ Thread that writes in the time in a log,
    used for testing. """

    def __init__(self, log_name, duration, time_interval=0.1):
        Thread.__init__(self)
        self.duration = duration
        self.log_name = log_name
        self.time_interval = time_interval

    def run(self):
        test_log = make_a_log_file(self.log_name, to_terminal=False)
        start_time = time.time()

        while time.time() - start_time < self.duration:
            test_log.info("")
            time.sleep(self.time_interval)

def make_a_log_file(name, to_terminal = True, to_filename = True,
                    terminal_level="INFO", file_level = "INFO"):
    """
    Create a new logger or also get the reference from an existing one
    :param name: the name of the logger
    :param to_terminal: if logging should go to terminal
    :param to_filename: if logging should go to a file
    :param terminal_level: logging file level
    :param file_level: logging terminal level
    :return: logger object
    """
    logger = logging.getLogger(name)

    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    if to_filename:
        fh = logging.FileHandler(name, encoding='UTF-8')
        fh.setLevel(file_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    if to_terminal:
        ch = logging.StreamHandler()
        ch.setLevel(terminal_level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger

def parse_log(line):
    pass



    
