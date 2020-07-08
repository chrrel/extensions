import unittest

from filehandler import FileHandler


class FileHandlerTest(unittest.TestCase):
	def setUp(self):
		self.file_handler = FileHandler(scan_directory="/tmp/fileHandlerTests", print_to_file=True)
		self.test_file = "/tmp/fileHandlerTestsurls_test.csv"
		with open(self.test_file, "w") as testfile:
			testfile.write("a.de\nb.com\ndef.net\ngü.xyz\n")

	def test_get_urls_from_file_should_return_list_of_urls(self):
		expected_urls = ["http://a.de", "http://b.com", "http://def.net", "http://gü.xyz"]
		urls = self.file_handler.get_urls_from_file(input_file=self.test_file, start_line=1, limit=4)
		self.assertListEqual(expected_urls, urls)

	def test_get_urls_from_file_with_start_line_should_return_list_of_urls(self):
		expected_urls = ["http://b.com", "http://def.net"]
		urls = self.file_handler.get_urls_from_file(input_file=self.test_file, start_line=2, limit=2)
		self.assertListEqual(expected_urls, urls)


if __name__ == "__main__":
	unittest.main()
