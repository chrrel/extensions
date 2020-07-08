from playhouse.shortcuts import model_to_dict

from models import Connect, SendMessage, PortPostMessage
import utils
from query import Query


class QueryMessages(Query):
	def query_messages_for_known_messages(self, table_name: str, known_extensions_messages: list) -> list:
		""" Search for known messages in the given table.

		:param table_name: The database table to search in.
		:param known_extensions_messages: Every sublist in 'messages' represents one message. It is possible to search
		for a combination of keys or a combination of key-value-pairs or both.
		e.g.
		[{
			"browser": "chrome", "risk": "ajax", "extension": "angncidddapgcmohkdmhidfleomhmfgi", "via": "content_scripts",
			"messages": [["test", "url"], [{"type": "abc"}, "param"]]
		}]
		:return:
		"""
		extensions = utils.build_query_strings_from_message_data(extensions=known_extensions_messages, table_name=table_name)
		found_messages = []
		for extension in extensions:
			for query_string in extension["query_strings"]:
				cursor = self.db.execute_sql(query_string)
				for website_id, url, data in cursor.fetchall():
					found_messages.append({
						"website_id": website_id,
						"url": url,
						"data": data,
						"extension": extension["extension"]
					})
		return found_messages

	def query_messages_for_keyword(self, table: str, keyword: str) -> list:
		""" Get all messages containing the given keyword (case insensitive).

		:param table: Name of the database table to query
		:param keyword: String to search for
		:return: A list of dicts containing messages
		"""
		# Use two % to prevent errors: https://github.com/coleifer/peewee/issues/1924
		query_string = f"SELECT id, website_id, data FROM {table} WHERE LOWER(CAST(data AS text)) LIKE LOWER('%%{keyword}%%');"
		cursor = self.db.execute_sql(query_string)
		messages = []
		for message_id, website_id, data in cursor.fetchall():
			messages.append({
				"id": message_id,
				"website": website_id,
				"data": data
			})
		return messages

	def query_messages_for_keywords(self, table: str, keywords: list) -> list:
		""" Get all messages containing one of the given keywords (case insensitive).

		:param table: Name of the database table to query
		:param keywords: List of keywords to search for
		:return: A list of dicts containing messages
		"""
		all_messages = []
		for keyword in keywords:
			messages = self.query_messages_for_keyword(table, keyword)
			all_messages = all_messages + messages
		return all_messages

	def query_frequent_messages(self, table: str, min_count: int) -> list:
		"""
		Get messages that appeared frequently. If a website send the same message multiple times this only counts as 1 time.

		:param table: The name of the table to search in (postmessage or sendmessage or portpostmessage)
		:param min_count: The minimum number of occurrences a message needs to have
		:return:
		"""
		if table not in ["postmessage", "sendmessage", "portpostmessage"]:
			raise ValueError(f"Table name {table} is unknown.")

		query_string = f"SELECT data, COUNT(DISTINCT (website_id || CAST(data AS text))) AS count FROM {table} GROUP BY data HAVING COUNT(DISTINCT (website_id || CAST(data AS text))) >= %s ORDER BY count DESC;"
		cursor = self.db.execute_sql(query_string, (min_count,))
		return [{"data": data, "count": count} for data, count in cursor.fetchall()]

	def query_connects_extensions(self) -> dict:
		"""Get the extension ids contacted via connect ordered by number of requests.
		If a websites requests the same extension multiple times, this is only counted once in connect_count_clean.
		"""
		query = "SELECT extension_id, COUNT(extension_id) AS connect_count, COUNT(DISTINCT (extension_id || website_id)) as connect_count_clean FROM connect GROUP BY extension_id ORDER BY connect_count_clean DESC;"
		return self._query_extensions(query)

	def query_connects_without_target(self) -> list:
		""" Get connect attempts where the extension to connect to was not specified.
		"""
		query = Connect.select().where(Connect.extension_id == "")
		connects = [model_to_dict(connect) for connect in query]
		return connects

	def query_connects_without_target_initiators(self) -> list:
		"""Get a list of connects containing the visited URL and the complete URL of the connect initiator."""
		query_string = """
		SELECT 
			url, 
			case
				when call_frames->0->>'url' != '' then call_frames->0->>'url' 
				else call_frames->1->>'url'
			end as initiator
		FROM
			connect, website
		WHERE
			connect.website_id = website.id AND
			extension_id='';
		"""
		cursor = self.db.execute_sql(query_string)
		return [{"url": url, "initiator": initiator} for url, initiator in cursor.fetchall()]

	def query_connects_with_target(self) -> list:
		""" Get connect attempts where the extension to connect to was specified.
		"""
		query = Connect.select().where(Connect.extension_id != "")
		connects = [model_to_dict(connect) for connect in query]
		return connects

	def query_sendmessage_extensions(self):
		"""Get the extensions contacted via sendMessage ordered by number of requests.
		If a websites requests the same extension multiple times, this is only counted once in count_clean.
		"""
		query = "SELECT extension_id, COUNT(extension_id) AS count, COUNT(DISTINCT (extension_id || website_id)) as count_clean FROM sendmessage GROUP BY extension_id ORDER BY count_clean DESC;"
		return self._query_extensions(query)

	def query_sendmessage_without_target(self) -> list:
		""" Get sendmessages where the extension to send to was not specified.
		"""
		query = SendMessage.select().where(SendMessage.extension_id == "")
		messages = [model_to_dict(message) for message in query]
		return messages

	def query_sendmessage_with_target(self) -> list:
		""" Get sendmessages where the extension to send to was specified.
		"""
		query = SendMessage.select().where(SendMessage.extension_id != "")
		messages = [model_to_dict(message) for message in query]
		return messages

	def query_portpostmessage(self) -> list:
		""" Get all messages sent using port.postMessage"""
		query = PortPostMessage.select()
		return [model_to_dict(row) for row in query]
