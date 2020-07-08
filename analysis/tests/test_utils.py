import unittest

import utils


class UtilsTest(unittest.TestCase):
	def test_build_query_strings_from_message_data(self):
		data = [
			{
				"browser": "chrome",
				"risk": "storage",
				"extension": "my-test-extension",
				"via": "content_scripts",
				"messages": [
					[{"type": "message"}, "id", "key", "value", {"a": 1}],
					["id", "key", "value"],
					[{"type": True}]
				]
			},
			{
				"browser": "chrome",
				"risk": "storage",
				"extension": "my-test-extension2",
				"messages": []
			}
		]

		extensions = utils.build_query_strings_from_message_data(extensions=data, table_name="postmessage")
		expected = [
			'SELECT website_id, url, data FROM postmessage, website WHERE website_id=website.id and data @> \'{"type": "message"}\' and data @> \'{"a": 1}\' and data ?& array[\'id\', \'key\', \'value\'] ;',
			"SELECT website_id, url, data FROM postmessage, website WHERE website_id=website.id and data ?& array['id', 'key', 'value'] ;",
			'SELECT website_id, url, data FROM postmessage, website WHERE website_id=website.id and data @> \'{"type": true}\' ;'
		]
		self.assertListEqual(expected, extensions[0]["query_strings"])


if __name__ == "__main__":
	unittest.main()
