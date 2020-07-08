import json
import logging
import re
from urllib.parse import urlparse


class EventHandler:
	def __init__(self):
		self._connects = []
		self._port_post_messages = []
		self._post_messages = []
		self._send_messages = []
		self._war_requests = []

	def war_request_handler(self, **kwargs):
		"""
		This handler saves WAR requests found in requestWillBeSent callbacks.
		"""
		logging.debug(f"war_request_logger {kwargs}")
		request_url = kwargs.get("request").get("url")
		scheme = urlparse(request_url).scheme
		if scheme in ["chrome-extension", "moz-extension", "opera-extension", "ms-browser-extension", "chrome"]:
			print("WARRequest", kwargs)
			self._war_requests.append(kwargs)

	def war_request_fetch_handler(self, **log_entry):
		"""
		WAR requests made using the fetch API do not appear as "normal" request objects. As they can be found in
		the browser log, this handler collect them there and create an request object having the same structure as
		objects from the requestWillBeSent callbacks.
		"""
		logging.debug(f"war_request_fetch_logger {log_entry}")
		log_entry = log_entry.get("entry")
		# text looks like this: "Fetch API cannot load chrome-extension://fetch. URL scheme must be "http" [...]"
		text = log_entry.get("text")

		schemes = [
			"Fetch API cannot load chrome-extension://",
			"Fetch API cannot load moz-extension://",
			"Fetch API cannot load opera-extension://",
			"Fetch API cannot load ms-browser-extension://",
			"Fetch API cannot load chrome://"
		]
		if any(scheme in text for scheme in schemes):
			requested_war_url = re.search("((chrome-extension|moz-extension|chrome)://.*)\. URL", text).group(1)
			request = {
				"requestId": "",
				"loaderId": "",
				"documentURL": log_entry.get("url"),
				"request": {
					"url": requested_war_url,
					"method": "",
					"headers": {},
					"mixedContentType": "",
					"initialPriority": "",
					"referrerPolicy": ""
				},
				"timestamp": log_entry.get("timestamp"),
				"wallTime": "",
				"initiator": {
					"type": "script",
					"stack": {
						"callFrames": log_entry.get("stackTrace").get("callFrames")
					}
				},
				"type": "Fetch",
				"frameId": "",
				"hasUserGesture": ""
			}
			print("WARRequestFetch", request)
			self._war_requests.append(request)

	def message_handler(self, **log_entry):
		"""
		Messages from the postMessage, sendMessage and connect/postMessage APIs are logged using the console API
		(via injected JS). This handler extracts these messages.
		"""
		logging.debug(f"message_logger {log_entry}")

		log_title = log_entry.get("args")[0].get("value")
		# Data from window.postMessage calls
		if log_title == "PostMessageObject":
			message = log_entry.get("args")[1].get("value")
			message = json.loads(message)
			message = self._replace_none_values(message)
			print("PostMessageEvent", message)
			self._post_messages.append(message)
		# Data from runtime.sendMessage calls
		elif log_title == "SendMessageObject":
			message = {
				"extensionId": log_entry.get("args")[1].get("value"),
				"data": json.loads(log_entry.get("args")[2].get("value")),
				"callFrames": log_entry.get("stackTrace").get("callFrames")
			}
			print("SendMessageEvent", message)
			self._send_messages.append(message)
		# Data from port.postMessage calls
		elif log_title == "PortPostMessageObject":
			message = {
				"extensionId": log_entry.get("args")[1].get("value"),
				"data": json.loads(log_entry.get("args")[2].get("value")),
				"callFrames": log_entry.get("stackTrace").get("callFrames")
			}
			print("PortPostMessageEvent", message)
			self._port_post_messages.append(message)
		# Data from runtime.connect attempts
		elif log_title == "ConnectObject":
			connect = {
				"extensionId": log_entry.get("args")[1].get("value"),
				"connectInfo": json.loads(log_entry.get("args")[2].get("value")),
				"callFrames": log_entry.get("stackTrace").get("callFrames")
			}
			print("ConnectEvent", connect)
			self._connects.append(connect)
		# Handle JS errors that occur when logging messages
		elif log_title == "Error":
			log_message = log_entry.get("args")[1].get("preview").get("properties")
			error = {
				"type": "jsError",
				"location": log_message[0].get("value"),
				"errorMessage": log_message[1].get("value")
			}
			logging.error(str(error))

	def get_connects(self):
		return self._connects

	def get_port_post_messages(self):
		return self._port_post_messages

	def get_post_messages(self):
		return self._post_messages

	def get_send_messages(self):
		return self._send_messages

	def get_war_requests(self):
		return self._war_requests

	def _replace_none_values(self, message):
		"""
		Replace values that are None since these would not be accepted by the database.
		"""
		if "data" not in message or message["data"] is None:
			message["data"] = ""
		if "origin" not in message or message["origin"] is None:
			message["origin"] = ""
		return message
