import string

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import tikzplotlib

import utils
import networkx as nx
import extensionanalysis as extanalysis
from plotfig import PlotFig


class EvaluationWar:
	output_dir = "results/war/plots"
	plot_color_dark = "#003f5c"
	plot_color_less_dark = "#346888"

	@staticmethod
	def analyse_extensions(requested_extensions: dict):
		chrome_extensions = requested_extensions["chrome"]

		# General info
		extensions = pd.DataFrame(chrome_extensions)
		print(f"Number of distinct requested extensions {len(chrome_extensions)}")
		chromecast_requests = extensions[extensions["id"].isin(extanalysis.chromecast_extension_ids)]
		print(f"Requests for Chromecast:\n {chromecast_requests.to_string()}")

		# By request count
		by_request_count = extanalysis.analyse_extensions_by_request_count_clean(chrome_extensions, min_request_count_clean=14)
		print("Extensions by request count\n", by_request_count[["title", "request_count_clean", "request_count"]].to_latex())
		print("Extensions by request count (with IDs)\n", by_request_count[["title", "id"]].to_latex(index=False))

		# Remove chromecast extensions from the list for plotting the diagram
		by_request_count = by_request_count[~by_request_count["id"].isin(extanalysis.chromecast_extension_ids)]
		with PlotFig(EvaluationWar.output_dir, "requested_extensions_by_request_count") as fig:
			ax = by_request_count.plot(kind="barh", x="title", y=["request_count_clean", "request_count"], color=["#004c6d", "#7aa6c2"])
			ax.update({"xlabel": "Number of Requests", "ylabel": "Extension Name"})

		# By extension category
		by_category = extanalysis.analyse_extensions_by_category(chrome_extensions)
		print("Requested extensions grouped by category. Number of requests per category and Number of extensions")
		print(by_category.to_string())

		with PlotFig(EvaluationWar.output_dir, "requested_extensions_by_category") as fig:
			ax = by_category.plot(kind="barh", y=["extension_count"], label=["Extensions"], color=EvaluationWar.plot_color_less_dark, edgecolor=EvaluationWar.plot_color_dark)
			ax.update({"xlabel": "Number of extensions", "ylabel": "Extension category"})
			ax.grid(axis="x", which="major", alpha=0.6, linestyle="--", color="#808080"),

		# By category with requests
		with PlotFig(EvaluationWar.output_dir, "requested_extensions_by_category_requests") as fig:
			ax = by_category.plot(kind="barh", y=["request_count_clean"], label=["Requests (max. 1 per website)"], color=EvaluationWar.plot_color_less_dark, edgecolor=EvaluationWar.plot_color_dark)
			ax.update({"xlabel": "Number of requests", "ylabel": "Extension category"})
			ax.grid(axis="x", which="major", alpha=0.6, linestyle="--", color="#808080")

		# By user count (ranges)
		by_user_count = extanalysis.analyse_extensions_by_user_count(chrome_extensions)
		print("Requested extensions grouped by user count:", by_user_count.to_string())
		utils.draw_donut_chart(
			df=by_user_count,
			output_path=f"{EvaluationWar.output_dir}/requested_extensions_by_user_count.pdf",
			legend_labels=["No data available", "0 - 100", "101 - 1000", "1001 - 10,000", "10,001 - 100,000", "100,001 - 1,000,000", "1,000,001+"],
			descriptions={"ylabel": ""},
		)

		# By frequent keywords
		frequent_keywords = extanalysis.analyse_extensions_by_keyword(chrome_extensions)
		print("Most frequent keywords in extension titles \n", frequent_keywords)

		with PlotFig(EvaluationWar.output_dir, "requested_extensions_by_frequent_keywords", tikz_axis_width=310) as fig:
			ax = frequent_keywords.plot(kind="bar", x="Word", y=["Frequency"], color=EvaluationWar.plot_color_less_dark, edgecolor=EvaluationWar.plot_color_dark)
			ax.update({"xlabel": "Keyword", "ylabel": "Number of extensions"})
			ax.legend(labels=["Extensions"])
			ax.grid(axis="y", which="major"),
			plt.xticks(rotation=50, ha="right", fontsize="small")
		# TODO: add "xticklabel style = {rotate=50,anchor=east,yshift=-2mm, font=\\small}")

	@staticmethod
	def analyse_extension_groups(requested_extension_groups: dict, war_websites: list):
		results = extanalysis.analyse_extension_groups(requested_extension_groups, war_websites)
		dfa = pd.DataFrame()
		# Print the results
		for i, result in enumerate(results):
			df = pd.DataFrame(result["extensions"])
			df = df[["title", "category", "user_count", "id"]]
			df["count"] = result["count"]
			df.insert(loc=0, column="group", value=string.ascii_uppercase[i])
			df.fillna("-", inplace=True)
			df.replace("?", "-", inplace=True)
			df.replace(-1.0, "-", inplace=True)
			df.replace(-1, "-", inplace=True)
			df.replace("", "-", inplace=True)
			dfa = pd.concat([dfa, df])

			print("\midrule")
			print("\multicolumn{3}{c}{\\textbf{Group $" + string.ascii_uppercase[i] +"$ (",len(result['websites']), " websites)}} \\\ ")
			print("\midrule")
			for website in result["websites"]:
				print(f"{website['url'].replace('http://', '')} & {website['distinct_extensions_requested_count']} & {website['requested_wars_count']} \\\ ")

		print("Groups of extensions requested together")
		print(dfa.to_latex())
		print("Groups of extensions requested together (with extension IDs)")
		print(dfa[["title", "id"]].to_latex(index=False))

		EvaluationWar.draw_extension_groups_graph(results)

	@staticmethod
	def draw_extension_groups_graph(extension_groups: list):
		G = nx.Graph()
		# Add edges for every combination of extensions requested together to the graph
		for group in extension_groups:
			for extension in group["extensions"]:
				for extension2 in group["extensions"]:
					G.add_edge(f"{extension['id']}", f"{extension2['id']}")

		# Rename nodes to integer numbers since the extension ids are too long to be useful
		G = nx.convert_node_labels_to_integers(G, label_attribute="original_label")
		# Print the mapping extension id - integer number
		label_list = nx.get_node_attributes(G, "original_label")
		print("Labels for extension groups: \n", label_list)

		pos = nx.spring_layout(G, k=0.48, iterations=35)
		nodes = nx.draw_networkx_nodes(G, pos, node_color="white")
		nx.draw_networkx_edges(G, pos, width=0.8)
		nx.draw_networkx_labels(G, pos, font_color="white", font_size=10, font_family="TeX Gyre Pagella")
		nodes.set_edgecolor(EvaluationWar.plot_color_dark)
		nodes.set_color(EvaluationWar.plot_color_less_dark)
		plt.savefig(f"{EvaluationWar.output_dir}/extensions_requested_together.pdf", bbox_inches="tight")
		tikzplotlib.save(
			f"{EvaluationWar.output_dir}/extensions_requested_together.tex",
			extra_tikzpicture_parameters=["font=\huge"],
			extra_axis_parameters=["clip mode=individual"],
			axis_width="370"
		)
		plt.close()
		# TODO: Add 'mark size=7.9' to \addplot in the output file manually to get a beautiful graph

	@staticmethod
	def analyse_websites(websites_data: list, top_list_path: str):
		# Add position in tranco list to each website
		tranco_list = utils.get_tranco_list(top_list_path)
		for website in websites_data:
			domain = website["url"].replace("http://", "")
			website["tranco_rank"] = tranco_list[domain]

		websites = pd.DataFrame(websites_data)
		websites_many_requests = websites[(websites["distinct_extensions_requested_count"] > 7)]

		print("Websites requesting more than 7 distinct extensions together with the initiators of the WAR requests found on these pages")
		for index, row in websites_many_requests.iterrows():
			print("-"*100, "\n\n", row["url"])
			for request in row["requests"]:
				print(request["initiator"])
		websites_many_requests = websites_many_requests[["url", "distinct_extensions_requested_count", "requested_wars_count", "tranco_rank"]]

		print("Websites requesting more than 7 distinct extensions:")
		print(websites_many_requests.to_latex(index=False))

		ranges = [0, 1000, 10000, 100000, 250000, 500000, 1000000, 900000000]
		by_tranco_rank = websites.groupby(pd.cut(websites["tranco_rank"], ranges)).count()["id"]
		print(by_tranco_rank.to_latex())
		# Convert to DataFrame
		df = by_tranco_rank.to_frame()
		# Drop all rows where the count is 0
		df = df[df["id"] != 0]
		# Replace count with percentage
		total = df.sum(numeric_only=True)[0]
		df["id"] = df["id"] / total
		# Transpose to allow stacked chart
		df = df.transpose()
		utils.draw_stacked_bar_chart(
			df,
			labels=["1 - 1000", "1001 - 10,000", "10,001 - 100,000", "100,001 - 250,000", "250,001 - 500,000", "500,001 - 1,000,000 "],
			colors=["#c1e7ff", "#9dc6e0", "#7aa6c2", "#5886a5", "#346888", "#004c6d"],
			legend_col_count=2,
			output_path=f"{EvaluationWar.output_dir}/websites_by_tranco_rank2"
		)

		# Probing Aggressivity
		w = websites[(websites["requested_wars_count"] < 8000)].sort_values(by=["tranco_rank"])
		with PlotFig(EvaluationWar.output_dir, "websites_probing_aggressivity_by_tranco_rank") as fig:
			w.plot(x="tranco_rank", y=["distinct_extensions_requested_count"], color=[EvaluationWar.plot_color_dark])

	@staticmethod
	def analyse_websites_3rd_party(websites: dict):
		# Count number of values for each key and save to new dict
		websites_count = {key: len(value) for key, value in websites.items()}
		print(f"Number of websites performing requests from ... {websites_count}")
		df = pd.DataFrame.from_dict(websites_count, orient="index", columns=["Websites performing requests"])
		with PlotFig(EvaluationWar.output_dir, "websites_war_requests_3rd_party") as fig:
			ax = df.plot.pie(y=0, figsize=(6, 6), counterclock=False, startangle=0, pctdistance=0.7, autopct="%.2f %%", labels=None, textprops={"color": "white"}, colors=["#ffa600", "#bc5090", EvaluationWar.plot_color_dark])
			ax.update({"ylabel": ""})

		df = pd.DataFrame.from_dict(websites_count, orient="index", columns=["websites"])
		total = df.sum(numeric_only=True)[0]
		df["websites"] = df["websites"] / total
		df = df.transpose()

		utils.draw_stacked_bar_chart(
			df,
			labels=["Same domain", "Other domain", "YouTube"],
			colors=["#c1e7ff", EvaluationWar.plot_color_less_dark, EvaluationWar.plot_color_dark],
			legend_col_count=3,
			output_path=f"{EvaluationWar.output_dir}/websites_war_requests_3rd_party2"
		)

	@staticmethod
	def analyse_war_initiators(websites_data: list):
		# Create a table of the domains which initiated WAR requests. Show the number of distinct extensions
		# requested from this site and the number of websites on which this initiator made requests (e.g. as 3rd party)
		df = pd.DataFrame(websites_data)
		df = df.groupby('initiator')[['extension_id', 'website_id']].nunique().add_prefix('num_').reset_index()
		df = df[(df["num_website_id"] >= 3)]
		df = df.sort_values(by=["num_website_id"], ascending=False)
		# Reorder columns
		df = df[["initiator", "num_website_id", "num_extension_id"]]
		print("Initiator Domains with number of distinct extensions requested and the number of websites on which this initiator made requests (only initiators which were found on at least 3 websites)")
		print(df.to_latex(index=False))
