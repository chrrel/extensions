import json
import requests

from exceptions import HealthCheckError


class HealthCheck:
	def __init__(self, api_url, api_key, check_name, enabled=False):
		self._api_url = api_url
		self._api_key = api_key
		self._enabled = enabled
		self._ping_url = self._create_check(check_name)

	def send_start_signal(self, data):
		self._send_signal("/start", data)

	def send_alive_signal(self, data):
		self._send_signal("", data)

	def send_failure_signal(self, data):
		self._send_signal("/fail", data)

	def _send_signal(self, path="", data=""):
		if self._enabled:
			requests.post(self._ping_url + path, data=str(data))

	def _create_check(self, check_name):
		if self._enabled:
			data = {
				"api_key": self._api_key,
				"name": check_name,
				"tags": "prod scanserver",
				"timeout": 1080,
				"grace": 900,
				"channels": "*",
				"unique": ["name"]
			}
			response = requests.post(self._api_url, data=json.dumps(data))
			if response.status_code not in [200, 201]:
				raise HealthCheckError(f"Cannot create healthcheck. Status: {response.status_code}. Response: {response.text}")
			else:
				response_text = json.loads(response.text)
				return response_text["ping_url"]
