import unittest
import unittest.mock as mock

import extensionstores


class ExtensionStoresTest(unittest.TestCase):
	def setUp(self):
		pass

	def test_get_extension_info_chrome(self):
		extension_id = "jnhgnonknehpejjnehehllkliplmbmhn"
		expected = {
			'title': 'Web Scraper',
			'description': 'Web site data extraction tool',
			'author': 'webscraper.io',
			'id': 'jnhgnonknehpejjnehehllkliplmbmhn',
			'category': 'Productivity',
			'user_count': mock.ANY,
			'browser': 'Chrome'
		}
		# The user count changes frequently so use mock.ANY which compares equal to everything
		extension_data = extensionstores.get_extension_info(extension_id)
		self.assertDictEqual(expected, extension_data)

	def test_get_extension_info_opera(self):
		extension_id = "cldfkgliklaggnopdgnepabenoiiopbi"
		expected = {
			'id': 'cldfkgliklaggnopdgnepabenoiiopbi',
			'title': 'PhotoTracker Lite',
			'description': mock.ANY,
			'author': 'phototracker',
			'category': 'Search',
			'user_count': mock.ANY,
			'browser': 'Opera'
		}
		extension_data = extensionstores.get_extension_info(extension_id)
		self.assertDictEqual(expected, extension_data)

	def test_get_extension_info_edge(self):
		extension_id = "odfafepnkmbhccpbejgmiehpchacaeak"
		expected = {
			'id': 'odfafepnkmbhccpbejgmiehpchacaeak',
			'title': 'uBlock Origin',
			'description': 'Finally, an efficient blocker. Easy on CPU and memory.',
			'author': 'Nik Rolls',
			'category': 'Productivity',
			'user_count': -1,
			'browser': 'Edge'
		}
		extension_data = extensionstores.get_extension_info(extension_id)
		self.assertDictEqual(expected, extension_data)

	def test_get_extension_info_unsupported(self):
		extension_id = "odfafepnkmbhccpbejgmiehpchacaeak"
		with self.assertRaises(extensionstores.GetExtensionInfoError):
			extensionstores.get_extension_info_from_store("firefox", extension_id)

	def test_clean_category_names(self):
		category = extensionstores._get_category_names(["1_communication"])
		expected_category = ["Social & Communication"]
		self.assertEqual(expected_category, category)

	def test_clean_category_names_not_found(self):
		category = extensionstores._get_category_names(["ThisTestFails"])
		expected_category = ["ThisTestFails"]
		self.assertEqual(expected_category, category)


if __name__ == "__main__":
	unittest.main()
