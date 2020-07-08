import pandas as pd
from tldextract import tldextract

import extensionstores
import utils
import extensionanalysis as extanalysis
import extensiondownloader
from plotfig import PlotFig


class EvaluationMessages:
	output_dir = "results/messages/plots"
	plot_color_dark = "#003f5c"
	plot_color_less_dark = "#346888"

	@staticmethod
	def _extract_and_add_initiator(items: list) -> list:
		"""Extract the domain which initiated the item and add it as property to the item object.
		Items can be: connect, sendmessage"""
		for item in items:
			if item["call_frames"][0]["url"] != "":
				requesting_url = item["call_frames"][0]["url"]
			else:
				requesting_url = item["call_frames"][1]["url"]
			item["initiator_domain"] = tldextract.extract(requesting_url).registered_domain
			item["url"] = item["website"]["url"]
		return items

	@staticmethod
	def analyse_connects_without_targets(connects: list):
		print("Connects without targets")
		print(f"In total there were {len(connects)} connects without targets. The table below lists them grouped by initiator.")

		connects = EvaluationMessages._extract_and_add_initiator(connects)
		by_initiator_domain = pd.DataFrame(connects)
		by_initiator_domain = by_initiator_domain.drop_duplicates(subset=["url", "initiator_domain"])
		by_initiator_domain = by_initiator_domain.groupby("initiator_domain").count()["id"]
		by_initiator_domain = by_initiator_domain.sort_values(ascending=False)
		print("Connects without targets by initiator domain \n", by_initiator_domain.to_latex())

		with PlotFig(EvaluationMessages.output_dir, "connects_without_target_by_initiator") as fig:
			by_initiator_domain.plot(kind="barh", x="initiator_domain", y=["id"], color=EvaluationMessages.plot_color_dark)

	@staticmethod
	def analyse_connects_without_targets_initiator_details(connect_initiators: list):
		print("URLs of initiators of connects without targets")
		for connect in connect_initiators:
			initiator_domain = tldextract.extract(connect["initiator"]).registered_domain
			# Do not print initiators we already now / are not relevant
			if initiator_domain not in ["ad-score.com", "perimeterx.net", "clearrtb.com"]:
				print(connect["url"].ljust(40), connect["initiator"])

	@staticmethod
	def analyse_connects_with_targets(connects: list):
		# There are not many connects so simply print them all
		print("Connects with targets")
		connects = EvaluationMessages._extract_and_add_initiator(connects)
		print(f"In total there were {len(connects)} connects with targets. The table below lists them without duplicates.")

		df = pd.DataFrame(connects)
		df["url"] = df["website"].apply(lambda x: x.get("url").replace("http://", ""))
		df["extension_title"] = df["extension"].apply(lambda x: x.get("title"))
		df = df[["url", "initiator_domain", "extension_title", "extension_id"]]
		df = df.drop_duplicates()
		print(df[["extension_title", "extension_id"]].to_latex(index=False))
		df = df[["url", "initiator_domain", "extension_title"]]
		print("Same data with more info\n", df.to_latex(index=False))

	@staticmethod
	def analyse_connect_extensions(requested_extensions: dict):
		# There are not many extensions so simply print them all
		print(f"Number of Chrome/Opera/Edge extensions: ", len(requested_extensions["chrome"]))
		print(f"Number of Firefox extensions: ", len(requested_extensions["firefox"]))
		print(f"Number of other extensions: ", len(requested_extensions["other"]))

		print("List of all extensions from connects")
		for extensions in requested_extensions.items():
			for extension in extensions[1]:
				print(extension)

	@staticmethod
	def analyse_sendmessage_with_targets(messages: list):
		print("Sendmessages with targets")
		messages = EvaluationMessages._extract_and_add_initiator(messages)

		by_initiator_domain = pd.DataFrame(messages)
		by_initiator_domain = by_initiator_domain.drop_duplicates(subset=["url", "initiator_domain"])
		by_initiator_domain = by_initiator_domain[["id", "url", "initiator_domain", "extension_id"]]
		by_initiator_domain = by_initiator_domain.sort_values(by="initiator_domain")
		print("Sendmessages with targets ordered by initiator\n", by_initiator_domain.to_string())

		by_initiator_domain = by_initiator_domain.groupby("initiator_domain").count()
		by_initiator_domain = by_initiator_domain[by_initiator_domain["id"] > 1]["id"]
		by_initiator_domain = by_initiator_domain.sort_values(ascending=False)
		print("Sendmessages with targets grouped by initiator, having a count > 1 \n", by_initiator_domain.to_latex())

		with PlotFig(EvaluationMessages.output_dir, "sendmessages_with_target_by_initiator") as fig:
			by_initiator_domain.plot(kind="barh", x="initiator_domain", y=["id"], color=EvaluationMessages.plot_color_dark)

	@staticmethod
	def analyse_sendmessage_extensions_manifest(messages: list):
		print("Analyse the manifest files of the extension sendmessages are sent to")
		messages = EvaluationMessages._extract_and_add_initiator(messages)
		# Remove duplicate entries
		messages = [(message["website"]["url"].replace("http://", ""), message["initiator_domain"], message["extension_id"], str(message["data"])) for message in messages]
		messages = set(messages)
		for message in messages:
			extension_id = message[2]
			print(message)
			try:
				manifest = extensiondownloader.get_extension_manifest(extension_id)
				print(f"name                  : {manifest.get('name')}")
				print(f"externally_connectable: {manifest.get('externally_connectable')}")
				print(f"permissions           : {manifest.get('permissions')}")
				print(f"\n")
			except:
				print(f"Error: Did not find {extension_id}.zip")
			finally:
				print("\n")

	@staticmethod
	def analyse_sendmessage_websites(messages: list):
		print("Websites sending sendmessages to more than one extension.")
		messages = EvaluationMessages._extract_and_add_initiator(messages)

		df = pd.DataFrame(messages)
		df["url"] = df["url"].apply(lambda x: x.replace("http://", ""))
		df["website_id"] = df["website"].apply(lambda x: x.get("id"))
		# Delete all duplicate rows where the same website requests the same extension
		df = df.drop_duplicates(subset=["website_id", "extension_id"])
		# Then find all rows which have a website that occurs more than once, i.e. requests multiple extensions
		counts = df["website_id"].value_counts()
		df = df[df["website_id"].isin(counts.index[counts > 1])]
		df["extension_title"] = df["extension_id"]
		df["extension_title"] = df["extension_id"].apply(lambda extid: extensionstores.get_extension_title(extid))
		df = df[["website_id", "url", "initiator_domain", "extension_title", "extension_id", "data"]]
		print(df.to_latex(index=False))
		print("Same data, less details\n", df[["url", "extension_title"]].to_latex(index=False))
		print("Same data, extension id\n", df[["extension_title", "extension_id"]].to_latex(index=False))

	@staticmethod
	def analyse_sendmessage_extensions(requested_extensions: dict):
		# General info
		print("Extensions that sendmessages are sent to:")
		print(f"Number of Chrome/Opera/Edge extensions: ", len(requested_extensions["chrome"]))
		print(f"Number of Firefox extensions: ", len(requested_extensions["firefox"]))
		print(f"Number of other extensions: ", len(requested_extensions["other"]), "List of these extensions:", requested_extensions["other"])

		chrome_extensions = requested_extensions["chrome"]
		extensions = pd.DataFrame(chrome_extensions)
		chromecast_requests = extensions[extensions["id"].isin(extanalysis.chromecast_extension_ids)]
		print(f"Messages to Chromecast:\n {chromecast_requests.to_string()}")

		# By request count / Number of messages
		by_request_count = extanalysis.analyse_extensions_by_request_count_clean(chrome_extensions, min_request_count_clean=2)
		print("Extensions contacted via sendmessage by request count\n", by_request_count[["title", "request_count_clean", "request_count"]].to_latex())
		print("Extensions contacted via sendmessage by request count (with id)\n", by_request_count[["title", "id"]].to_latex(index=False))

		with PlotFig(EvaluationMessages.output_dir, "sendmessage_extensions_by_request_count") as fig:
			ax = by_request_count.plot(kind="barh", x="title", y=["request_count_clean"], color=EvaluationMessages.plot_color_dark)
			ax.update({"xlabel": "Number of sendmessages", "ylabel": "Extension Name", "title": "Extensions contacted via sendmessage by request count"})

		# By extension category
		by_category = extanalysis.analyse_extensions_by_category(chrome_extensions)
		print("Number of sendmessages sent per category / Number of sendmessages sent per category when only one message per website is counted / Number of extensions messages are sent to per category:")
		print(by_category.to_string())

		with PlotFig(EvaluationMessages.output_dir, "sendmessage_extensions_by_category") as fig:
			ax = by_category.plot(
				kind="barh",
				y=["request_count_clean", "extension_count"],
				label=["Messages (max. 1 per website)", "Extensions"],
				color=[EvaluationMessages.plot_color_less_dark, "#9dc6e0"],
				edgecolor=[EvaluationMessages.plot_color_dark, EvaluationMessages.plot_color_less_dark]
			)
			ax.update({"xlabel": "Count", "ylabel": "Extension Category"})
			ax.grid(axis="x", which="major", alpha=0.6, linestyle="--", color="#808080"),

		# By user count (ranges)
		by_user_count = extanalysis.analyse_extensions_by_user_count(chrome_extensions)
		print("Requested extensions grouped by user count:", by_user_count.to_string())

		utils.draw_donut_chart(
			df=by_user_count,
			output_path=f"{EvaluationMessages.output_dir}/sendmessage_extensions_by_user_count.pdf",
			legend_labels=["No data available", "0 - 100", "101 - 1000", "1001 - 10,000", "10,001 - 100,000", "100,001 - 1,000,000", "1,000,001+"],
			descriptions={"ylabel": ""},
		)

		# By frequent keywords
		frequent_keywords = extanalysis.analyse_extensions_by_keyword(chrome_extensions)
		print("Most frequent keywords in extension titles \n", frequent_keywords)

		with PlotFig(EvaluationMessages.output_dir, "sendmessage_extensions_by_keyword") as fig:
			frequent_keywords.plot(kind="bar", x="Word", y=["Frequency"], color=EvaluationMessages.plot_color_dark)

		# List all
		print("List of all Chrome/Opera/Edge extensions sendmessages were sent to \n", extensions.to_latex())

	@staticmethod
	def analyse_postmessage_known_messages(found_messages: list, known_extensions_messages_data: list):
		print(f"Number of postmessages with known messages: {len(found_messages)}")

		# Remove duplicates
		messages_without_duplicates = []
		for message in found_messages:
			if message not in messages_without_duplicates:
				messages_without_duplicates.append(message)
		print(f"Number of postmessages with known messages without duplicates: {len(messages_without_duplicates)}")

		for message in messages_without_duplicates:
			# Find the query params that were used to find this message
			for known_extension in known_extensions_messages_data:
				if message["extension"] == known_extension["extension"]:
					# Exclude messages sent via background (= using the runtime API)
					if known_extension['via'] != "background":
						# Print the found message
						print(message)
						# Print the search term (why the message is marked as 'known') and the risk and the used API
						print(f"-- search term: {known_extension['messages']}    risk: {known_extension['risk']}     via: {known_extension['via']}\n")
