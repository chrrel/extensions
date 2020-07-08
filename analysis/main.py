import configparser
import logging
from pathlib import Path

import utils
from database import Database
from messages.runmessageanalysis import message_analysis
from models import Website
from war.runwaranalysis import war_analysis


def main():
	logging.basicConfig(level=logging.INFO)

	# Read config file
	config = configparser.ConfigParser()
	config.read("config.cfg")

	# Get known malicious messages and the corresponding vulnerable extensions
	extensions_messages_data = utils.read_json_file(config["input"]["extension_data_path"])
	# Extract the extension ids only from the known data
	known_extension_ids = [e["extension"] for e in extensions_messages_data]

	# Create directories for storing results
	Path("results/war/plots").mkdir(parents=True, exist_ok=True)
	Path("results/messages/plots").mkdir(parents=True, exist_ok=True)

	with Database(
		config["database"]["ssh_address_or_host"],
		config["database"]["database_name"],
		config["database"]["user"],
		config["database"]["password"]
	) as db:
		print(f"Total number of scanned websites in database: {Website.select().count()}")
		war_analysis(db, config, extensions_messages_data, known_extension_ids)
		message_analysis(db, config, extensions_messages_data, known_extension_ids)


if __name__ == "__main__":
	main()
