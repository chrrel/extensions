"""
This module implements methods for gathering additional information on extensions from the extension stores.
"""
import json
import re

import requests
from bs4 import BeautifulSoup


def get_extension_info(extension_id: str) -> dict:
	"""
	Retrieve information about an extension. Checks if info can be found in several resources.
	If no result is found the next resource is searched in the following order
	1 - Chrome Web Store, 2 - Opera Add-Ons Store, 3 - Microsoft Edge Add-Ons Store,
	4 - crx4chrome.com, 5 - crx.dam.io, 6 - Offline list of extensions.
	Note that 4, 5 and 6 only retrieve the extension's name.

	:param extension_id: The extension to search for
	:return: dictionary with information
	"""
	try:
		return get_extension_info_from_store("chrome", extension_id)
	except GetExtensionInfoError:
		pass
	try:
		return get_extension_info_from_store("opera", extension_id)
	except GetExtensionInfoError:
		pass
	try:
		return get_extension_info_from_store("edge", extension_id)
	except GetExtensionInfoError:
		pass
	try:
		return get_extension_info_from_crx4chrome(extension_id)
	except GetExtensionInfoError:
		pass
	try:
		return get_extension_info_from_list(extension_id)
	except GetExtensionInfoError:
		raise GetExtensionInfoError(f"Cannot find info for extension id {extension_id}")


def get_extension_title(extension_id: str) -> str:
	"""Get the title of an extension as a string. Returns an empty string if no title can be found."""
	try:
		return get_extension_info(extension_id)["title"]
	except GetExtensionInfoError:
		return ""


def get_info_for_extensions(extension_ids_with_count: list) -> list:
	"""
	Gather information on the extensions passed as param.
	Input: [{'id': 'pkedcjkdefgpdelpbcmbmeomcjbeemfm', 'request_count': 75363, 'request_count_clean': 75363}]
	Output: List of dicts with extension info
	"""

	extensions = []
	for extension_raw in extension_ids_with_count:
		extension = {}
		try:
			extension = get_extension_info(extension_raw["id"])
		except GetExtensionInfoError:
			extension = _build_extension_info_dict(extension_raw["id"], "")
		finally:
			extension["request_count"] = extension_raw["request_count"]
			extension["request_count_clean"] = extension_raw["request_count_clean"]
			extensions.append(extension)
	# sort by request_count_clean
	return sorted(extensions, key=lambda i: i["request_count_clean"], reverse=True)


def get_extension_info_from_store(browser: str, extension_id: str) -> dict:
	"""
	Retrieve information about an extension from the browser vendor's extension store.

	:param browser: One of "chrome" or "opera" or "edge"
	:param extension_id: The extension to search for
	:return:
	"""
	if browser == "chrome":
		extract_data = _extract_chrome_data
		base_url = "https://chrome.google.com/webstore/detail"
	elif browser == "opera":
		extract_data = _extract_opera_data
		base_url = "https://addons.opera.com/extensions/details/app_id"
	elif browser == "edge":
		extract_data = _extract_edge_data
		base_url = "https://microsoftedge.microsoft.com/addons/getproductdetailsbycrxid"
	else:
		raise GetExtensionInfoError("The specified browser is not supported.")

	try:
		url = f"{base_url}/{extension_id}"
		response = requests.get(url, headers={"Accept-Language": "en-US,en;q=0.5"})
		extension_info = extract_data(response, extension_id)
		return extension_info
	except Exception:
		raise GetExtensionInfoError(f"Error while retrieving data for {extension_id}")


def get_extension_info_from_crx4chrome(extension_id: str) -> dict:
	"""Get extension info from crx4chrome.com"""
	headers = {"user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:75.0) Gecko/20100101 Firefox/75.0"}
	url = f"https://www.crx4chrome.com/extensions/{extension_id}"
	response = requests.get(url, headers=headers, timeout=4.0)
	if response.status_code == 200:
		soup = BeautifulSoup(response.text, "html.parser")
		title = soup.find("h1").get("title")
		return _build_extension_info_dict(extension_id, title, browser="Chrome")
	else:
		raise GetExtensionInfoError(f"Error while retrieving data for {extension_id} from crx4chrome")


def get_extension_info_from_list(extension_id: str) -> dict:
	"""Get extension info from a manually curated list."""
	try:
		extension_info = {
			# Built-in extensions
			"pkedcjkdefgpdelpbcmbmeomcjbeemfm": "Chrome Media Router",
			"enhhojjnijigcajfphajepfemndkmdlo": "Chrome Media Router (Dev)",
			"ahfgeienlihckogmohjhadlkjgocpleb": "Web Store",
			"apdfllckaahabafndbhieahigkjlhalf": "Google Drive",
			"blpcfgokakmgnkcojhhkbfbldkacnbeo": "YouTube",
			"gfdkimpbcpahaombhbimeihdjnejgicl": "Feedback",
			"kmendfapggjehodndflmmgagdbamhnfd": "CryptoTokenExtension",
			"mfehgcgbbipciphmccgaenjidiccnmng": "Cloud Print",
			"mhjfbmdgcfjbbpaeojofohoefgiehjai": "Chrome PDF Viewer",
			"neajdppkdcdipfabeoofebfddakdcjhd": "Google Network Speech",
			"nkeimhogjdpnpccoofpliimaahmaaome": "Google Hangouts",
			"nmmhkkegccagdldgiimedpiccmgmieda": "Chrome Web Store-Zahlungen",
			"pjkljhegncpnkpknbcohdijeoejaedia": "Google Mail",
			"gndmhdcefbhlchkhipcnnbkcmicncehk": "Assessment Assistant",

			# Old Chromecast extensions
			# See https://github.com/chromium/chromium/commit/7682c4d0bc1f5ccde371417af4bf96e64a94f4ed
			"fjhoaacokmgbjemoflkofnenfaiekifl": "Google Cast",
			"fmfcbgogabcbclcofgocippekhfcmgfj": "Google Cast Staging",

			# Other extensions
			"idmboeiokenffegdeclenehnflmpakik": "Openoox",
			"hcobdfnjjaceclfdjpmmpiknimccjpmf": "Taskade - Team Tasks, Notes, Video Chat",
			"anepbdekljkmmimmhbniglnnanmmkoja": "Media Hint",
			"haldlgldplgnggkjaafhelgiaglafanh": "GoGuardian",
			"gelklkflikmdhljjiaijacpldbmchiml": "Turbo PDF",
			"opdcgjoencjhdbpbmhnkkdooajkpgpkp": "New Tab",
			"lmldjiibpfhdjjdjapcdlpjgeaihflpi": "飛比價格購物幫手：網路購物即時比價工具",
			"ebpjnjghimiofdlpnmhclanhckablllf": "Safe Browsing by Safely",
			"ihbjcgipifkapccgbkonknmdkhlfhaii": "Openoox | Awesome Bookmark Tool",
			"gnkkeblimhggleigddpgeiekibmbnfnb": "Media Hint ???",
			"dkioigicbijecidbooccnhfafineggga": "Padlet ???",
			"ipiejeandmfgndimddbdoalejbbebenn": "Miniplay.com - Free Games",
			"mgcnpgabjnbfmemhoemhngfmekdnkfch": "Captcha Recognition (Translated)",
			"pegejndighibdjlgclcnbadgpfaohanj": "?",
			"ppiglcdmigpbibdfbldkjpgbggfnmppc": "?",
			"haanbmjmhcofgngkioelkdablmmmbhoo": "?",
			"icepmffdobkomjgneohjlpohfcnejdii": "?",
			"iilolidfebgjhmfmlmfhokgajggcphff": "?",
			"kipakjdmemedbmfbibnldikcgceemhoc": "?"
		}
		return _build_extension_info_dict(extension_id, extension_info[extension_id])
	except KeyError:
		raise GetExtensionInfoError(f"Error while retrieving data for {extension_id} from list")


def _extract_chrome_data(response: requests.Response, extension_id: str) -> dict:
	"""Parse the Chrome Web Store website"""
	# Remove comments so that BeautifulSoup can parse the PageMap's content containing meta data
	html = response.text.replace("<!--", "").replace("-->", "")
	soup = BeautifulSoup(html, "html.parser")

	# Extract the extension's author from the text field "offered by XY" where XY is either plain text or a link
	pattern = re.compile(r"offered by .+")
	html_author = soup.find(text=pattern)
	if html_author is not None:
		author = html_author.replace("offered by ", "")
	else:
		pattern = re.compile(r"offered by")
		author = soup.find(text=pattern).find_next_sibling("a").string

	return _build_extension_info_dict(
		extension_id=extension_id,
		title=soup.find("meta", property="og:title")["content"],
		description=soup.find("meta", property="og:description")["content"],
		author=author,
		category=soup.find("attribute", attrs={"name": "category"}).get_text(),
		user_count=int(soup.find("attribute", attrs={"name": "user_count"}).get_text()),
		browser="Chrome"
	)


def _extract_opera_data(response: requests.Response, extension_id: str) -> dict:
	"""Parse the Opera Store website"""
	soup = BeautifulSoup(response.text, "html.parser")
	downloads = soup.find("dt", string="Downloads").nextSibling.text
	downloads = int(downloads.replace(",", ""))
	return _build_extension_info_dict(
		extension_id=extension_id,
		title=soup.find("meta", property="og:title")["content"],
		description=soup.find("meta", property="og:description")["content"],
		author=soup.find("h2", {"itemtype": "https://schema.org/Organization"}).find("a").text,
		category=soup.find("meta", property="aoc:category")["content"],
		user_count=downloads,
		browser="Opera"
	)


def _extract_edge_data(response: requests.Response, extension_id: str) -> dict:
	"""Retrieve data from the Microsoft Edge Add-Ons Store REST API"""
	# Microsoft has a REST API for gathering extension info, so there is no need to scrape the website
	content = json.loads(response.text)
	return _build_extension_info_dict(
		extension_id=extension_id,
		title=content["name"],
		description=content["shortDescription"],
		author=content["developer"],
		category=content["category"],
		user_count=-1,
		browser="Edge"
	)


def _build_extension_info_dict(
		extension_id: str, title: str, description: str = "", author: str = "",
		category: str = "", user_count: int = -1, browser: str = ""
	) -> dict:

	# The category can actually be multiple categories so create a list of categories
	categories = category.split(",")
	category = _get_category_names(categories)
	# If the category list is empty or only a single category then return it as string
	if len(category) == 0:
		category = ""
	elif len(category) == 1:
		category = category[0]

	return {
		"id": extension_id,
		"title": title,
		"description": description,
		"author": author,
		"category": category,
		"user_count": user_count,
		"browser": browser
	}


def _get_category_names(category_ids: list) -> list:
	""" Transform the category id like '10_blogging' to a human-friendly name like 'Blogging'
		If no name is found for an id the input value will be returned
	"""
	categories = {
		"1_communication": "Social & Communication",
		"2_entertainment": "Entertainment",
		"6_news": "News & Weather",
		"7_productivity": "Productivity",
		"10_blogging": "Blogging",
		"11_web_development": "Developer Tools",
		"12_shopping": "Shopping",
		"13_sports": "Sports",
		"14_fun": "Fun",
		"15_by-google": "By Google",
		"22_accessibility": "Accessibility",
		"28_photos": "Photos",
		"38_search_tools": "Search Tools",
		"69_office_applications": "Office Applications",
		"71_online_documents_and_file_storage": "Online Documents & File Storage",
		"83_online_videos": "Online Videos",
		"87_task_management": "Task Management"
	}
	# Replace the category id with the category title, if not found use the category id as default
	return [categories.get(category, category) for category in category_ids]


class GetExtensionInfoError(Exception):
	pass
