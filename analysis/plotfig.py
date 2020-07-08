import matplotlib.pyplot as plt
import tikzplotlib


class PlotFig:
	"""
	Create figures with matplotlib, then save them as PDF and as tikz figures using tikzplotlib.
	"""

	def __init__(self, file_path: str, file_name: str, tikz_axis_width: int = 250, tikz_extra_axis_parameters: list = None):
		self.path = f"{file_path}/{file_name}"
		self.tikz_axis_width = tikz_axis_width
		if tikz_extra_axis_parameters is None:
			tikz_extra_axis_parameters = []
		self.tikz_extra_axis_parameters = tikz_extra_axis_parameters.append("label style={font=\\small}")

	def __enter__(self):
		return plt.figure()

	def __exit__(self, exc_type, exc_value, exc_traceback):
		plt.savefig(f"{self.path}.pdf", bbox_inches="tight")
		tikzplotlib.save(
			f"{self.path}.tex",
			extra_axis_parameters=self.tikz_extra_axis_parameters,
			axis_width=str(self.tikz_axis_width)
		)
		plt.close()
