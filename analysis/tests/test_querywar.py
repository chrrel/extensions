import unittest

from tests.test_query import QueryTest
from war.querywar import QueryWar


class QueryWarTest(QueryTest):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		cls.query = QueryWar(cls.db)

	def test_query_war_schemes(self):
		by_schemes = self.query.query_war_schemes()
		expected = [
			{'scheme': '.*', 'requests': 9, 'websites': 3},
			{'scheme': 'chrome-extension', 'requests': 9, 'websites': 3},
			{'scheme': 'moz-extension', 'requests': 0, 'websites': 0},
			{'scheme': 'opera-extension', 'requests': 0, 'websites': 0},
			{'scheme': 'ms-browser-extension', 'requests': 0, 'websites': 0},
			{'scheme': 'chrome', 'requests': 0, 'websites': 0},
			{'scheme': 'chrome-extension (Chrome Media Router only)', 'requests': 6, 'websites': 3},
			{'scheme': 'chrome-extension (Chrome Media Router excluded)', 'requests': 3, 'websites': 3}
		]
		self.assertListEqual(expected, by_schemes)

	def test_query_war_requested_extensions(self):
		extensions = self.query.query_war_requested_extensions()
		expected_extensions = {
			'chrome': [
				{'id': 'pkedcjkdefgpdelpbcmbmeomcjbeemfm', 'request_count': 6, 'request_count_clean': 3},
				{'id': '0kedcjkdefgpdelpbcmbmeomcjbeemfm', 'request_count': 1, 'request_count_clean': 1},
				{'id': '1kedcjkdefgpdelpbcmbmeomcjbeemfm', 'request_count': 1, 'request_count_clean': 1},
				{'id': '2kedcjkdefgpdelpbcmbmeomcjbeemfm', 'request_count': 1, 'request_count_clean': 1}],
			'firefox': [], 'other': []
		}
		self.assertDictEqual(expected_extensions, extensions)

	def test_query_websites_with_war_requests(self):
		websites = self.query.query_websites_with_war_requests()
		expected_websites = [
			{'id': 1, 'url': 'http://website0.de', 'distinct_extensions_requested_count': 2, 'requested_wars_count': 3, 'requests': []},
			{'id': 2, 'url': 'http://website1.de', 'distinct_extensions_requested_count': 2, 'requested_wars_count': 3,  'requests': []},
			{'id': 3, 'url': 'http://website2.de', 'distinct_extensions_requested_count': 2, 'requested_wars_count': 3, 'requests': []}
		]
		self.assertListEqual(expected_websites, websites)

	def test_query_war_requests_for_website(self):
		requests = self.query.query_war_requests_for_website(1)
		expected_requests = [
			{'requested_extension_id': 'pkedcjkdefgpdelpbcmbmeomcjbeemfm', 'requested_war': 'chrome-extension://pkedcjkdefgpdelpbcmbmeomcjbeemfm/a.txt', 'initiator': 'https://youtube.com'},
			{'requested_extension_id': 'pkedcjkdefgpdelpbcmbmeomcjbeemfm', 'requested_war': 'chrome-extension://pkedcjkdefgpdelpbcmbmeomcjbeemfm/a.txt', 'initiator': 'https://youtube.com'},
			{'requested_extension_id': '0kedcjkdefgpdelpbcmbmeomcjbeemfm', 'requested_war': 'chrome-extension://0kedcjkdefgpdelpbcmbmeomcjbeemfm/a.txt', 'initiator': 'https://test.com/TSPD/08011'}]
		self.assertListEqual(expected_requests, requests)

	def test_query_war_requests_with_initiators(self):
		requests = self.query.query_war_requests_with_initiators()
		expected_requests = [
			{'extension_id': '0kedcjkdefgpdelpbcmbmeomcjbeemfm', 'website_id': 1, 'initiator': 'test.com'},
			{'extension_id': '1kedcjkdefgpdelpbcmbmeomcjbeemfm', 'website_id': 2, 'initiator': 'test.com'},
			{'extension_id': '2kedcjkdefgpdelpbcmbmeomcjbeemfm', 'website_id': 3, 'initiator': 'test.com'}
		]
		self.assertListEqual(expected_requests, requests)

	def test_query_war_extensions_requested_together(self):
		extensions = self.query.query_war_extensions_requested_together()
		expected_extensions = {
			1: ["0kedcjkdefgpdelpbcmbmeomcjbeemfm"],
			2: ["1kedcjkdefgpdelpbcmbmeomcjbeemfm"],
			3: ["2kedcjkdefgpdelpbcmbmeomcjbeemfm"]
		}
		self.assertDictEqual(expected_extensions, extensions)

	def test_query_war_request_3rd_party(self):
		websites = self.query.query_war_request_3rd_party()
		expected_websites = {
			'same_domain': set(),
			'other_domain': {'http://website1.de', 'http://website2.de', 'http://website0.de'},
			'youtube': {'http://website1.de', 'http://website2.de', 'http://website0.de'}
		}
		self.assertDictEqual(expected_websites, websites)

	def test_query_war_request_f5(self):
		result = self.query.query_war_request_f5()
		expected = {'request_count': 3, 'distinct_websites_count': 3, 'distinct_extensions_count': 3}
		self.assertDictEqual(expected, result)


if __name__ == "__main__":
	unittest.main()
