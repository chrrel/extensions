import json
import requests
import configparser

config = configparser.ConfigParser()
config.read("../scanner/config.cfg")

API_KEY = config["healthcheck"]["api_key"]

# Get all existing checks
response = requests.get(config["healthcheck"]["api_url"], headers={"X-Api-Key": API_KEY})
json_data = json.loads(response.text)
print(json.dumps(json_data, indent=4))


# Update all existing checks
data = {
	"api_key": API_KEY,
	"timeout": 1080,
	"grace": 900,
}
for scanner in json_data["checks"]:
	update_url = scanner["update_url"]
	res = requests.post(update_url, data=json.dumps(data))
	print(scanner["name"], res.status_code, res.text)

