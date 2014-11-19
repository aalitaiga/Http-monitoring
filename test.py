import unittest
import time
import os
import re
from http_monitoring import (
	TailLogFile,
	WriteApacheLog,
	MonitorTraffic,
	SendReport,
	Queue,
	make_a_log_file
)

# Write test to see how many connection/s the program can handle

class TestUtils(unittest.TestCase):

	def test_write_apache_log(self):
		if os.path.isfile("test.log"):
			os.remove("test.log")
		write = WriteApacheLog("test.log", 1)
		write.start()
		write.join()

		with open("test.log") as f:
			line = f.readline()
			self.assertIsNotNone(line)

	def test_tail_log_file(self):
		if os.path.isfile("test.log"):
			os.remove("test.log")
		if os.path.isfile("tail.log"):
			os.remove("tail.log")
		write = WriteApacheLog("test.log", 1)
		tail = TailLogFile("tail.log")
		write.start()
		tail.start()
		write.join()
		tail.stop()

		with open("tail.log", 'r') as tail, open("test.log", 'r') as test:
			tail_lines = tail.readlines()
			test_lines = test.readlines()

			for tail_line, test_line in zip(tail_lines, test_lines):
				self.assertEqual(tail_line, test_line)

	def test_send_report(self):
		""" Not working """
		write = WriteApacheLog('test.log', 5)
		write.start()
		tail = TailLogFile('test.log')
		tail.start()
		write.join()
		time.sleep(2)
		tail.stop()

		self.assertFalse(df.empty)

	def test_monitor_traffic(self):
		pass

	def test_add_to_df(self):
		pass

	def clean_df(self):
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


if __name__ == '__main__':
	unittest.main()