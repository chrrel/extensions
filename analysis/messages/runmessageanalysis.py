import logging
from configparser import ConfigParser

from playhouse.postgres_ext import PostgresqlExtDatabase

import extensionstores
import utils
from messages.evaluationmessages import EvaluationMessages
from messages.querymessages import QueryMessages


def message_analysis(db: PostgresqlExtDatabase, config: ConfigParser, extensions_messages_data: list, known_extension_ids: list):
	query = QueryMessages(db)
	# Suspicious keywords to search in messages
	suspicious_keywords = ["ajax", "bookmarks", "browsing", "command", "cookie", "download", "exec", "history", "store", "{{{}}}", "headline-extension-clickable"]

	if config.getboolean("messages", "connect"):
		logging.info("[+] Querying connects")
		# Connects without target
		connects = utils.retrieve_data("results/messages/connect_without_target.json", lambda: query.query_connects_without_target())
		EvaluationMessages.analyse_connects_without_targets(connects)

		# Connects without targets - details on initiators
		connect_initiators = query.query_connects_without_target_initiators()
		EvaluationMessages.analyse_connects_without_targets_initiator_details(connect_initiators)

		# Connects with target
		def get_data():
			connects = query.query_connects_with_target()
			# Add infos about the target extensions
			for connect in connects:
				try:
					connect["extension"] = extensionstores.get_extension_info(connect["extension_id"])
				except extensionstores.GetExtensionInfoError:
					connect["extension"] = extensionstores._build_extension_info_dict(extension_id=connect["extension_id"], title="")
			return connects
		connects = utils.retrieve_data("results/messages/connect_with_target.json", get_data)
		EvaluationMessages.analyse_connects_with_targets(connects)

		# Connects to known extensions
		connects = utils.retrieve_data("results/messages/connect_known_extensions.json", lambda: query.query_for_known_extensions(table="connect", known_ids=known_extension_ids))
		print(f"Number of connects to known extensions: {len(connects)}\nList of these connects: {connects}")

		# Extensions connected to
		def get_data():
			extensions = query.query_connects_extensions()
			extensions["chrome"] = extensionstores.get_info_for_extensions(extensions["chrome"])
			return extensions
		extensions = utils.retrieve_data("results/messages/connect_extensions.json", get_data)
		print("Extensions contacted via runtime.connect:")
		EvaluationMessages.analyse_connect_extensions(extensions)

	if config.getboolean("messages", "sendmessage"):
		logging.info("[+] Querying sendmessages")
		# Sendmessage without target
		messages = utils.retrieve_data("results/messages/sendmessage_without_target.json", lambda: query.query_sendmessage_without_target())
		print(f"Number of sendmessages without targets: {len(messages)}")

		# Sendmessages with target
		messages = utils.retrieve_data("results/messages/sendmessage_with_target.json", lambda: query.query_sendmessage_with_target())
		print(f"Number of sendmessages with targets: {len(messages)}")
		EvaluationMessages.analyse_sendmessage_with_targets(messages)
		EvaluationMessages.analyse_sendmessage_websites(messages)

		# Uncomment the following line to get information from the extension's manifest.
		# This will download all extensions messages were found for!
		# EvaluationMessages.analyse_sendmessage_extensions_manifest(messages)

		# Sendmessages to known extensions
		messages = utils.retrieve_data("results/messages/sendmessage_known_extensions.json", lambda: query.query_for_known_extensions(table="sendmessage", known_ids=known_extension_ids))
		print(f"Number of sendmessages to known extensions: {len(messages)}.\nList of these messages: {messages}")

		# Sendmessages with known messages
		messages = utils.retrieve_data("results/messages/sendmessage_with_known_messages.json", lambda: query.query_messages_for_known_messages("sendmessage", extensions_messages_data))
		print(f"Number of sendmessages with known messages: {len(messages)}.\nList of these messages: {messages}")

		# Sendmessages containing suspicious keywords
		messages = utils.retrieve_data("results/messages/sendmessage_with_keywords.json", lambda: query.query_messages_for_keywords("sendmessage", suspicious_keywords))
		print(f"Sendmessages containing suspicious keywords: {messages}")

		# Extensions sendmessages are sent to
		def get_data():
			extensions = query.query_sendmessage_extensions()
			extensions["chrome"] = extensionstores.get_info_for_extensions(extensions["chrome"])
			return extensions
		sendmessage_extensions = utils.retrieve_data("results/messages/sendmessage_extensions.json", get_data)
		EvaluationMessages.analyse_sendmessage_extensions(sendmessage_extensions)

		# Sendmessages occurring frequently
		messages = utils.retrieve_data("results/messages/sendmessage_frequent.json", lambda: query.query_frequent_messages(table="sendmessage", min_count=3))
		print(f"Sendmessages occuring frequently \n {messages}")

	if config.getboolean("messages", "postmessage"):
		logging.info("[+] Querying postmessages")

		# Postmessages containing suspicious keywords
		messages = utils.retrieve_data("results/messages/postmessage_with_keywords.json", lambda: query.query_messages_for_keywords("postmessage", suspicious_keywords))
		print(f"Number of postmessages containing suspicious keywords: {len(messages)}")
		print(*messages, sep="\n")

		# Postmessages with known messages
		messages = utils.retrieve_data("results/messages/postmessage_with_known_messages.json", lambda: query.query_messages_for_known_messages("postmessage", extensions_messages_data))
		EvaluationMessages.analyse_postmessage_known_messages(messages, extensions_messages_data)

		# Postmessages occurring frequently
		messages = utils.retrieve_data("results/messages/postmessage_frequent.json", lambda: query.query_frequent_messages(table="postmessage", min_count=50))
		print(f"Postmessages occuring frequently \n {messages}")

	if config.getboolean("messages", "portpostmessage"):
		logging.info("[+] Querying portpostmessages")

		# All portpostmessages
		messages = query.query_portpostmessage()
		print(f"Number of all found portpostmessages: {len(messages)}")
		# No further analysis of port.postMessage() data since the complete dataset for this was empty
