import unittest
import datetime as dt
import time
import os
import re
from http_monitoring import (
	TailLogFile, WriteApacheLog, MonitorTraffic,
	SendReport, Queue, df, add_to_df,
	T_REPORT, clean_df
)


class TestUtils(unittest.TestCase):

	def test_write_apache_log(self):
		if os.path.isfile("apache.log"):
			os.remove("apache.log")
		write = WriteApacheLog('apache.log', 0.5, 0.05)
		write.start()
		write.join()

		with open('apache.log', 'r') as f:
			line = f.readline()
			self.assertIsNotNone(line)
		os.remove("apache.log")

	def clean_df(self):
		clean_df(0)
		self.assertTrue(df.empty)

		string = '127.0.0.1 - adrien [{} -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326 "http://www.example.com/start.html" "Mozilla/4.08 [en] (Win98; I ;Nav)"'
		tme = dt.datetime.now()
		time_previous = (tme - dt.timedelta(seconds=3*T_REPORT)).strftime("%d/%b/%Y:%H:%M:%S")
		add_to_df(string.format(time_previous))
		clean_df()
		self.assertTrue(df[df.time < tme - dt.timedelta(seconds=2*T_REPORT)].empty)

	def test_add_to_df(self):
		string = '127.0.0.1 - adrien [{} -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326 "http://www.example.com/start.html" "Mozilla/4.08 [en] (Win98; I ;Nav)"'
		tme = dt.datetime.now()
		clean_df(0)
		add_to_df(string.format(tme.strftime("%d/%b/%Y:%H:%M:%S")))
		self.assertFalse(df.empty)

	def test_tail_log_file(self):
		if os.path.isfile("test.log"):
			os.remove("test.log")
		if os.path.isfile("http_monitoring.log"):
			os.remove("http_monitoring.log")
		clean_df(0)
		write = WriteApacheLog("test.log", 1)
		tail = TailLogFile("test.log")
		write.start()
		tail.start()
		write.join()
		time.sleep(0.1)
		tail.stop()

		with open("test.log", 'r') as test:
			test_lines = test.readlines()
			self.assertEqual(len(test_lines), len(df))
		os.remove("test.log")

	def test_send_report(self):
		pass

	def test_monitor_traffic(self):
		pass

	def test_queue(self):
		queue = Queue(3)
		queue.push(1)
		self.assertEqual(queue.size(), 1)
		for i in range(1, 5):
			queue.push(i)
		self.assertEqual(queue.size(), 9)

	def test_regex(self):
		regex = r'([(\d\.)]+) ([^ ]+) ([^ ]+) \[(.*?)\] "(.*?)" (\d+|-) (\d+|-) (?:"(.*?)" "(.*?)")'
		string = r'127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326 ' + \
		'"http://www.example.com/start.html" "Mozilla/4.08 [en] (Win98; I ;Nav)"'
		groups = re.match(regex, string).groups()
		self.assertEqual(len(groups), 9)

		string = r'168.23.35.12 adrien frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326 ' + \
		'"http://www.example.com/start.html" "Mozilla/4.08 [en] (Win98; I ;Nav)"'
		groups = re.match(regex, string).groups()
		self.assertEqual(len(groups), 9)

		string = r'192.24.0.16 - - [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326 ' + \
		'"http://www.example.com/start.html" "Mozilla/4.08 [en] (Win98; I ;Nav)"'
		groups = re.match(regex, string).groups()
		self.assertEqual(len(groups), 9)



if __name__ == '__main__':
	unittest.main()