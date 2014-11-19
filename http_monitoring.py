"""
Http Monitoring

Usage:
    http_monitoring.py <log_file>
    http_monitoring.py (-h | --help)

Options:
    -h --help       Show this screen.
    logfile        Name or path to the log file to tail.
"""

from threading import Thread, RLock
import time
import logging
import pandas as pd
import re
import datetime as dt

bstr = '127.0.0.1 - adrien [{} -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326 "http://www.example.com/start.html" "Mozilla/4.08 [en] (Win98; I ;Nav)"'

# A lock is used to prevent the different threads to access the dataframe
# at the same time
lock = RLock()
# Time interval between report
T_REPORT = 10
# Time range window to use to monitor the traffic
TM_WINDOW = 120
# Number of connection autorized during the window
THRESHOLD = 20
# Global variable to store the data 
global df
df = pd.DataFrame(columns=['ip_adress', 'user_id', 'http_code', 'url', 'section', 'time']) 


class WriteRandomStuff(Thread):
    """ Thread that writes the time in a log,
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

class WriteApacheLog(Thread):
    """ Thread that simulates an apache log,
    used for testing. """

    def __init__(self, file_name, duration, time_interval=0.3):
        Thread.__init__(self)
        self.duration = duration
        self.file_name = file_name
        self.time_interval = time_interval

    def run(self):
        start_time = time.time()
        with open(self.file_name, 'w+') as f:
            while time.time() - start_time < self.duration:
                with lock:
                    string = '127.0.0.1 - adrien [{} -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326 "http://www.example.com/start.html" "Mozilla/4.08 [en] (Win98; I ;Nav)" \n'
                    time_now = dt.datetime.strftime(dt.datetime.now(),"%d/%b/%Y:%H:%M:%S")
                    f.write(string.format(time_now))
                    f.flush()
                time.sleep(self.time_interval)

class TailLogFile(Thread):
    """ Thread to keep track of the changes in the log file
    and update the dataframe containing the current data """

    def __init__(self, file_name, refresh_interval=0.1):
        Thread.__init__(self)
        self.file_name = file_name 
        # ecire quelque chose pour chemin absolu ou relatif
        self.refresh_interval = refresh_interval
        self.terminated = False

    def run(self): 
        with open(self.file_name, 'r') as file_:
                # Go to the end of file
                file_.seek(0,2)
                while not self.terminated:
                    curr_position = file_.tell()
                    with lock:
                        lines = file_.readlines()
                    if not lines:
                        file_.seek(curr_position)
                    else:
                        for l in lines:
                                add_to_df(l)
                    time.sleep(self.refresh_interval)

    def stop(self):
        self.terminated = True

def add_to_df(line):
    """ Add line to the dataframe """
    regex = r'([(\d\.)]+) ([^ ]+) ([^ ]+) \[(.*?)\] "(.*?)" (\d+|-) (\d+|-) (?:"(.*?)" "(.*?)")'
    match = re.match(regex, line)
    if match:
        parsed_line = match.groups()
    else:
        return log.error(line)
    # Format '10/Oct/2000:13:55:36 -0700'
    # The time zone is removed, we assume the log file and the computer have the same
    time = dt.datetime.strptime(parsed_line[3][:-6], "%d/%b/%Y:%H:%M:%S")
    items = [parsed_line[i] for i in [0, 2, 5, 7]]
    section = '/'.join(items[3].split('/')[:4])
    items.extend([section, time])
    with lock:
        df.loc[len(df)+1] = items
        df.replace('-', pd.np.nan, inplace=True)

class SendReport(Thread):
    """ Thread used to send a report every 10s """
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        while True:
            time_report = dt.datetime.now() - dt.timedelta(seconds=T_REPORT)

            with lock:
                to_report = df[df['time'] > time_report]

            if to_report.empty:
                log.info("Report for the last {}s: No connection were made".format(T_REPORT))

            else:
                max_section = to_report.groupby('section').count().idxmax()[0]
                nb_section_hits = to_report.groupby('section').count().max()[0]
                nb_users = to_report.groupby('ip_adress').size()[0]
                nb_connections = len(to_report)

                report_string = "Report for the last {}s :{} connections were made, from {} users, " + \
                "{} was the section with the most hits ({} hits)"
                log.info(report_string.format(T_REPORT, nb_connections, nb_users, max_section, nb_section_hits))
            time.sleep(T_REPORT)

class MonitorTraffic(Thread):
    """ Thread that send a warning if the traffic was above a certain
    value for more than 2 minutes. Send an other warning when the traffic
    gets back to normal """

    def __init__(self, threshold=THRESHOLD):
        Thread.__init__(self)
        self.on_alert = False
        self.threshold = threshold

    # To monitor the traffic on the last 2min we need to check the traffic regularly, 
    # here it's done every 10s. We could keep in memory the data for the last 2min and
    # calculate the new stats about the traffic every 10s, but using a queue with fixed
    # sized we can limit the memory usage

    def run(self):
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
                    alert = "Traffic back to normal, for the last two minutes " + \
                    "generated an alert - hits = {}, triggered at {}"
                    log.warning(alert.format(nb_hits, current_time))
                    self.on_alert = False
            else:
                if nb_hits > self.threshold:
                    alert = "High traffic for the last two minutes generated " + \
                    "an alert - hits = {}, triggered at {}"
                    log.warning(alert.format(nb_hits, current_time))
                    self.on_alert = True
            clean_df()
            time.sleep(T_REPORT)



class Queue(object):
    def __init__(self, queue_size):
        self.queue = []
        self.max_size = queue_size

    def push(self, element):
        self.queue = [element] + self.queue
        if len(self.queue) > self.max_size:
            self.queue.pop()

    def size(self):
        return sum(self.queue) 

def clean_df():
    """ Function to remove old data and to limit the memory usage """
    to_keep = dt.datetime.now() - dt.timedelta(seconds=2*T_REPORT)
    with lock:
        df.drop(df.index[df.time < to_keep], inplace=True)
        df.reset_index(inplace=True, drop=True)

def make_a_log_file(name, to_terminal = True, to_filename = True, terminal_level="INFO", file_level = "INFO"):
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
        fh = logging.FileHandler('http_monitoring.log', encoding='UTF-8')
        fh.setLevel(file_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    if to_terminal:

        found = False
        for index,h in enumerate(logger.handlers):
            if isinstance(h,logging.StreamHandler) and not isinstance(h,logging.FileHandler):
                found = True
                break

        if not found:
            ch = logging.StreamHandler()
            ch.setLevel(terminal_level)
            # create formatter and add it to the handlers
            ch.setFormatter(formatter)
            # add the handlers to the logger
            logger.addHandler(ch)

        else:
            ch = logger.handlers[index]
            ch.setFormatter(formatter)
            ch.setLevel(terminal_level)
    logger.propagate = False
    return logger

if __name__ == '__main__':
    from docopt import docopt

    args = docopt(__doc__, version='Http Monitoring 1.0')

    log = make_a_log_file('http_monitoring')

    write = WriteApacheLog('test.log', 100)
    write.start()

    tail = TailLogFile('test.log')
    tail.start()

    monitor = MonitorTraffic()
    monitor.start()

    report = SendReport()
    report.start()

    # args = docopt(__doc__, version='Http Monitoring 1.0')

    # log = make_a_log_file('http_monitoring')

    # write = WriteApacheLog('test.log', 100)
    # write.start()

    # tail = TailLogFile(args['log_file'])
    # tail.start()

    # monitor = MonitorTraffic()
    # monitor.start()

    # report = SendReport()
    # report.start()






