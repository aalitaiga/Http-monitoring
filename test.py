import unittest
import os
from utils import (
	WriteRandomStuff, 
	TailLogFile,
	parse_line
)

# To do, update the test
# Write test to see how many connection per s the program can handle

class TestUtils(unittest.TestCase):

	def test_write_random_stuff(self):
		if os.path.isfile("test.log"):
			os.remove("test.log")
		write = WriteRandomStuff("test.log", 1)
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
		write = WriteRandomStuff("test.log", 1)
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
		pass

	def test_monitor_traffic(self):
		pass

	def test_queue(self):
		pass

	def test_parse_line(self):
		test_string1 = r'127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326\
		 "http://www.example.com/start.html" "Mozilla/4.08 [en] (Win98; I ;Nav)"'
		groups = parse_line(test_string1)
		self.assertEqual(len(groups), 9)

if __name__ == '__main__':
	unittest.main()