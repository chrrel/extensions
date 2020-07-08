import unittest
import unittest.mock as mock

from messages.querymessages import QueryMessages
from tests.test_query import QueryTest


class QueryMessagesTest(QueryTest):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		cls.query = QueryMessages(cls.db)

	def test_query_messages_for_known_messages(self):
		known_extensions_messages_data = [{
			"browser": "chrome",
			"risk": "ajax",
			"extension": "angncidddapgcmohkdmhidfleomhmfgi",
			"via": "content_scripts",
			"messages": [
				[{"type": "exec"}],
				[{"from": "sender"}, "msg"]
			]
		}]
		post_messages = self.query.query_messages_for_known_messages("postmessage", known_extensions_messages_data)
		expected_messages = [
			{'website_id': 1, 'url': 'http://website0.de', 'data': {'type': 'exec'}, 'extension': 'angncidddapgcmohkdmhidfleomhmfgi'},
			{'website_id': 2, 'url': 'http://website1.de', 'data': {'type': 'exec'}, 'extension': 'angncidddapgcmohkdmhidfleomhmfgi'},
			{'website_id': 3, 'url': 'http://website2.de', 'data': {'type': 'exec'}, 'extension': 'angncidddapgcmohkdmhidfleomhmfgi'},
			{'website_id': 1, 'url': 'http://website0.de', 'data': {'msg': 'hi', 'from': 'sender'}, 'extension': 'angncidddapgcmohkdmhidfleomhmfgi'},
			{'website_id': 2, 'url': 'http://website1.de', 'data': {'msg': 'hi', 'from': 'sender'}, 'extension': 'angncidddapgcmohkdmhidfleomhmfgi'},
			{'website_id': 3, 'url': 'http://website2.de', 'data': {'msg': 'hi', 'from': 'sender'}, 'extension': 'angncidddapgcmohkdmhidfleomhmfgi'}
		]
		self.assertListEqual(expected_messages, post_messages)

	def test_query_messages_for_keyword(self):
		messages = self.query.query_messages_for_keyword("postmessage", "exec")
		expected_messages = [
			{'id': mock.ANY, 'website': 1, 'data': {'type': 'exec'}},
			{'id': mock.ANY, 'website': 2, 'data': {'type': 'exec'}},
			{'id': mock.ANY, 'website': 3, 'data': {'type': 'exec'}}
		]
		self.assertListEqual(expected_messages, messages)

	def test_query_messages_for_keywords(self):
		messages = self.query.query_messages_for_keywords("postmessage", ["exec", "asd"])
		expected_messages = [
			{'id': mock.ANY, 'website': 1, 'data': {'type': 'exec'}},
			{'id': mock.ANY, 'website': 2, 'data': {'type': 'exec'}},
			{'id': mock.ANY, 'website': 3, 'data': {'type': 'exec'}}
		]
		self.assertListEqual(expected_messages, messages)

	# ####
	# SendMessage
	# ####
	def test_query_sendmessage_extensions(self):
		extensions = self.query.query_sendmessage_extensions()
		expected_extensions = {
			'chrome': [
				{'id': 'uiddcjkdefgpdelpbcmbmeomcjbeeplo', 'request_count': 6, 'request_count_clean': 3},
				{'id': '0kedcjkdefgpdelpbcmbmeomcjbeemfm', 'request_count': 1, 'request_count_clean': 1},
				{'id': '1kedcjkdefgpdelpbcmbmeomcjbeemfm', 'request_count': 1, 'request_count_clean': 1},
				{'id': '2kedcjkdefgpdelpbcmbmeomcjbeemfm', 'request_count': 1, 'request_count_clean': 1}
			],
			'firefox': [], 'other': [{'id': '', 'request_count': 3, 'request_count_clean': 3}]}
		self.assertDictEqual(expected_extensions, extensions)

	def test_query_sendmessage_without_target(self):
		messages = self.query.query_sendmessage_without_target()
		expected_messages = [
			{'id': 4, 'website': {'id': 1, 'url': 'http://website0.de', 'scan_time': 120}, 'extension_id': '', 'data': {'msg': 'test'}, 'call_frames': []},
			{'id': 8, 'website': {'id': 2, 'url': 'http://website1.de', 'scan_time': 121}, 'extension_id': '', 'data': {'msg': 'test'}, 'call_frames': []},
			{'id': 12, 'website': {'id': 3, 'url': 'http://website2.de', 'scan_time': 122}, 'extension_id': '', 'data': {'msg': 'test'}, 'call_frames': []}
		]
		self.assertListEqual(expected_messages, messages)

	def test_query_sendmessage_with_target(self):
		messages = self.query.query_sendmessage_with_target()
		expected_messages = [
			{'id': 1, 'website': {'id': 1, 'url': 'http://website0.de', 'scan_time': 120}, 'extension_id': 'uiddcjkdefgpdelpbcmbmeomcjbeeplo', 'data': {'msg': 'test'}, 'call_frames': []},
			{'id': 2, 'website': {'id': 1, 'url': 'http://website0.de', 'scan_time': 120}, 'extension_id': 'uiddcjkdefgpdelpbcmbmeomcjbeeplo', 'data': {'msg': 'test'}, 'call_frames': []},
			{'id': 3, 'website': {'id': 1, 'url': 'http://website0.de', 'scan_time': 120}, 'extension_id': '0kedcjkdefgpdelpbcmbmeomcjbeemfm', 'data': {'msg': 'test'}, 'call_frames': []},
			{'id': 5, 'website': {'id': 2, 'url': 'http://website1.de', 'scan_time': 121}, 'extension_id': 'uiddcjkdefgpdelpbcmbmeomcjbeeplo', 'data': {'msg': 'test'}, 'call_frames': []},
			{'id': 6, 'website': {'id': 2, 'url': 'http://website1.de', 'scan_time': 121}, 'extension_id': 'uiddcjkdefgpdelpbcmbmeomcjbeeplo', 'data': {'msg': 'test'}, 'call_frames': []},
			{'id': 7, 'website': {'id': 2, 'url': 'http://website1.de', 'scan_time': 121}, 'extension_id': '1kedcjkdefgpdelpbcmbmeomcjbeemfm', 'data': {'msg': 'test'}, 'call_frames': []},
			{'id': 9, 'website': {'id': 3, 'url': 'http://website2.de', 'scan_time': 122}, 'extension_id': 'uiddcjkdefgpdelpbcmbmeomcjbeeplo', 'data': {'msg': 'test'}, 'call_frames': []},
			{'id': 10, 'website': {'id': 3, 'url': 'http://website2.de', 'scan_time': 122}, 'extension_id': 'uiddcjkdefgpdelpbcmbmeomcjbeeplo', 'data': {'msg': 'test'}, 'call_frames': []},
			{'id': 11, 'website': {'id': 3, 'url': 'http://website2.de', 'scan_time': 122}, 'extension_id': '2kedcjkdefgpdelpbcmbmeomcjbeemfm', 'data': {'msg': 'test'}, 'call_frames': []}]
		self.assertListEqual(expected_messages, messages)

	def test_query_connects_extensions(self):
		extensions = self.query.query_connects_extensions()
		expected_extensions = {
			'chrome': [
				{'id': 'aeddcjkdefgpdelpbcmbmeomcjbeemla', 'request_count': 6, 'request_count_clean': 3},
				{'id': '0kedcjkdefgpdelpbcmbmeomcjbeemfm', 'request_count': 1, 'request_count_clean': 1},
				{'id': '1kedcjkdefgpdelpbcmbmeomcjbeemfm', 'request_count': 1, 'request_count_clean': 1},
				{'id': '2kedcjkdefgpdelpbcmbmeomcjbeemfm', 'request_count': 1, 'request_count_clean': 1}],
			'firefox': [], 'other': [{'id': '', 'request_count': 3, 'request_count_clean': 3}]}
		self.assertDictEqual(expected_extensions, extensions)

	def test_query_connects_without_target(self):
		connects = self.query.query_connects_without_target()
		expected_connects = [
			{'id': mock.ANY, 'website': {'id': 1, 'url': 'http://website0.de', 'scan_time': 120}, 'extension_id': '',
			 'connect_info': {}, 'call_frames': [{'url': ''}, {'url': 'https://example.com/f.js', 'functionName': 'runtime.connect'}]},
			{'id': mock.ANY, 'website': {'id': 2, 'url': 'http://website1.de', 'scan_time': 121}, 'extension_id': '',
			 'connect_info': {}, 'call_frames': [{'url': ''}, {'url': 'https://example.com/f.js', 'functionName': 'runtime.connect'}]},
			{'id': mock.ANY, 'website': {'id': 3, 'url': 'http://website2.de', 'scan_time': 122}, 'extension_id': '',
			 'connect_info': {}, 'call_frames': [{'url': ''}, {'url': 'https://example.com/f.js', 'functionName': 'runtime.connect'}]}
		]
		self.assertListEqual(expected_connects, connects)

	def test_query_connects_without_target_initiators(self):
		connects_initiators = self.query.query_connects_without_target_initiators()
		expected_initiators = [
			{'url': 'http://website0.de', 'initiator': 'https://example.com/f.js'},
			{'url': 'http://website1.de', 'initiator': 'https://example.com/f.js'},
			{'url': 'http://website2.de', 'initiator': 'https://example.com/f.js'}
		]
		self.assertListEqual(expected_initiators, connects_initiators)

	def test_query_connects_with_target(self):
		connects = self.query.query_connects_with_target()
		expected_connects = [
			{'id': 1, 'website': {'id': 1, 'url': 'http://website0.de', 'scan_time': 120},
			 'extension_id': 'aeddcjkdefgpdelpbcmbmeomcjbeemla', 'connect_info': {}, 'call_frames': []},
			{'id': 2, 'website': {'id': 1, 'url': 'http://website0.de', 'scan_time': 120},
			 'extension_id': 'aeddcjkdefgpdelpbcmbmeomcjbeemla', 'connect_info': {}, 'call_frames': []},
			{'id': 3, 'website': {'id': 1, 'url': 'http://website0.de', 'scan_time': 120},
			 'extension_id': '0kedcjkdefgpdelpbcmbmeomcjbeemfm', 'connect_info': {}, 'call_frames': []},
			{'id': 5, 'website': {'id': 2, 'url': 'http://website1.de', 'scan_time': 121},
			 'extension_id': 'aeddcjkdefgpdelpbcmbmeomcjbeemla', 'connect_info': {}, 'call_frames': []},
			{'id': 6, 'website': {'id': 2, 'url': 'http://website1.de', 'scan_time': 121},
			 'extension_id': 'aeddcjkdefgpdelpbcmbmeomcjbeemla', 'connect_info': {}, 'call_frames': []},
			{'id': 7, 'website': {'id': 2, 'url': 'http://website1.de', 'scan_time': 121},
			 'extension_id': '1kedcjkdefgpdelpbcmbmeomcjbeemfm', 'connect_info': {}, 'call_frames': []},
			{'id': 9, 'website': {'id': 3, 'url': 'http://website2.de', 'scan_time': 122},
			 'extension_id': 'aeddcjkdefgpdelpbcmbmeomcjbeemla', 'connect_info': {}, 'call_frames': []},
			{'id': 10, 'website': {'id': 3, 'url': 'http://website2.de', 'scan_time': 122},
			 'extension_id': 'aeddcjkdefgpdelpbcmbmeomcjbeemla', 'connect_info': {}, 'call_frames': []},
			{'id': 11, 'website': {'id': 3, 'url': 'http://website2.de', 'scan_time': 122},
			 'extension_id': '2kedcjkdefgpdelpbcmbmeomcjbeemfm', 'connect_info': {}, 'call_frames': []}
		]
		self.assertListEqual(expected_connects, connects)

	def test_query_frequent_messages(self):
		messages = self.query.query_frequent_messages(table="sendmessage", min_count=3)
		expected_messages = [{'data': {'msg': 'test'}, 'count': 3}]
		self.assertListEqual(expected_messages, messages)

	def test_query_portpostmessage(self):
		messages = self.query.query_portpostmessage()
		expected_messages_count = 12
		self.assertEqual(expected_messages_count, len(messages))


if __name__ == "__main__":
	unittest.main()
