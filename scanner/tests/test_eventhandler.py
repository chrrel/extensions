import unittest

from eventhandler import EventHandler


class EventHandlerTest(unittest.TestCase):
	def setUp(self):
		self.eh = EventHandler()

	def test_handler_should_not_detect_war_request(self):
		request = {"request": {"url": "http://localhost:8000", "method": "GET"}}
		self.eh.war_request_handler(**request)
		war_requests_count = len(self.eh.get_war_requests())
		self.assertEqual(0, war_requests_count, "Number of found WAR requests should be 0")

	def test_handler_should_detect_war_request(self):
		request1 = {"request": {"url": "chrome-extension://aadghinnclilhikdhkfjggfmjjpkhbop/logo.png", "method": "GET"}}
		request2 = {"request": {"url": "moz-extension://aadghinnclilhikdhkfjggfmjjpkhbop/logo.png", "method": "GET"}}
		request3 = {"request": {"url": "chrome://aadghinnclilhikdhkfjggfmjjpkhbop/logo.png", "method": "GET"}}

		self.eh.war_request_handler(**request1)
		self.eh.war_request_handler(**request2)
		self.eh.war_request_handler(**request3)

		war_requests_count = len(self.eh.get_war_requests())
		self.assertEqual(3, war_requests_count,  "Number of found WAR requests should be 3")

	def test_handler_should_detect_war_request_fetch(self):
		log_entry1 = {
			'entry': {
				'text': 'Fetch API cannot load chrome-extension://fetch. URL scheme must be "http" or "https" for CORS request.',
				'timestamp': 1575299676251.366,
				'url': 'http://localhost:8000/',
				'lineNumber': 94,
				'stackTrace': {
					'callFrames': [{'functionName': 'a', 'scriptId': '1', 'url': 'http://a.de/', 'lineNumber': 1, 'columnNumber': 1}]
				}
			}
		}
		log_entry2 = {
			'entry': {
				'text': 'Fetch API cannot load moz-extension://fetch. URL scheme must be "http" or "https" for CORS request.',
				'timestamp': 1575299676251.366,
				'url': 'http://localhost:8000/',
				'lineNumber': 94,
				'stackTrace': {
					'callFrames': [{'functionName': 'a', 'scriptId': '1', 'url': 'http://a.de/', 'lineNumber': 1, 'columnNumber': 1}]
				}
			}
		}
		log_entry3 = {
			'entry': {
				'text': 'Fetch API cannot load chrome://fetch. URL scheme must be "http" or "https" for CORS request.',
				'timestamp': 1575299676251.366,
				'url': 'http://localhost:8000/',
				'lineNumber': 94,
				'stackTrace': {
					'callFrames': [{'functionName': 'a', 'scriptId': '1', 'url': 'http://a.de/', 'lineNumber': 1, 'columnNumber': 1}]
				}
			}
		}
		self.eh.war_request_fetch_handler(**log_entry1)
		self.eh.war_request_fetch_handler(**log_entry2)
		self.eh.war_request_fetch_handler(**log_entry3)

		war_requests_count = len(self.eh.get_war_requests())
		self.assertEqual(3, war_requests_count,  "Number of found WAR requests (Fetch) should be 3")

	def test_handler_should_not_detect_war_request_fetch(self):
		log_entry = {'entry': {'source': 'network', 'level': 'error', 'text': 'Failed to load resource: net::ERR_UNKNOWN_URL_SCHEME', 'timestamp': 1575301194388.0679, 'url': 'chrome-extension://script', 'networkRequestId': '10127.3'}}
		self.eh.war_request_fetch_handler(**log_entry)

		war_requests_count = len(self.eh.get_war_requests())
		self.assertEqual(0, war_requests_count, "Number of found WAR requests (Fetch) should be 0")

	def test_handler_should_detect_post_message(self):
		log_entry = {'type': 'log', 'args': [{'type': 'string', 'value': 'PostMessageObject'}, {'type': 'string', 'value': '{"data":{"Action":"GETCOOKIE","action":"GETCOOKIE"},"origin":"http://localhost:8000"}'}], 'executionContextId': 2, 'timestamp': 1575302207634.243, 'stackTrace': {'callFrames': [{'functionName': '', 'scriptId': '11', 'url': '', 'lineNumber': 16, 'columnNumber': 11}]}}
		self.eh.message_handler(**log_entry)

		post_messages_count = len(self.eh.get_post_messages())
		self.assertEqual(1, post_messages_count, "Number of found PostMessages should be 1")

	def test_handler_should_not_detect_post_message(self):
		log_entry = {'type': 'log', 'args': [{'type': 'string', 'value': 'Hello from the other side.'}], 'executionContextId': 2, 'timestamp': 1575302207595.895, 'stackTrace': {'callFrames': [{'functionName': '', 'scriptId': '12', 'url': 'http://localhost:8000/', 'lineNumber': 96, 'columnNumber': 29}]}}

		self.eh.message_handler(**log_entry)

		post_messages_count = len(self.eh.get_post_messages())
		self.assertEqual(0, post_messages_count, "Number of found PostMessages should be 0")

	def test_handler_should_detect_send_message(self):
		log_entry = {'type': 'log', 'args': [{'type': 'string', 'value': 'SendMessageObject'}, {'type': 'string', 'value': 'jpchabeoojaflbaajmjhfcfiknckabpo'}, {'type': 'string', 'value': '{"type":"get-bookmarks"}'}], 'executionContextId': 2, 'timestamp': 1580744177143.306, 'stackTrace': {'callFrames': [{'functionName': 'chrome.runtime.sendMessage', 'scriptId': '3', 'url': '', 'lineNumber': 13, 'columnNumber': 11}, {'functionName': 'sendMessage', 'scriptId': '4', 'url': 'http://localhost:8000/', 'lineNumber': 121, 'columnNumber': 18}, {'functionName': '', 'scriptId': '4', 'url': 'http://localhost:8000/', 'lineNumber': 131, 'columnNumber': 2}]}}
		self.eh.message_handler(**log_entry)

		send_messages_count = len(self.eh.get_send_messages())
		self.assertEqual(1, send_messages_count, "Number of found SendMessages should be 1")

	def test_handler_should_not_detect_send_message(self):
		log_entry = {'type': 'log', 'args': [{'type': 'string', 'value': 'Hello from the other side.'}], 'executionContextId': 2, 'timestamp': 1575302207595.895, 'stackTrace': {'callFrames': [{'functionName': '', 'scriptId': '12', 'url': 'http://localhost:8000/', 'lineNumber': 96, 'columnNumber': 29}]}}
		self.eh.message_handler(**log_entry)

		send_messages_count = len(self.eh.get_send_messages())
		self.assertEqual(0, send_messages_count, "Number of found SendMessages should be 0")

	def test_handler_should_detect_port_post_message(self):
		log_entry = {'type': 'log', 'args': [{'type': 'string', 'value': 'PortPostMessageObject'}, {'type': 'string', 'value': 'jpchabeoojaflbaajmjhfcfiknckabpo'}, {'type': 'string', 'value': '{"joke":"Knock knock"}'}], 'executionContextId': 2, 'timestamp': 1580930038236.622, 'stackTrace': {'callFrames': [{'functionName': 'postMessage', 'scriptId': '3', 'url': '', 'lineNumber': 56, 'columnNumber': 14}, {'functionName': 'portPostMessage', 'scriptId': '4', 'url': 'http://aaaaaext1-test.de:8000/', 'lineNumber': 126, 'columnNumber': 8}, {'functionName': '', 'scriptId': '4', 'url': 'http://aaaaaext1-test.de:8000/', 'lineNumber': 137, 'columnNumber': 2}]}}
		self.eh.message_handler(**log_entry)

		port_post_messages_count = len(self.eh.get_port_post_messages())
		self.assertEqual(1, port_post_messages_count, "Number of found PortPostMessages should be 1")

	def test_handler_should_not_detect_port_post_message(self):
		log_entry = {'type': 'log', 'args': [{'type': 'string', 'value': 'Hello from the other side.'}], 'executionContextId': 2, 'timestamp': 1575302207595.895, 'stackTrace': {'callFrames': [{'functionName': '', 'scriptId': '12', 'url': 'http://localhost:8000/', 'lineNumber': 96, 'columnNumber': 29}]}}
		self.eh.message_handler(**log_entry)

		port_post_messages_count = len(self.eh.get_port_post_messages())
		self.assertEqual(0, port_post_messages_count, "Number of found PortPostMessages should be 0")

	def test_handler_should_detect_connect(self):
		log_entry = {'type': 'log', 'args': [{'type': 'string', 'value': 'ConnectObject'}, {'type': 'string', 'value': 'jpchabeoojaflbaajmjhfcfiknckabpo'}, {'type': 'string', 'value': '{"name":"knockknock"}'}], 'executionContextId': 2, 'timestamp': 1580930883776.823, 'stackTrace': {'callFrames': [{'functionName': 'runtime.connect', 'scriptId': '3', 'url': '', 'lineNumber': 46, 'columnNumber': 11}, {'functionName': 'portPostMessage', 'scriptId': '4', 'url': 'http://aaaaaext1-test.de:8000/', 'lineNumber': 125, 'columnNumber': 29}, {'functionName': '', 'scriptId': '4', 'url': 'http://aaaaaext1-test.de:8000/', 'lineNumber': 137, 'columnNumber': 2}]}}
		self.eh.message_handler(**log_entry)

		connect_count = len(self.eh.get_connects())
		self.assertEqual(1, connect_count, "Number of found Connencts should be 1")

	def test_handler_should_not_detect_connect(self):
		log_entry = {'type': 'log', 'args': [{'type': 'string', 'value': 'Hello from the other side.'}], 'executionContextId': 2, 'timestamp': 1575302207595.895, 'stackTrace': {'callFrames': [{'functionName': '', 'scriptId': '12', 'url': 'http://localhost:8000/', 'lineNumber': 96, 'columnNumber': 29}]}}
		self.eh.message_handler(**log_entry)

		connect_count = len(self.eh.get_connects())
		self.assertEqual(0, connect_count, "Number of found Connencts should be 0")


if __name__ == '__main__':
	unittest.main()
