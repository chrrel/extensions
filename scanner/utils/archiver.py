import logging
import requests

from exceptions import ArchiverError


class Archiver:
	def __init__(self, enabled=False):
		self.enabled = enabled

	def _archive_url(self, url):
		"""Send URL to Internet Archive (https://web.archive.org)"""
		if self.enabled:
			try:
				res = requests.get(f"https://web.archive.org/save/{url}", headers={"user-agent": "extension-scanner"})
				if res.status_code == 200:
					archive_link = "https://web.archive.org" + res.headers["Content-Location"]
					logging.info(f"Archived website to: {archive_link}")
				else:
					raise ArchiverError(f"Cannot archive {url}. Status code was {res.status_code}")
			except Exception as e:
				logging.error(f"Error while trying to archive {url}: {e}", exc_info=True)
				pass

	def archive_website_if_suspicious(self, results):
		"""Send URL to archive if it contains requests to more than 2 WARs"""
		if len(results["warRequests"]) > 2:
			self._archive_url(results["url"])
