"""
This module contains general database queries.
"""
from playhouse.shortcuts import model_to_dict

from models import WarRequest, Connect, SendMessage, PortPostMessage


class Query:
	def __init__(self, database):
		self.db = database
		self._create_get_initiator_function()

	def query_for_known_extensions(self, table: str, known_ids: list) -> list:
		""" Search for known extension ids in table. Returns a list of dicts for each matching row."""
		if table == "connect":
			query = Connect.select().where(Connect.extension_id.in_(known_ids))
		elif table == "sendmessage":
			query = SendMessage.select().where(SendMessage.extension_id.in_(known_ids))
		elif table == "portpostmessage":
			query = PortPostMessage.select().where(PortPostMessage.extension_id.in_(known_ids))
		elif table == "warrequest":
			query = WarRequest.select().where(WarRequest.requested_extension_id.in_(known_ids))
		else:
			raise ValueError(f"Table name {table} is unknown.")
		return [model_to_dict(row) for row in query]

	def _query_extensions(self, query_string) -> dict:
		extensions_chrome = []
		extensions_firefox = []
		extensions_else = []

		# Get requested extension ids and number of requests, ordered by this number
		cursor = self.db.execute_sql(query_string)
		for requested_extension_id, request_count, request_count_clean in cursor.fetchall():
			extension = {
				"id": requested_extension_id,
				"request_count": request_count,
				"request_count_clean": request_count_clean
			}
			# Chrome extensions have an id with length 32
			if len(requested_extension_id) == 32:
				extensions_chrome.append(extension)
			elif len(requested_extension_id) == 36:
				extensions_firefox.append(extension)
			else:
				extensions_else.append(extension)
		return {
			"chrome": extensions_chrome,
			"firefox": extensions_firefox,
			"other": extensions_else
		}

	def _create_get_initiator_function(self):
		"""
		Create a Postgres Database function which extracts the initiating URL of a WAR request.
		First test if the documentURL refers to YouTube, then we can be sure that YT made the request.
		Otherwise try to extract it from the call stack or from the documentURL or form the initiator object.
		"""
		self.db.execute_sql("""
			CREATE OR REPLACE FUNCTION get_initiator(request_object jsonb) RETURNS text
			AS 
			$$ SELECT
			case
				when request_object->>'documentURL' ~* '^http(s)?://www.youtube(-nocookie).com' then request_object->>'documentURL'
				when request_object->'initiator'->'stack'->'callFrames'->0->>'url' ~* '^http(s)?://' then request_object->'initiator'->'stack'->'callFrames'->0->>'url'
				when request_object->>'documentURL' ~* '^http(s)?://' then request_object->>'documentURL'
				else request_object->'initiator'->>'url'
			end as initiator
			$$	
			LANGUAGE SQL
			IMMUTABLE
			RETURNS NULL ON NULL INPUT;
		""")
