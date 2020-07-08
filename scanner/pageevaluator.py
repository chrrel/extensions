import time
import random
import logging

from eventhandler import EventHandler
from exceptions import ScannerTimeoutError
from utils.scannertimeout import ScannerTimeout


class PageEvaluator:
	JAVASCRIPT = """
	/* Overwrite alert, confirm and prompt since when called these block the browser forever. */
	window.alert = function () { return true; }
	window.confirm = function () { return true; }
	window.prompt = function () { return true; }

	/*  Define the window.chrome object. It is needed for detecting chromecast WAR requests,
		but is not available in headless mode by default. */
	window.chrome = {};	
	chrome = { runtime: {} }
	
	/* Also define the browser object which is used for accessing communication APIs in Firefox. */
	browser = { runtime: {} }

	/*  Define the runtime.sendMessage function as it is not available in headless Chrome. */
	runtime = {}
	runtime.sendMessage = function (extensionId, message, options) {
		try {
			console.log("SendMessageObject", extensionId, JSON.stringify(message));
		}
		catch (e) {
			var error = {"location": window.location.href, "errorMessage": e}
			console.error("Error", error);
		}
	}

	/*  Define the runtime.connect function as it is not available in headless chrome. */		
	runtime.connect = function () {
		try {
			/* The parameters are optional so check which ones were passed.*/
			var extensionId = "";
			var connectInfo = {}; 
			if (typeof arguments[0] == "string") {
				extensionId = arguments[0];
			}
			if (typeof arguments[0] == "object") {
				connectInfo = arguments[0];
			}
			if (typeof arguments[1] == "object") {
				connectInfo = arguments[1];
			}
			
			if(connectInfo && connectInfo.name) {
				name = connectInfo.name;
			} 
			else {
				name = "NoConnectInfoNameSpecified";
			}
			console.log("ConnectObject", extensionId, JSON.stringify(connectInfo));

			/* Return a Port object as specified for the connect function.*/
			return {
				name: name,
				disconnect: function () { return true; },
				onDisconnect: {},
				onMessage: {},
				postMessage: function (message) {
					try {
						console.log("PortPostMessageObject", extensionId, JSON.stringify(message));
					}
					catch (e) {
						var error = {"location": window.location.href, "errorMessage": e}
						console.error("Error", error);
					}
					return false;
				},
				sender: {}
			}
		}
		catch (e) {
			var error = {"location": window.location.href, "errorMessage": e}
			console.error("Error", error);
		}
	}
	
	/* Make all runtime methods available to Chrome. */
	chrome.runtime = runtime;
	/* Make all runtime methods available to Firefox. */
	browser.runtime = runtime;

	/*  Returns a stringified version of the important properties of the event object. 
		It is not possible to simply JSON.stringify an event object due to circular references. */
	function extractMessageDetails(event) {
		var message = {
			data: event.data,
			origin: event.origin,			
		}
		return JSON.stringify(message);
	}

	/*  Listen for message events and log these to the console. */
	window.addEventListener("message", function(event) {
		try {
			console.log("PostMessageObject", extractMessageDetails(event));
		}
		catch (e) {
			var error = {"location": window.location.href, "errorMessage": e}
			console.error("Error", error);
		}
	});
	""".lstrip()

	def __init__(self, timeout, tab_wait_time):
		self._timeout = timeout
		self._tab_wait_time = tab_wait_time

	def evaluate(self, browser, url):
		tab = browser.new_tab()
		# Create a new event handler object for each website as it stores data
		eh = EventHandler()

		# Activate event handlers
		tab.Runtime.consoleAPICalled = eh.message_handler
		tab.Network.requestWillBeSent = eh.war_request_handler
		tab.Log.entryAdded = eh.war_request_fetch_handler
		tab.start()

		# Set user agent: remove "headless" from the user agent string
		user_agent = tab.Browser.getVersion()["userAgent"].replace("Headless", "")
		tab.Network.setUserAgentOverride(userAgent=user_agent)
		tab.Network.setExtraHTTPHeaders(headers={"accept-language": "en-US,en;q=0.8"})

		# Activate all needed features
		tab.Runtime.enable()
		tab.Network.enable()
		tab.Page.enable()
		tab.Log.enable()

		tab.Network.clearBrowserCache()
		tab.Network.clearBrowserCookies()
		tab.Page.addScriptToEvaluateOnNewDocument(source=PageEvaluator.JAVASCRIPT)

		try:
			with ScannerTimeout(40):
				# Use the ScannerTimeout to force the tab to be stopped after a maximum of 40 seconds. This is needed if
				# a website does not react or when it blocks the scanner for a potentially unknown reason.

				# navigate to page
				tab.Page.navigate(url=url, _timeout=self._timeout)

				# wait for loading
				tab.wait(self._tab_wait_time)
				# simulate scrolling on page
				self._simulate_page_interaction(tab)
		except ScannerTimeoutError:
			# The scan took longer than expected
			# Do not raise the timeout since there can be data that was collected and the only problem was that the
			logging.error(f"There was a ScannerTimeout at {url}. The data collected so far will be saved.")
		# All other exceptions are raised to the calling function
		finally:
			# Close the tab properly even if an exception (e.g. timeout) occurs.
			# stop the tab (stop handle events and stop recv message from chrome)
			tab.stop()
			# close tab
			browser.close_tab(tab)

		# return results
		results = {
			"url": url,
			"scanTime": int(time.time()),
			"postMessages": eh.get_post_messages(),
			"sendMessages": eh.get_send_messages(),
			"portPostMessages": eh.get_port_post_messages(),
			"connects": eh.get_connects(),
			"warRequests": eh.get_war_requests()
		}
		return results

	def _simulate_page_interaction(self, tab):
		"""
		Scroll on page to simulate user interaction.
		This method is adapted from Privacyscore. https://github.com/PrivacyScore/privacyscanner
		"""
		layout = tab.Page.getLayoutMetrics()
		height = layout['contentSize']['height']
		viewport_height = layout['visualViewport']['clientHeight']
		viewport_width = layout['visualViewport']['clientWidth']
		x = random.randint(0, viewport_width - 1)
		y = random.randint(0, viewport_height - 1)
		# Avoid scrolling too far, since some sites load the start page
		# when scrolling to the bottom (e.g. sueddeutsche.de)
		max_scrolldown = random.randint(int(height / 2.5), int(height / 1.5))
		last_page_y = 0
		while True:
			distance = random.randint(100, 300)
			tab.Input.dispatchMouseEvent(
				type='mouseWheel', x=x, y=y, deltaX=0, deltaY=distance)
			layout = tab.Page.getLayoutMetrics()
			page_y = layout['visualViewport']['pageY']
			# We scroll down until we have reached max_scrolldown, which was
			# obtained in the beginning. This prevents endless scrolling for
			# sites that dynamically load content (and therefore change their
			# height). In addition we check if the page indeed scrolled; this
			# prevents endless scrolling in case the content's height has
			# decreased.
			if page_y + viewport_height >= max_scrolldown or page_y <= last_page_y:
				break
			last_page_y = page_y
			tab.wait(random.uniform(0.050, 0.150))
