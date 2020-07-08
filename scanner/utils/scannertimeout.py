import signal
from exceptions import ScannerTimeoutError


class ScannerTimeout:
	"""
	ScannerTimeout class using ALARM signal
	Adapted from:
	https://stackoverflow.com/questions/8464391/what-should-i-do-if-socket-setdefaulttimeout-is-not-working/8465202#8465202
	"""
	def __init__(self, seconds):
		self.seconds = seconds

	def __enter__(self):
		signal.signal(signal.SIGALRM, self.raise_timeout)
		signal.alarm(self.seconds)

	def __exit__(self, *args):
		signal.alarm(0)  # disable alarm

	def raise_timeout(self, signum, frame):
		raise ScannerTimeoutError()
