"""
This module can be used to download (Chrome) extensions from the extension store.
"""
import json
import os

import requests
import zipfile

from extensionstores import GetExtensionInfoError


def get_extension_manifest(extension_id: str) -> dict:
	"""
	Get the extension manifest of a Chrome extension.

	:param extension_id: The id of the extension.
	:return: The manifest as dictionary.
	"""
	directory_name = "results/downloaded_extensions/"
	file_path = download_chrome_extension(extension_id, directory_name)
	return _extract_manifest_from_extension(file_path)


def download_chrome_extension(extension_id: str, download_directory: str) -> str:
	"""
	Download the crx/zip file of a Chrome extension (if file does not exist yet).

	:param download_directory: Name of the directory to save the extension in.
	:param extension_id: The ID of the extension to download
	:return: Path to the downloaded file
	"""
	file_path = f"{download_directory}{extension_id}.zip"
	if not os.path.exists(download_directory):
		os.mkdir(download_directory)

	if os.path.isfile(file_path):
		return file_path

	download_url = f"https://clients2.google.com/service/update2/crx?response=redirect&os=linux&arch=x86-64&os_arch=x86-64&nacl_arch=x86-64&prod=chromiumcrx&prodchannel=unknown&prodversion=52.0.2743.116&acceptformat=crx2,crx3&x=id%3D{extension_id}%26uc"
	response = requests.get(download_url, timeout=20.0, stream=True)
	if response.status_code == 200:
		with open(file_path, "wb") as fd:
			for chunk in response.iter_content(chunk_size=512):
				fd.write(chunk)
			return file_path
	else:
		raise GetExtensionInfoError(f"Error: Cannot download crx file for extension {extension_id}")


def _extract_manifest_from_extension(extension_path: str):
	with zipfile.ZipFile(extension_path, "r") as zip_ref:
		manifest = zip_ref.read("manifest.json")
		return json.loads(manifest)
