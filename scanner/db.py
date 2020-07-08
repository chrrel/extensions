import time
from urllib.parse import urlparse

from peewee import OperationalError, DatabaseError
from playhouse.postgres_ext import PostgresqlExtDatabase

from models import Connect, Website, PortPostMessage, PostMessage, SendMessage, WarRequest, database_proxy


class DB:
	def __init__(self, host, port, database, user, password, enabled=False):
		self.enabled = enabled
		if not self.enabled:
			return
		try:
			self.database = PostgresqlExtDatabase(database, user=user, password=password, host=host, port=port)

			database_proxy.initialize(self.database)
			self.database.connect(reuse_if_open=True)
		except Exception as error:
			raise DatabaseError(f"Cannot connect to database: {error}")

		self._create_tables()

	def _create_tables(self):
		tries = 50
		# Try to create the needed tables multiple times as this can crash when multiple scanners perform this
		# operation at the same time. By default, peewee includes an IF NOT EXISTS.
		for i in range(tries):
			try:
				self.database.create_tables([Connect, Website, PortPostMessage, PostMessage, SendMessage, WarRequest])
			except OperationalError as error:
				if i < tries - 1:  # i is zero indexed
					time.sleep(2)
					continue
				else:
					raise DatabaseError(f"Cannot create table: {error}")

	def save_results(self, results):
		if not self.enabled:
			return
		try:
			with self.database.atomic():
				website = Website(url=results["url"], scan_time=results["scanTime"])

				post_messages = []
				for message in results["postMessages"]:
					post_messages.append({"website": website, "origin": message["origin"], "data": message["data"]})

				send_messages = []
				for message in results["sendMessages"]:
					send_messages.append({
						"website": website,
						"extension_id": message["extensionId"],
						"data": message["data"],
						"call_frames": message["callFrames"]
					})

				port_post_messages = []
				for message in results["portPostMessages"]:
					port_post_messages.append({
						"website": website,
						"extension_id": message["extensionId"],
						"data": message["data"],
						"call_frames": message["callFrames"]
					})

				connects = []
				for connect in results["connects"]:
					connects.append({
						"website": website,
						"extension_id": connect["extensionId"],
						"connect_info": connect["connectInfo"],
						"call_frames": connect["callFrames"]
					})

				war_requests = []
				for war_request in results["warRequests"]:
					requested_war = war_request["request"]["url"]
					war_requests.append({
						"website": website,
						"requested_war": requested_war,
						"requested_extension_id": urlparse(requested_war).netloc,
						"request_object": war_request
					})

				website.save()
				PostMessage.insert_many(post_messages).execute()
				SendMessage.insert_many(send_messages).execute()
				PortPostMessage.insert_many(port_post_messages).execute()
				Connect.insert_many(connects).execute()
				WarRequest.insert_many(war_requests).execute()
		except Exception as error:
			raise DatabaseError(f"Cannot save data for website {results['url']}: {error}")

	def close_connection(self):
		if self.enabled:
			self.database.close()
