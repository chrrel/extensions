import logging
from configparser import ConfigParser

import pandas as pd
from playhouse.postgres_ext import PostgresqlExtDatabase

import extensionstores
import utils
from war.evaluationwar import EvaluationWar
from war.querywar import QueryWar


def war_analysis(db: PostgresqlExtDatabase, config: ConfigParser, extensions_messages_data: list, known_extension_ids: list):
	query = QueryWar(db)
	if config.getboolean("war", "general_info"):
		logging.info("[+] Querying general info for WARs")
		by_scheme = query.query_war_schemes()
		print(pd.DataFrame(by_scheme).to_latex(index=False))

	if config.getboolean("war", "requested_extensions"):
		logging.info("[+] Querying requested extensions")

		def get_data():
			extensions = query.query_war_requested_extensions()
			extensions["chrome"] = extensionstores.get_info_for_extensions(extensions["chrome"])
			return extensions
		requested_extensions = utils.retrieve_data("results/war/war_requested_extensions.json", get_data)
		EvaluationWar.analyse_extensions(requested_extensions)

	if config.getboolean("war", "requested_extension_groups"):
		logging.info("[+] Querying for groups of extensions requested together")
		requested_extension_groups = utils.retrieve_data("results/war/war_requested_extension_groups.json", lambda: query.query_war_extensions_requested_together())
		websites = utils.retrieve_data("results/war/war_websites.json", lambda: query.query_websites_with_war_requests())
		EvaluationWar.analyse_extension_groups(requested_extension_groups, websites)

	if config.getboolean("war", "requested_known_extensions"):
		extensions = utils.retrieve_data("results/war/war_requested_known_extensions.json", lambda: query.query_for_known_extensions(table="warrequest", known_ids=known_extension_ids))
		print(f"Number of WAR requests to known extensions: {len(extensions)}.\nList of these extensions: {extensions}")

	if config.getboolean("war", "requesting_websites"):
		logging.info("[+] Querying for requesting websites")

		websites_with_wars = utils.retrieve_data("results/war/war_websites.json", lambda: query.query_websites_with_war_requests())
		EvaluationWar.analyse_websites(websites_with_wars, config["input"]["toplist_path"])

		websites_f5_protection = utils.retrieve_data("results/war/war_websites_f5.json", lambda: query.query_war_request_f5())
		print("WAR requests/Websites which use a F5 Big IP Appliance that generates WAR requests\n", websites_f5_protection)

		war_requests_with_initiators = utils.retrieve_data("results/war/war_initiators.json", lambda: query.query_war_requests_with_initiators())
		EvaluationWar.analyse_war_initiators(war_requests_with_initiators)

	if config.getboolean("war", "3rd_party"):
		logging.info("[+] Querying for 3rd party website analysis")
		websites = utils.retrieve_data("results/war/war_websites_3rd.json", lambda: query.query_war_request_3rd_party())
		EvaluationWar.analyse_websites_3rd_party(websites)
