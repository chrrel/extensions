# Data Analysis

This is a library for performing automatic extension and website analyses based on the data collected using the scanner provided in this project.

## Evaluations

The analysis tool can perform the following evaluations. It is possible to define which evaluations are to be run as described in *Usage*.

### Extension Discovery (Web Accessible Resources)

* General Information (`general_info`)
  * Number of WAR requests
  * Number of WAR requests per scheme
* Requested Extensions (`requested_extensions`)
  * Extensions by request count
  * Extensions grouped by category (multiple evaluations)
  * Extensions by user count (ranges)
  * Extensions by frequent keywords (NLTK)
* Extension groups (`requested_extension_groups`)
  * Groups of extensions requested together
* Known extensions (`requested_known_extensions`)
  * Find WAR requests to known extensions (based on a list of extension IDs), e.g. extensions with vulnerabilities.
* Requesting websites (`requesting_websites`)
  * Websites requesting more than 7 distinct extensions
  * Websites performing war requests grouped by rank in Tranco list
  * Probing aggressivity (by Tranco rank)
  * Cumulative sum by Tranco rank
  * WAR requests/websites which use an F5 Big IP Appliance that generates WAR requests
* Requesting websites 3rd Party initiators (`3rd_party`)
  * WAR requests by initiator: "Same domain", "Other domain", "YouTube"

### Message Passing

* Runtime API: `runtime.connect()` (`connect`)
  * Calls to `runtime.connect()` *without* specified target extension
  * Calls to `runtime.connect()` *with* specified target extension
  * Connect attempts to known (vulnerable) extensions
  * Extensions connected to
* Runtime API: `runtime.sendMessage()` (`sendMessage`)
  * Calls to `runtime.sendMessage()` *without* specified target extension
  * Calls to `runtime.sendMessage()` *with* specified target extension
  * Messages to known (vulnerable) extensions
  * Messages containing known (malicious) contents
  * Messages containing suspicious keywords
  * Extensions messages are sent to
    * Extensions by number of messages
    * Extensions grouped by category (multiple evaluations)
    * Extensions by user count (ranges)
    * Extensions by frequent keywords (NLTK)
* `window.postMessage()` API (`postmessage`)
  * Messages containing suspicious keywords*
  * Messages containing known (malicious) contents
  * Messages occurring frequently*
* Runtime API: `port.postMessage()` (`portpostmessage`)
  * Print all messages sent using this method

`*` These evaluations can take very long. 

## Set Up

### Installation

This project requires Python 3 which can be installed using the following command.

```shell
sudo apt-get install python3 python3-pip python3-dev
```

All Python dependencies needed for running the tool can be installed using the following pip command.

```shell
pip3 install -r requirements.txt
```

### Configuration

1. Set all configuration values needed for the database connection in  `analysis/config.cfg`.
2. Add the paths for the used top list and extension data in  `analysis/config.cfg`.

## Usage

### Finding Known (Malicious) Data Patterns

The analysis tool can identify known malicious messages based on their structure and based on their content. For this, it is necessary to specify the messages and the corresponding extensions in  `input_data/extensions.json`.

In general there are two types of messages which we will describe with two examples. 

* The first type are messages that always have the same contents, e.g. `{action: "getData"}`.
* In contrast to that, messages of the other type have varying contents, e.g. if a parameter is passed. An example is the message `{data: <insert-data-here>, url: <insert-url-here>}`. 

In order to be able to detect both types we define a data structure that allows to store the relevant parts of known messages. It is a JSON list containing objects, one for every extension for which one or more messages are known. Beginning in line 4 all known message data for this extension is defined. Line 5 contains a complete object consisting of a key and a value. During the analysis phase our tool will search for occurrences of this object. Line 6 shows how messages of the second type can be found. Here, we only search for message data that contains the given keys as the contents of the corresponding values are unknown. Additionally it is also possible to search for combinations of the described approaches. Line 7 shows how to search for messages like `{action: "example", data: <insert-data-here>}`.

The analysis tool reads the list of extensions and their message data and builds the corresponding SQL query strings needed to find the messages within the database. 

```javascript
[{
	"browser": "chrome",
	"extension": "abcdefghijklmnoabcdefhijklmnoabc",
	"messages": [
		[{"action": "getData"}],
		["data", "url"],
		[{"action": "example"}, "data"]
	]
}]
```

The file  `input_data/extensions.json` contains data for several example messages from the [EmPoWeb](https://ieeexplore.ieee.org/document/8835286) paper.

### Choosing the Evaluations to Run

You can disable individual evaluations to only run a subset of all analyses by adjusting the boolean values in  `analysis/config.cfg`. This can be useful, e.g. for the sake of performance, as long-running evaluations can be disabled.

### Starting the Analysis

Run the analysis by executing the `main.py` in this directory.

```shell
python3 main.py
```

## Results

The analysis tool prints text outputs (e.g. tables) to `stdout`. The standard output format is LaTeX (implemented by the `to_latex()` method of Pandas data frames. All diagrams and graphs will be saved to `analysis/results/`. Moreover, this directory is used for storing intermediate results as a caching mechanism as JSON files.

> **Important**: For performance reasons, the analysis tool skips database queries and further long-running operations if intermediate results (JSON files) for the corresponding evaluations already exist in the results directory. In order to perform these operations again, e.g. after modifying database queries, these files need to be deleted manually first. 

## Implementation Details

The analysis tool is implemented following a modular approach. Therefore, new evaluations can be a added, existing ones can be disabled and even completely new analysis goals (e.g. targeting other security and privacy issues) can be implemented.

Currently there are two modules: `war` for the analysis of web accessible resources and `messages` for the analysis of message passing APIs.

The program executes based on the following flow:

`main.py → war.runwaranalysis → war.QueryWar + war.EvaluationWar`

* `main.py` loads all configurations and sets up the analysis (creates directories, establishes a database connection, ...).
* The runner (e.g. `runwaranalysis`) checks which evaluations are to be executed, triggers the database queries (which are defined  e.g. in `QueryWar`) and calls the corresponding evaluation methods (e.g. from `EvaluationWar`).
* The query scripts (e.g. `QueryWar`) implement the database queries using the ORM *Peewee*.
* The evaluation files (e.g. `EvaluationWar`) contain the actual data evaluations, mainly implemented based on the *Pandas* library.

