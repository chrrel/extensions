import csv
import json
import logging
import os
from collections import defaultdict

import matplotlib.pyplot as plt
import tikzplotlib
from pandas import DataFrame


def write_json_file(file_path: str, results):
	with open(file_path, "w") as json_file:
		json.dump(results, json_file, default=_set_default, indent=4)


def read_json_file(file_path: str):
	with open(file_path) as json_file:
		data = json.load(json_file)
		return data


def _set_default(obj) -> list:
	"""Convert sets to list since JSON does not support sets."""
	if isinstance(obj, set):
		return list(obj)
	raise TypeError


def get_tranco_list(file_path: str) -> defaultdict:
	tranco = defaultdict(int)
	with open(file_path) as f:
		for row in csv.reader(f, delimiter=",", skipinitialspace=True):
			position = int(row[0])
			domain = row[1]
			tranco[domain] = position
		return tranco


def retrieve_data(file_path: str, cb):
	"""
	Return data from JSON file at file_path if the file exists. Otherwise execute the callback which returns
	the data and writes it to file_path.
	"""
	if os.path.isfile(file_path):
		data = read_json_file(file_path)
	else:
		data = cb()
		write_json_file(file_path, data)

	return data


def build_query_strings_from_message_data(extensions: list, table_name: str) -> list:
	# Build the needed query strings for every extension
	for extension in extensions:
		extension["query_strings"] = []

		# For every message there will be one query string
		for message in extension["messages"]:
			logging.debug(json.dumps(message))
			query_string = f"SELECT website_id, url, data FROM {table_name}, website WHERE website_id=website.id "
			message_dicts = []
			message_keys = []
			for message_component in message:
				if type(message_component) is dict:
					# All key/value pairs of known messages
					message_dicts.append(message_component)
				else:
					# components that are no dicts are treated as keys
					message_keys.append(message_component)

			# Append query options to search for specific key/value pairs in messages, e.g. [{"method": "abc"}]
			# --> SELECT website_id, data FROM postmessage WHERE data @> '{"method": "abc"}' ;
			for message_dict in message_dicts:
				query_string = query_string + f"and data @> '{json.dumps(message_dict)}' "

			# Append query options for messages that have the given keys, e.g. 'action' and 'value'
			# --> SELECT website_id, data FROM postmessage WHERE data ?& array['action', 'value'] ;
			if message_keys:
				query_string = query_string + f"and data ?& array{message_keys} "

			# Append a ';' at the end to close the query string
			query_string = query_string + ";"
			extension["query_strings"].append(query_string)
			logging.debug(query_string)

	return extensions


def draw_stacked_bar_chart(df: DataFrame, labels: list, colors: list, legend_col_count: int, output_path: str):
	plt.rcParams["font.family"] = "TeX Gyre Pagella"
	plt.figure()
	ax = df.plot(kind="barh", stacked=True, width=0.4, color=colors, label=labels)
	ax.update({"ylabel": "", "xlabel": ""})
	# Set position of the bar and thegraph
	ax.set_ylim([-0.4, 1])
	plt.gcf().subplots_adjust(bottom=0.45, top=0.65)
	# Format xtick labels as percentage
	ax.set_xticklabels(['{:,.0%}'.format(x) for x in ax.get_xticks()])
	# Hide yaxis and all yticks (needed for tikz)
	ax.yaxis.set_visible(False)
	ax.set_yticklabels([""])
	ax.tick_params(left=False, bottom=False)
	ax.grid(axis="x", which='both', alpha=0.6, linestyle=":"),
	# Hide the sourrounding box
	#plt.box(on=None)

	for axis in ['top', 'bottom', 'left', 'right']:
		ax.spines[axis].set_linewidth(0.2)

	legend = ax.legend(loc="upper center", bbox_transform=plt.gcf().transFigure, labels=labels, ncol=legend_col_count)
	legend.get_frame().set_linewidth(0.3)

	plt.savefig(f"{output_path}.pdf", bbox_inches="tight")
	tikzplotlib.save(
		f"{output_path}.tex",
		axis_width="320",
		extra_axis_parameters=["x grid style={dotted,color=CTsemi}"],
	)
	plt.close()


def draw_donut_chart(df: DataFrame, output_path: str, legend_labels: list, descriptions: dict):
	plt.figure()
	df.plot.pie(
		figsize=(4, 8),
		counterclock=False,
		startangle=-270,
		autopct="%.2f %%",
		pctdistance=0.78,
		labels=legend_labels,
		textprops={"color": "white", "fontsize": 18},
		colors=["#c1e7ff", "#a3cbe5", "#86b0cc", "#6996b3", "#4c7c9b", "#2d6484", "#004c6d"],
	)
	plt.gcf().gca().legend(
		bbox_to_anchor=(1.5, 0.5),
		loc="center right",
		bbox_transform=plt.gcf().transFigure,
		labels=legend_labels
	)
	plt.gcf().gca().axis('off')
	# Add title, labels for axes, etc.
	plt.gca().update(descriptions)

	# Add a white circle in the middle to create a donut diagram
	middle_circle_white = plt.Circle((0, 0), 0.55, color='white')
	plt.gcf().gca().add_artist(middle_circle_white)

	# Save and close diagram
	plt.savefig(output_path, bbox_inches="tight")
	o = output_path.replace(".pdf", "")
	tikzplotlib.save(
		f"{o}.tex",
		axis_width="260",
	)
	plt.close()
