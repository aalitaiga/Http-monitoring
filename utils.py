from threading import Thread
import time
import logging
import pandas as pd
import re
import init_df
import datetime as dt

# To do add, something to start the thread together

log = make_a_log_file('write.log', to terminal=False)

class WriteRandomStuff(Thread):
    """ Thread that writes the time in a log,
    used for testing. """

    def __init__(self, log_name, duration, time_interval=0.1):
        self.duration = duration
        self.log_name = log_name
        self.time_interval = time_interval

    def run(self):
        test_log = make_a_log_file(self.log_name, to_terminal=False)
        start_time = time.time()

        while time.time() - start_time < self.duration:
            test_log.info("")
            time.sleep(self.time_interval)

class TailLogFile(Thread):
    """ Thread to keep track of the changes in the log file """

    def __init__(self, file_name, refresh_interval=0.1, log_name="tail.log"):
        self.file_name = file_name
        self.refresh_interval = refresh_interval
        self.log_name = log_name
        self.terminated = False

    def run(self):     
        if not 'df' in globals():
            initiate_dataframe()
        #print_log = make_a_log_file(self.log_name, to_terminal=False)
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
                                log.info(line)
                                add_to_df(line)
                    time.sleep(self.refresh_interval)
    def stop(self):
        self.terminated = True

class SendReport(Thread):
    """ Thread used to send a report every 10s """
    def __init__(self):
        Thread.__init__(self)
        # Do something to start to tail?

    def run(self):
        while True:
            now = dt.datetime.now()
            time_report = dt.timedelta(seconds=10)
            to_report = df[df.time > time_report]
            max_section = to_report.groupby('section').count().idmax()
            nb_hits = to_report.groupby('section').count().max()
            nb_users = to_report.groupby('ip_adress').size()
            nb_connections = len(to_report)

            log.info("Report for the last 10s : {} was the section with the most\
                hits ({} hits), {} connections were made, from {} users"\
                .format(max_section, nb_hits, nb_connections, nb_users))
            # Not crucial but we make sure 10 wait exactly 10s even if the 
            # operations are taking some time
            time_to_wait = dt.timedelta(seconds=10) - dt.datetime.now() + now
            sleep(time_to_wait.total_seconds)

class MonitorTraffic(Thread):
    """ Thread that send a warning if the traffic was above a certain
    value for more than 2 minutes. Send an other warning when the traffic
    gets back to normal """

    def __init__(self, threshold=100):
        self.on_alert = False
        self.threshold = threshold

    def run(self):
        while True:
            current_time = dt.datetime.now()
            interval_to_monitor = dt.timedelta(minutes=2)
            to_monitor = df[df.time > time_report]

            if self.on_alert:

            else:
                nb_hits = len(to_monitor)

                if nb_hits > value:
                    log.warning()


def add_to_df(line):
    """ Add line to the dataframe """
    parsed_line = parse_log(line)

    # Format '10/Oct/2000:13:55:36 -0700'
    # The time zone is removed, we used it is the same on the log file
    # and on the computer 
    time = dt.datetime.strptime(parsed_line[3][:-6], "%d/%b/%Y:%H:%M:%S")
    items = [parsed_line[i] for i in [0, 2, 5, 7]]

    # Get the section of the url
    section = '/'.join(items[3].split('/')[:4])

    # Add the row to the dataframe
    df.loc[time] = items.append(section)

def initiate_dataframe():
    global df
    df = pd.DataFrame(columns=['ip_adress', 'user_id', 'http_code', 'url', 'section'])
    df.index.name = 'time'

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
    regex = r'([(\d\.)]+) ([^ ]+) ([^ ]+) \[(.*?)\] "(.*?)" (\d+|-) (\d+|-) (?:"(.*?)" "(.*?)")'
    match = re.match(regex, line)
    if match:
        return match.groups
    else:
        # Raise error in the log 