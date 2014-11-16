import unittest
import time
import os
import pandas as pd
from http_monitoring import (
	WriteRandomStuff, 
	TailLogFile,
	WriteApacheLog,
	MonitorTraffic,
	SendReport,
	parse_log,
	Queue,
	make_a_log_file
)

# Write test to see how many connection/s the program can handle

class TestUtils(unittest.TestCase):

	# def test_write_random_stuff(self):
	# 	if os.path.isfile("test.log"):
	# 		os.remove("test.log")
	# 	write = WriteRandomStuff("test.log", 1)
	# 	write.start()
	# 	write.join()

	# 	with open("test.log") as f:
	# 		line = f.readline()
	# 		self.assertIsNotNone(line)

	# def test_tail_log_file(self):
	# 	if os.path.isfile("test.log"):
	# 		os.remove("test.log")
	# 	if os.path.isfile("tail.log"):
	# 		os.remove("tail.log")
	# 	write = WriteRandomStuff("test.log", 1)
	# 	tail = TailLogFile("tail.log")
	# 	write.start()
	# 	tail.start()
	# 	write.join()
	# 	tail.stop()

	# 	with open("tail.log", 'r') as tail, open("test.log", 'r') as test:
	# 		tail_lines = tail.readlines()
	# 		test_lines = test.readlines()

	# 		for tail_line, test_line in zip(tail_lines, test_lines):
	# 			self.assertEqual(tail_line, test_line)

	# def test_write_apache_log(self):
	# 	if os.path.isfile("apache.txt"):
	# 		os.remove("apache.txt")
	# 	write = WriteApacheLog('apache.txt', 2)
	# 	write.start()
	# 	write.join()

	# 	with open('apache.txt', 'r') as f:
	# 		line = f.readline()
	# 		self.assertIsNotNone(line)

	def test_send_report(self):
		global df
		df = pd.DataFrame(columns=['ip_adress', 'user_id', 'http_code', 'url', 'section'])
		df.index.name = 'time'

		write = WriteApacheLog('test.log', 5)
		write.start()
		tail = TailLogFile('test.log')
		tail.start()
		time.sleep(5)
		write.join()
		tail.stop()

		self.assertFalse(df.empty)
		print df


	def test_monitor_traffic(self):
		pass

	def test_queue(self):
		queue = Queue(3)
		queue.push(1)
		self.assertEqual(queue.size(), 1)
		for i in range(1, 5):
			queue.push(i)
		self.assertEqual(queue.size(), 9)

	def test_parse_line(self):
		test_string1 = r'127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326 ' + \
		'"http://www.example.com/start.html" "Mozilla/4.08 [en] (Win98; I ;Nav)"'
		groups = parse_log(test_string1)
		self.assertEqual(len(groups), 9)


if __name__ == '__main__':
	unittest.main()