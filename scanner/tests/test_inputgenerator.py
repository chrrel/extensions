import unittest

from inputgeneration.inputgenerator import InputGenerator


class FileHandlerTest(unittest.TestCase):
	def setUp(self):
		self.all_urls = [f"{x:02}" for x in list(range(0, 36))]
		self.expected_groups = {
			0: ['00', '01', '02', '03', '04', '20', '21', '22', '23', '24'],
			1: ['05', '06', '07', '08', '09', '25', '26', '27', '28', '29'],
			2: ['10', '11', '12', '13', '14', '30', '31', '32', '33', '34'],
			3: ['15', '16', '17', '18', '19', '35']
		}

	def test_split_urls_into_groups_should_return_correct_dict(self):
		urls_grouped = InputGenerator._split_urls_into_groups(urls=self.all_urls, n=4, chunk_size=5)
		print(self.all_urls)
		print(urls_grouped)
		self.assertDictEqual(self.expected_groups, urls_grouped)


if __name__ == "__main__":
	unittest.main()
