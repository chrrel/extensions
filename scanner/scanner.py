import logging

from peewee import DatabaseError
from pychrome import PyChromeException
from pychrome import TimeoutException

from db import DB
from filehandler import FileHandler
from pageevaluator import PageEvaluator
from utils.archiver import Archiver
from chromium import ChromeBrowser


class Scanner:
	def __init__(self, config, healthcheck, scan_id, hostname):
		self.file_handler = FileHandler(
			scan_directory=config["output"]["output_directory"] + scan_id + "/",
			print_to_file=config.getboolean("output", "print_results_to_file")
		)
		self.db = DB(
			host=config["database"]["host"],
			port=config.getint("database", "port"),
			database=config["database"]["database_name"],
			user=config["database"]["user"],
			password=config["database"]["password"],
			enabled=config.getboolean("database", "enabled")
		)
		self.pageEvaluator = PageEvaluator(
			timeout=config.getint("scanner", "page_timeout"),
			tab_wait_time=config.getint("scanner", "tab_wait_time")
		)
		self.archiver = Archiver(
			enabled=config.getboolean("archiver", "enabled")
		)
		self.healthcheck = healthcheck

		self.debugging_port = config.getint("chromium", "debugging_port")
		self.chromium_executable = config["chromium"]["chromium_executable"]
		self.chromium_log_file = f"{config['output']['output_directory']}chromium-err-{scan_id}-{hostname}.log"

	def run_scan(self, urls):
		errors_count = 0
		browser = None
		for i, url in enumerate(urls):
			try:
				# Restart browser regularly
				if i % 1000 == 0:
					if browser is not None:
						browser.stop()
					browser = ChromeBrowser(
						log_file_path=self.chromium_log_file,
						debugging_port=self.debugging_port,
						chrome_executable=self.chromium_executable
					)

				# Do health check every 25 pages
				if i % 25 == 0:
					self.healthcheck.send_alive_signal(data={"amountOfScannedSites": i, "nextURLToScan": url})

				# Scan next url and save results
				logging.info(url)
				results = self.pageEvaluator.evaluate(browser.get_browser(), url)
				self.file_handler.write_results_to_file(f"{i}.json", results)
				self.db.save_results(results)
				self.archiver.archive_website_if_suspicious(results)
			except TimeoutException as e:
				# If a website times out during loading, log it and proceed with the next website.
				# Timeouts are going to happen for sure so there is no need to send a fail signal.
				# This exception is distinct from the ScannerTimeoutError where the scan takes too long
				# Here, nothing has to be written to the DB
				logging.error(f"Error when evaluating {url}: Timeout  - {e}")
			except KeyboardInterrupt:
				browser.stop()
				raise KeyboardInterrupt
			except (DatabaseError, PyChromeException, OSError) as e:
				# Log exception and continue with the next url
				logging.error(f"Error when evaluating {url}: {e}", exc_info=True)
				# Send an alert using the healthcheck system when there have been too many errors e.g. while trying
				# to insert data into the database. Otherwise it could happen that the scan continues but all
				# insertions fail silently so that no data is saved at all.
				errors_count += 1
				if errors_count > 50:
					self.healthcheck.send_failure_signal(
						f"Scan is still running but there have been more than 50 errors. Last at {url}: {e}"
					)
					errors_count = 0
				pass
		if browser is not None:
			browser.stop()
		self.db.close_connection()
