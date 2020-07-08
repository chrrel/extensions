import configparser
import unittest

from database import Database
from models import Website, WarRequest, Connect, PortPostMessage, PostMessage, SendMessage
from query import Query


class QueryTest(unittest.TestCase):
	db = None
	db_obj = None

	@classmethod
	def setUpClass(cls) -> None:
		# Read config file
		config = configparser.ConfigParser()
		config.read("../config.cfg")

		# Call the methods of the database context handler manually to allow a persistent connection set up in this method
		cls.db_obj = Database(ssh_address_or_host=config["database"]["ssh_address_or_host"], database="test", user=config["database"]["user"], password=config["database"]["password"])
		cls.db = cls.db_obj.__enter__()
		cls._generate_test_data()
		cls.query = Query(cls.db)

	@classmethod
	def tearDownClass(cls) -> None:
		cls.db.drop_tables([Connect, Website, PortPostMessage, PostMessage, SendMessage, WarRequest])
		cls.db.close()
		cls.db_obj.tunnel.stop()

	def test_query_for_known_extensions(self):
		extensions = self.query.query_for_known_extensions("connect", ["1kedcjkdefgpdelpbcmbmeomcjbeemfm"])
		expected_extensions = [{
			'id': 7, 'website': {'id': 2, 'url': 'http://website1.de', 'scan_time': 121},
			'extension_id': '1kedcjkdefgpdelpbcmbmeomcjbeemfm', 'connect_info': {}, 'call_frames': []
		}]
		self.assertListEqual(expected_extensions, extensions)

	@classmethod
	def _generate_test_data(cls):
		cls.db.create_tables([Connect, Website, PortPostMessage, PostMessage, SendMessage, WarRequest])

		for i in range(3):
			website = Website(url=f"http://website{i}.de", scan_time=120 + i)
			# Append 3 WAR requests per website: one is requested 2x by every website, one is distinct
			# for every extension and requested 1x per website
			war_requests = []
			war1 = {
				"website": website,
				"requested_war": "chrome-extension://pkedcjkdefgpdelpbcmbmeomcjbeemfm/a.txt",
				"requested_extension_id": "pkedcjkdefgpdelpbcmbmeomcjbeemfm",
				'request_object': {
					'documentURL': 'https://youtube.com',
				}
			}
			war2 = {
				"website": website,
				"requested_war": f"chrome-extension://{i}kedcjkdefgpdelpbcmbmeomcjbeemfm/a.txt",
				"requested_extension_id": f"{i}kedcjkdefgpdelpbcmbmeomcjbeemfm",
				'request_object': {
					'documentURL': 'https://test.com',
					'initiator': {'stack': {'callFrames': [{'url': 'https://test.com/TSPD/08011'}]}},
				}
			}
			war_requests.append(war1)
			war_requests.append(war1)
			war_requests.append(war2)

			website.save()
			WarRequest.insert_many(war_requests).execute()

			# Add connect attempts for website (same method as above)
			connects = []
			connect1 = {
				"website": website,
				"extension_id": "aeddcjkdefgpdelpbcmbmeomcjbeemla",
				"connect_info": {},
				"call_frames": []
			}
			connect2 = {
				"website": website,
				"extension_id": f"{i}kedcjkdefgpdelpbcmbmeomcjbeemfm",
				"connect_info": {},
				"call_frames": []
			}
			connect3 = {
				"website": website,
				"extension_id": f"",
				"connect_info": {},
				"call_frames": [{"url": ""}, {"url": "https://example.com/f.js", "functionName": "runtime.connect"}]
			}
			connects.append(connect1)
			connects.append(connect1)
			connects.append(connect2)
			connects.append(connect3)
			Connect.insert_many(connects).execute()

			# Add postmessages
			postmessages = [
				{
					"website": website,
					"origin": "https://www.test.org",
					"data": {"type": "exec"}
				},
				{
					"website": website,
					"origin": "https://www.test.org",
					"data": {"msg": "hi", "from": "sender"}
				},
				{
					"website": website,
					"origin": "https://www.test.org",
					"data": {"hi": 2}
				}
			]
			PostMessage.insert_many(postmessages).execute()

			# Add portpostmessages and SendMessages - both have the same format so use the same data
			messages = [
				{
					"website": website,
					"extension_id": "uiddcjkdefgpdelpbcmbmeomcjbeeplo",
					"data": {"msg": "test"},
					"call_frames": []
				},
				{
					"website": website,
					"extension_id": "uiddcjkdefgpdelpbcmbmeomcjbeeplo",
					"data": {"msg": "test"},
					"call_frames": []
				},
				{
					"website": website,
					"extension_id": f"{i}kedcjkdefgpdelpbcmbmeomcjbeemfm",
					"data": {"msg": "test"},
					"call_frames": []
				},
				{
					"website": website,
					"extension_id": "",
					"data": {"msg": "test"},
					"call_frames": []
				}
			]
			PortPostMessage.insert_many(messages).execute()
			SendMessage.insert_many(messages).execute()


if __name__ == "__main__":
	unittest.main()
