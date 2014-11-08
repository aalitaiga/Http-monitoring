import unittest
import os
from utils import WriteRandomStuff, TailLogFile


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






if __name__ == '__main__':
	unittest.main()