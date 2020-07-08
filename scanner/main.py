import configparser
import logging
import socket
import subprocess
import sys
import time

from filehandler import FileHandler
from scanner import Scanner
from utils.healthcheck import HealthCheck


def main():
	start = time.time()
	start_time_human_readable = time.asctime(time.gmtime(start))

	# Read config file
	config = configparser.ConfigParser()
	config.read("config.cfg")

	# Get the operating system's hostname
	hostname = socket.gethostname()

	# Set up health check
	healthcheck = HealthCheck(
		api_url=config["healthcheck"]["api_url"],
		api_key=config["healthcheck"]["api_key"],
		check_name=hostname,
		enabled=config.getboolean("healthcheck", "enabled")
	)
	log_message_start = f"Started scan on {hostname} at {start_time_human_readable} ({start})"
	healthcheck.send_start_signal(log_message_start)

	# Create directory for scan
	timestamp = int(start)
	scan_id = "scan-{}".format(timestamp)
	scan_directory_name = config["output"]["output_directory"] + scan_id
	FileHandler.create_directory(scan_directory_name)

	# Set up logger
	logfile = f"{config['output']['output_directory']}{scan_id}-{hostname}.log"
	logging.basicConfig(format="%(levelname)s:%(asctime)s:%(module)s:%(message)s", level=logging.INFO, filename=logfile)
	logging.getLogger().addHandler(logging.StreamHandler())

	try:
		logging.info(log_message_start)

		# Log current git commit and status for reproducibility reasons
		current_git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("ascii").strip()
		git_status = subprocess.check_output(["git", "status"]).decode("utf-8").strip()
		logging.info(f"Current git commit: {current_git_commit}")
		logging.info(f"Output of git status: {git_status}")

		# Define the line of the input file at which the scan shall start (begins at 1)
		start_line = 1
		if len(sys.argv) > 1:
			start_line = int(sys.argv[1])
		# Get all URLs to be scanned by this scanner by using the system's hostname as index
		urls_to_scan = FileHandler.get_urls_from_file(
			input_file=config["input"][hostname],
			start_line=start_line,
			limit=config.getint("scanner", "max_number_of_urls_to_scan")
		)
		scanner = Scanner(config, healthcheck, scan_id, hostname)
		scanner.run_scan(urls_to_scan)
	except (Exception, KeyboardInterrupt) as e:
		logging.critical(f"Error: Cannot run scan due to {e}", exc_info=True)
		healthcheck.send_failure_signal(f"Scan stopped. Exception: {e}")

	end = time.time()
	logging.info(f"Time needed for the complete scan: {end - start}")


if __name__ == "__main__":
	main()
