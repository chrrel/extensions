import unittest
from unittest.mock import patch

from exceptions import HealthCheckError
from utils.healthcheck import HealthCheck


class HealthCheckTest(unittest.TestCase):
	def setUp(self):
		with patch("requests.post") as mock_request:
			mock_request.return_value.status_code = 200
			mock_request.return_value.text = '{"ping_url": "https://hc-ping.com/a123b"}'

			self.healthcheck = HealthCheck(
				api_url="https://healthchecks.io/api/v1/checks/",
				api_key="...",
				check_name="test-host",
				enabled=True
			)

	def test_start_signal_should_do_request(self):
		with patch("requests.post") as mock_request:
			# set a status_code of mock object with value 200
			mock_request.return_value.status_code = 200

			expected_url = "https://hc-ping.com/a123b/start"
			expected_data = "hi"

			# Do request
			self.healthcheck.send_start_signal(data="hi")

			# test if requests.get was called with the given url or not
			mock_request.assert_called_once_with(expected_url, data=expected_data)

	def test_alive_signal_should_do_request(self):
		with patch("requests.post") as mock_request:
			# set a status_code of mock object with value 200
			mock_request.return_value.status_code = 200

			expected_url = "https://hc-ping.com/a123b"
			expected_data = "hi"

			# Do request
			self.healthcheck.send_alive_signal(data="hi")

			# test if requests.get was called with the given url or not
			mock_request.assert_called_once_with(expected_url, data=expected_data)

	def test_fail_signal_should_do_request(self):
		with patch("requests.post") as mock_request:
			# set a status_code of mock object with value 200
			mock_request.return_value.status_code = 200

			expected_url = "https://hc-ping.com/a123b/fail"
			expected_data = "hi"

			# Do request
			self.healthcheck.send_failure_signal(data="hi")

			# test if requests.get was called with the given url or not
			mock_request.assert_called_once_with(expected_url, data=expected_data)

	def test_alive_signal_should_not_do_request_if_disabled(self):
		with patch("requests.post") as mock_request:
			# set a status_code of mock object with value 200
			mock_request.return_value.status_code = 200

			# Do request on new healthcheck object since enabled should be set to False
			hc = HealthCheck(
				api_url="https://healthchecks.io/api/v1/checks/",
				api_key="...",
				check_name="test-host",
				enabled=False
			)
			hc.send_alive_signal(data="hi")

			# test that request is not made
			mock_request.assert_not_called()

	def test_create_check_should_raise_error_if_check_cannot_be_created(self):
		with self.assertRaises(HealthCheckError):
			with patch("requests.post") as mock_request:
				mock_request.return_value.status_code = 401
				HealthCheck(
					api_url="https://healthchecks.io/api/v1/checks/",
					api_key="...",
					check_name="test-host",
					enabled=True
				)


if __name__ == '__main__':
	unittest.main()
