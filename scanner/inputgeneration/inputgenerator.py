from collections import defaultdict


class InputGenerator:
	@staticmethod
	def _get_urls_from_file(input_file):
		urls = []
		with open(input_file, "r") as file:
			for i, line in enumerate(file):
				url = line.split(",")[1]
				url = url.replace("\n", "")
				urls.append(url)
		return urls

	@staticmethod
	def _split_urls_into_groups(urls, n, chunk_size):
		"""
		Splits the given URLs into n groups by always appending the chunk_size next elements to the current group. Example:
			Input: ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13']
			Output: {0: ['00', '01', '02', '03', '04', '10', '11', '12', '13'], 1: ['05', '06', '07', '08', '09']}
		"""
		urls_in_chunks = [urls[i:i + chunk_size] for i in range(0, len(urls), chunk_size)]
		urls_grouped = defaultdict(list)
		group_id = 0
		for chunk in urls_in_chunks:
			# Append next chunk to current group
			urls_grouped[group_id] = urls_grouped[group_id] + chunk
			# Set group_id to next group
			group_id = (group_id + 1) % n
		return dict(urls_grouped)

	@staticmethod
	def split_input_data_into_files(input_file, output_directory, n, chunk_size):
		""" Splits the input data into n files which contains the URLs separated by line."""
		all_urls = InputGenerator._get_urls_from_file(input_file)
		urls_grouped = InputGenerator._split_urls_into_groups(urls=all_urls, n=n, chunk_size=chunk_size)
		for i, values in urls_grouped.items():
			lines = "\n".join(values)
			output_file_name = f"{output_directory}/extscan{(i + 1):02}.csv"
			with open(output_file_name, "w") as write_file:
				# Add newline at end of file
				write_file.writelines(lines + "\n")


if __name__ == "__main__":
	InputGenerator.split_input_data_into_files(
		input_file="../input_data/top-list.csv",
		output_directory="../input_data/top-1m/",
		n=20,
		chunk_size=25
	)
