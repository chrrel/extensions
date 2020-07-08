import logging

from playhouse.postgres_ext import PostgresqlExtDatabase
from sshtunnel import SSHTunnelForwarder

from models import database_proxy


class Database:
	"""
	This class is responsible for managing database connections. It is implemented as context manager and allows
	connections to a remote database server via an SSH tunnel.
	"""

	def __init__(self, ssh_address_or_host: str, database: str, user: str, password: str):
		"""
		Establish a database connection through an SSH tunnel using data from the SSH config file.
		"""
		try:
			self.tunnel = SSHTunnelForwarder(
				ssh_address_or_host=ssh_address_or_host,
				remote_bind_address=("127.0.0.1", 5432)
			)
			self.tunnel.start()
			self.db = PostgresqlExtDatabase(
				database=database,
				user=user,
				password=password,
				host="127.0.0.1",
				port=self.tunnel.local_bind_port
			)

			database_proxy.initialize(self.db)
			self.db.connect(reuse_if_open=True)
		except Exception as error:
			logging.error(f"Error while establishing a database connection: {error}")

	def __enter__(self):
		return self.db

	def __exit__(self, exc_type, exc_value, exc_traceback):
		# Close connection
		self.db.close()
		self.tunnel.stop()
