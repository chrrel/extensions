"""
This module contains methods for analysing extensions.
"""
import string
from collections import defaultdict

import nltk
import pandas as pd

import extensionstores

chromecast_extension_ids = ["pkedcjkdefgpdelpbcmbmeomcjbeemfm", "enhhojjnijigcajfphajepfemndkmdlo"]


def analyse_extensions_by_request_count_clean(requested_extensions: list, min_request_count_clean: int) -> pd.DataFrame:
	"""
	Analyse extensions by the number of websites which requested the extensions.

	:param requested_extensions: The extension data to analyse
	:param min_request_count_clean: Only extensions having at least this number of requests are analysed
	:return: A pandas data frame containing the results
	"""
	df = pd.DataFrame(requested_extensions)
	df = df[(df["request_count_clean"] >= min_request_count_clean)]
	# Start the index at 1 instead of 0 to use it as a ranking number
	df.index += 1
	return df


def analyse_extensions_by_category(requested_extensions: list) -> pd.DataFrame:
	"""
	Analyse extensions by their categories as defined in the extension stores.
	Returns the number of requests, the number of extensions
	and the number of websites per category.
	Chromecast extensions are excluded.

	:param requested_extensions: The extension data to analyse
	:return: A pandas data frame containing the results
	"""
	df = pd.DataFrame(requested_extensions)
	# Category can contain a list of categories, make these to own rows
	df = df.explode("category")
	# Exclude requests to chromecast
	df = df[~df["id"].isin(chromecast_extension_ids)]
	# Replace empty categories with unknown
	df["category"].replace({"": "[unknown]"}, inplace=True)
	df = df.groupby("category").agg(
		request_count=pd.NamedAgg(column="request_count", aggfunc="sum"),
		request_count_clean=pd.NamedAgg(column="request_count_clean", aggfunc="sum"),
		extension_count=pd.NamedAgg(column="request_count", aggfunc="count"),
	)
	df = df.sort_values(by="extension_count", ascending=False)
	return df


def analyse_extensions_by_user_count(requested_extensions: list) -> pd.DataFrame:
	"""
	Analyse extensions grouped by the number of users who installed them (in ranges).
	Chromecast extensions are excluded.

	:param requested_extensions: The extension data to analyse
	:return: A pandas data frame containing the results
	"""
	df = pd.DataFrame(requested_extensions)
	ranges = [-2, -1, 100, 1000, 10000, 100000, 1000000, 900000000]
	# Exclude requests to chromecast
	df = df[~df["id"].isin(chromecast_extension_ids)]
	df = df.groupby(pd.cut(df["user_count"], ranges)).count()["id"]
	return df


def analyse_extensions_by_keyword(requested_extensions: list) -> pd.DataFrame:
	"""
	Analyse extension titles using NLTK to find frequent keywords. Returns the top 25 keywords.

	:param requested_extensions: The extension data to analyse
	:return: A pandas data frame containing the results
	"""
	nltk.download('punkt')
	nltk.download("stopwords")
	stopwords = nltk.corpus.stopwords.words("english")

	# Create a list of frequent words
	# For every extension create a set of words included in the extension title. We use a set to make sure that every
	# word only occurs once per extension. We exclude stopwords and punctuation symbols.
	# Moreover, we strip whitespace and only use lowercase versions of all words.
	titles = []
	for extension in requested_extensions:
		title_tokens = nltk.word_tokenize(extension["title"])
		title_words = set()
		for word in title_tokens:
			if word not in stopwords and word not in string.punctuation:
				title_words.add(word.strip().lower())
		titles.append(title_words)

	# Flatten the list of sets to a simple list and create a frequency distribution
	text = [word for title in titles for word in title]
	fdist = nltk.FreqDist(text)

	# Create data frame from FreqDist
	frequent_keywords = pd.DataFrame(fdist.most_common(25), columns=["Word", "Frequency"])
	return frequent_keywords


def analyse_extension_groups(requested_extension_groups: dict, war_websites: list) -> list:
	"""
	Analyse which extensions were requested together. Only considers groups that
	actually were requested, not subsets of these groups.

	:param requested_extension_groups:
	:param war_websites: List of websites which performed WAR requests.
	:return: A list of the found groups.
	"""
	# Extension groups must be requested by at least min_count websites
	min_count = 3
	# A group consists of min_group_size extensions
	min_group_size = 2

	print("Requested extension groups")
	# Transform the list of websites that performed war requests to a dictionary where the website id is used as key.
	websites = {website["id"]: website for website in war_websites}

	# Create a default dict where the key is an extension group (as tuple) and the corresponding value
	# is the number of occurrences of this group. A group consists of at least min_group_size extensions.
	groups_with_count = defaultdict(lambda: {"count": 0, "websites": []})
	for website_id, group in requested_extension_groups.items():
		if len(group) >= min_group_size:
			extensions = tuple(group)
			groups_with_count[extensions]["count"] += 1
			groups_with_count[extensions]["websites"].append(websites[int(website_id)])

	# Create a list of dicts, one for each group containing info on the extensions and the requesting websites
	results = []
	for extensions, data in groups_with_count.items():
		# Only keep groups that occurred at least min_count times
		if data["count"] < min_count:
			continue
		result = {"extensions": [], "websites": data["websites"], "count": data["count"]}
		# Gather information on all requested extensions from the web store
		for extension_id in extensions:
			try:
				extension_info = extensionstores.get_extension_info(extension_id)
			except extensionstores.GetExtensionInfoError:
				extension_info = {"title": "-", "author": "-", "id": extension_id}
			result["extensions"].append(extension_info)
		results.append(result)
	return results
