from collections import defaultdict

import tldextract

from extensionanalysis import chromecast_extension_ids
from query import Query


class QueryWar(Query):
	def query_war_schemes(self) -> list:
		"""Get the number of WAR requests and the number of websites performing WAR requests grouped per URL scheme"""
		results = []
		schemes = [".*", "^chrome-extension://", "^moz-extension://", "^opera-extension://", "^ms-browser-extension://", "^chrome://"]
		for scheme in schemes:
			count = self.db.execute_sql(
				sql="SELECT COUNT(requested_war), COUNT(DISTINCT website_id) FROM warrequest WHERE requested_war ~* %(scheme)s;",
				params={"scheme": (scheme,)}
			).fetchone()
			results.append({"scheme": scheme.replace("^", "").replace("://", ""), "requests": count[0], "websites": count[1]})

		# Get count for chrome-extension:// with Chrome Media Router only
		count_wo_cast = self.db.execute_sql(
			sql="SELECT COUNT(requested_war), COUNT(DISTINCT website_id) FROM warrequest WHERE requested_war ~* '^chrome-extension://' AND requested_extension_id IN %(chromecast_extension_ids)s;",
			params={"chromecast_extension_ids": tuple(chromecast_extension_ids)}
		).fetchone()
		results.append({"scheme": "chrome-extension (Chrome Media Router only)", "requests": count_wo_cast[0], "websites": count_wo_cast[1]})

		# Get count for chrome-extension:// with Chrome Media Router only requests excluded
		count_wo_cast = self.db.execute_sql(
			sql="SELECT COUNT(requested_war), COUNT(DISTINCT website_id) FROM warrequest WHERE requested_war ~* '^chrome-extension://' AND requested_extension_id NOT IN %(chromecast_extension_ids)s;",
			params={"chromecast_extension_ids": tuple(chromecast_extension_ids)}
		).fetchone()
		results.append({"scheme": "chrome-extension (Chrome Media Router excluded)", "requests": count_wo_cast[0], "websites": count_wo_cast[1]})
		return results

	def query_war_requested_extensions(self) -> dict:
		query = """
		SELECT
			requested_extension_id,
			COUNT(requested_extension_id) AS request_count,
			COUNT(DISTINCT (requested_extension_id || website_id)) AS request_count_clean 
		FROM
			warrequest 
		GROUP BY
			requested_extension_id
		ORDER BY
			request_count_clean DESC;
		"""
		return self._query_extensions(query)

	def query_websites_with_war_requests(self) -> list:
		websites = []
		# Get website URLs together with the number of distinct requested extensions and the number of requested WARs
		cursor = self.db.execute_sql("""
		SELECT
			website.id,
			website.url,
			COUNT(DISTINCT requested_extension_id) AS distinct_extensions_requested_count, 
			COUNT(requested_extension_id) AS requested_wars_count
		FROM
			warrequest, website 
		WHERE
			website.id = warrequest.website_id 
		GROUP BY
			website.id, website.url
		ORDER BY
			distinct_extensions_requested_count DESC;
		""")
		for website_id, url, distinct_extensions_requested_count, requested_wars_count in cursor.fetchall():
			website = {
				"id": website_id,
				"url": url,
				"distinct_extensions_requested_count": distinct_extensions_requested_count,
				"requested_wars_count": requested_wars_count,
				"requests": []
			}
			if distinct_extensions_requested_count > 5:
				website["requests"] = self.query_war_requests_for_website(website_id)
			websites.append(website)
		return websites

	def query_war_requests_for_website(self, website_id: int) -> list:
		cursor = self.db.execute_sql("""
				SELECT requested_extension_id, requested_war, get_initiator(request_object) FROM warrequest  WHERE website_id = %s;
			""", (website_id,))
		requests = []
		for requested_extension_id, requested_war, initiator in cursor.fetchall():
			requests.append({
				"requested_extension_id": requested_extension_id,
				"requested_war": requested_war,
				"initiator": initiator
			})
		return requests

	def query_war_requests_with_initiators(self) -> list:
		"""Get a list of dicts of WAR requests. Contains the requested extension_id, website_id and
		the request initiator. Chromecast requests are excluded.
		"""
		war_requests = []
		cursor = self.db.execute_sql("""
			SELECT
				requested_extension_id,
				website_id,
				get_initiator(request_object)
			FROM warrequest 
			WHERE requested_extension_id NOT IN ('pkedcjkdefgpdelpbcmbmeomcjbeemfm', 'enhhojjnijigcajfphajepfemndkmdlo')
			;
		""")
		for extension_id, website_id, initiator_url in cursor.fetchall():
			initiator_domain = tldextract.extract(initiator_url).registered_domain
			war_requests.append({
				"extension_id": extension_id,
				"website_id": website_id,
				"initiator": initiator_domain
			})
		return war_requests

	def query_war_extensions_requested_together(self) -> dict:
		"""Get the ids of the requested extensions without duplicates for each website. Chromecast requests are excluded.
		:return: e.g. {"198542": ["pkedcjkdefgpdelpbcmbmeomcjbeemfm","enhhojjnijigcajfphajepfemndkmdlo"]}
		"""
		wars = defaultdict(list)
		cursor = self.db.execute_sql("SELECT website_id, requested_extension_id FROM warrequest WHERE requested_extension_id NOT IN ('pkedcjkdefgpdelpbcmbmeomcjbeemfm', 'enhhojjnijigcajfphajepfemndkmdlo');")
		for website_id, requested_extension_id in cursor.fetchall():
			if requested_extension_id not in wars[website_id]:
				wars[website_id].append(requested_extension_id)
		return dict(wars)

	def query_war_request_3rd_party(self) -> dict:
		"""Returns websites that perform WAR requests grouped by request source (same/3rd party domain/YouTube).
		If a websites performs multiple request, only one is counted (per category)."""
		# Use sets to ensure that websites are only counted once
		websites = {
			"same_domain": set(),
			"other_domain": set(),
			"youtube": set()
		}
		query_string = "SELECT website_id, url, get_initiator(request_object) AS initiator FROM warrequest, website WHERE warrequest.website_id = website.id;"
		cursor = self.db.execute_sql(query_string)
		for website_id, url, req_url in cursor.fetchall():
			website_domain = tldextract.extract(url).registered_domain
			request_source_domain = tldextract.extract(req_url).registered_domain

			if request_source_domain in ["youtube.com", "youtube-nocookie.com"]:
				websites["youtube"].add(url)
			elif website_domain != request_source_domain:
				websites["other_domain"].add(url)
			else:
				websites["same_domain"].add(url)
		return websites

	def query_war_request_f5(self):
		""" Gather information on WAR requests where the initiator URL contains the string '/TSPD/'
			which indicates that a F5 Big IP appliance is used.
		"""
		query_string = "SELECT COUNT(id) AS request_count, COUNT(DISTINCT website_id) AS distinct_websites_count, COUNT(DISTINCT requested_extension_id) distinct_extensions_count FROM warrequest WHERE get_initiator(request_object) LIKE '%%/TSPD/%%';"
		result = self.db.execute_sql(query_string).fetchone()
		return {
			"request_count": result[0],
			"distinct_websites_count": result[1],
			"distinct_extensions_count": result[2]
		}
