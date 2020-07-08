import json
import os


class FileHandler:
	def __init__(self, scan_directory, print_to_file=True):
		self._scan_directory = scan_directory
		# Define if results shall be printed to file
		self._print_to_file = print_to_file

	def write_results_to_file(self, file_name, results):
		if self._print_to_file:
			file_path = self._scan_directory + file_name
			with open(file_path, "w") as write_file:
				json.dump(results, write_file, indent=4)

	@staticmethod
	def create_directory(directory):
		try:
			if not os.path.exists(directory):
				os.makedirs(directory)
		except OSError:
			raise OSError(f"Error: Cannot create directory {directory}")

	@staticmethod
	def get_urls_from_file(input_file, start_line, limit):
		urls = []
		with open(input_file, "r") as file:
			for i, line in enumerate(file):
				# Stop if maximum number of URLs is reached
				if len(urls) == limit:
					break
				# Ignore all lines before start_line (i starts at 0, so add 1)
				if (i+1) < start_line:
					continue
				url = line.replace("\n", "")
				urls.append(f"http://{url}")
		return urls
