"""
Http Monitoring

Usage:
    http_monitoring.py log_file [--log]

Options:
    -h --help       Show this screen.
    log_file        Name or path to the log file to tail.
    threshold       Number of connection autorized before getting a warning
    --log           Name of the log file for the output (necessary ??)
"""

from threading import Thread, RLock
import time
import logging
import pandas as pd
import re
import datetime as dt


# A lock is used to prevent the different threads to access the dataframe
# at the same time
lock = RLock()

# Time interval between report
T_REPORT = 10
# Time range window to use to monitor the traffic
TM_WINDOW = 120
# Number of connection autorized during the window
THRESHOLD = 100


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
    """ Thread to keep track of the changes in the log file
    and update the dataframe containing the current data """

    def __init__(self, file_name, refresh_interval=0.1, log_name="tail.log"):
        self.file_name = file_name 
        # ecire quelque chose pour chemin absolu ou relatif
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
                            log.info(line)
                            with lock:
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
            time_report = dt.timedelta(seconds=T_REPORT)

            with lock:
                to_report = df[df.time > time_report]

            max_section = to_report.groupby('section').count().idmax()
            nb_section_hits = to_report.groupby('section').count().max()
            nb_users = to_report.groupby('ip_adress').size()
            nb_connections = len(to_report)

            log.info("Report for the last {}s : {} was the section with the most\
                hits ({} hits), {} connections were made, from {} users"\
            .format(T_REPORT, max_section, nb_section_hits, nb_connections, nb_users))
            # Not crucial but we make sure to wait exactly 10s even if the 
            # operations are taking some time
            time_to_wait = dt.timedelta(seconds=T_REPORT) - dt.datetime.now() + now
            time.sleep(time_to_wait.total_seconds)

class MonitorTraffic(Thread):
    """ Thread that send a warning if the traffic was above a certain
    value for more than 2 minutes. Send an other warning when the traffic
    gets back to normal """

    def __init__(self, threshold=THRESHOLD):
        self.on_alert = False
        self.threshold = threshold

    def run(self):
        while True:
            current_time = dt.datetime.now()
            interval_to_monitor = current_time - dt.timedelta(minutes=2)
            with lock:
                to_monitor = df[df.time > interval_to_monitor]
            nb_hits = len(to_monitor)

            if self.on_alert:
                if nb_hits < self.threshold:
                    log.warning("Traffic back to normal, for the last two minutes\
                    generated an alert - hits = {}, triggered at {}")\
                    .format(nb_hits, current_time)
            else:
                if nb_hits > self.high_threshold:
                    log.warning("High traffic for the last two minutes generated\
                    an alert - hits = {}, triggered at {}")\
                    .format(nb_hits, current_time)
                    self.on_alert = True
            clean_df()
            time.sleep(T_REPORT)

        # To do: find a way to calculate nb_hist without calculating the number of 
        # hits the last 2min but only the last 10s.
        # Idee use a queue  new_hits   --> [ | | | | | ]  --> old_hits
        # When the function is called the first time calculate nb_hits
        # Every 10s juste calculate: 
        # new_nb_hits = old_nb_hits + new_hits - old_hits
        # Implement a queue whom the size is equal to 2min / 10 i.e 12 elements
        # And create a push function which send you back the old_hits if the queue is full
        # This method allows us to limit the calculation and the memory usage,
        # We just need to keep in memory the data for the last 10s

    def run_updated(self):
        queue = Queue(TM_WINDOW / T_REPORT)
        while True:
            current_time = dt.datetime.now()
            interval_to_monitor = current_time - dt.timedelta(seconds=T_REPORT)
            with lock:
                to_monitor = df[df.time > interval_to_monitor]
            queue.push(len(to_monitor))
            nb_hits = queue.size()

            if self.on_alert:
                if nb_hits < self.threshold:
                    log.warning("Traffic back to normal, for the last two minutes\
                    generated an alert - hits = {}, triggered at {}")\
                    .format(nb_hits, current_time)
            else:
                if nb_hits > self.high_threshold:
                    log.warning("High traffic for the last two minutes generated\
                    an alert - hits = {}, triggered at {}")\
                    .format(nb_hits, current_time)
                    self.on_alert = True
            clean_df()
            time.sleep(T_REPORT)


class Queue(object):
    def __init__(self, queue_size):
        self.queue = []
        self.max_size = queue_size

    def push(self, element):
        if len(self.queue) < self.max_size:
            self.queue += element
            return None
        else:
            self.queue = [element] + self.queue
            return self.queue.pop() 

    def size(self):
        return sum(self.queue) 



def add_to_df(line):
    """ Add line to the dataframe """
    parsed_line = parse_log(line)
    # Format '10/Oct/2000:13:55:36 -0700'
    # The time zone is removed, we assume it is the same on the log file
    # and on the computer 
    time = dt.datetime.strptime(parsed_line[3][:-6], "%d/%b/%Y:%H:%M:%S")
    items = [parsed_line[i] for i in [0, 2, 5, 7]]
    # Get the section of the url
    section = '/'.join(items[3].split('/')[:4])
    # Add the row to the dataframe
    with lock:
        df.loc[time] = items.append(section) # Don't forget to replace '-' by NaNs


# Use a function? Or just instantiate the data frame at the beginning of the program?
def initiate_dataframe():
    """ Global variable is used to handle the data between the differents threads """
    global df
    df = pd.DataFrame(columns=['ip_adress', 'user_id', 'http_code', 'url', 'section'])
    df.index.name = 'time'


def clean_df():
    """ Function to remove old data and to limit the memory usage """
    if not 'df' in globals():
        initiate_dataframe()
    to_keep = dt.datetime.now() - dt.timedela(minutes=2)
    with lock:
        df = df[df.time > to_keep]
    # or del df[df.time < to_keep]

def parse_log(line):
    regex = r'([(\d\.)]+) ([^ ]+) ([^ ]+) \[(.*?)\] "(.*?)" (\d+|-) (\d+|-) (?:"(.*?)" "(.*?)")'
    match = re.match(regex, line)
    if match:
        return match.groups
    else:
        # Raise error in the log
        log.error("Impossible to parse line: {}").format(line)

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

if __name__ == '__main__':
    from docopt import docopt

    args = docopt(__doc__, version='Http Monitoring 1.0')

    if args[log_file]:
        log = make_a_log_file('http_monitoring.log', to_terminal=False)




