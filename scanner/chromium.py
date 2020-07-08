import json
import logging
import os
import subprocess
import tempfile
import time
from contextlib import suppress
from pathlib import Path

import psutil
import pychrome
from urllib3.exceptions import MaxRetryError
from requests.exceptions import ConnectionError
from exceptions import ChromeBrowserStartupError

"""
The code in this file is adapted from PrivacyScore.
https://github.com/PrivacyScore/privacyscanner/blob/master/privacyscanner/scanmodules/chromedevtools/chromescan.py
"""

CHROME_OPTIONS = [
    # Disable various background network services, including extension
    # updating, safe browsing service, upgrade detector, translate, UMA
    '--disable-background-networking',

    # Disable fetching safebrowsing lists. Otherwise requires a 500KB
    # download immediately after launch. This flag is likely redundant
    # if disable-background-networking is on
    '--safebrowsing-disable-auto-update',

    # Disable syncing to a Google account
    '--disable-sync',

    # Disable reporting to UMA, but allows for collection
    '--metrics-recording-only',

    # Disable installation of default apps on first run
    '--disable-default-apps',

    # Mute any audio
    '--mute-audio',

    # Skip first run wizards
    '--no-first-run',

    # Disable timers being throttled in background pages/tabs
    '--disable-background-timer-throttling',

    # Disables client-side phishing detection. Likely redundant due to
    # the safebrowsing disable
    '--disable-client-side-phishing-detection',

    # Disable popup blocking
    '--disable-popup-blocking',

    # Reloading a page that came from a POST normally prompts the user.
    '--disable-prompt-on-repost',

    # Disable a few things considered not appropriate for automation.
    # (includes password saving UI, default browser prompt, etc.)
    '--enable-automation',

    # Avoid potential instability of using Gnome Keyring or KDE wallet.
    # crbug.com/571003
    '--password-store=basic',

    # Use mock keychain on Mac to prevent blocking permissions dialogs
    '--use-mock-keychain',

    # Disable dialog to update components
    '--disable-component-update',

    # Do autoplay everything.
    '--autoplay-policy=no-user-gesture-required',

    # Disable notifications (Web Notification API)
    '--disable-notifications',

    # Disable the hang monitor
    '--disable-hang-monitor',

    # Disable GPU acceleration
    '--disable-gpu',

    # Run headless
    '--headless',

    # Additional parameters for the study

    # Disable CORS protection to be able to log XHR requests
    '--disable-web-security',

    # Disable isolation
    '--disable-site-isolation-trials',
    '--disable-features=IsolateOrigins,site-per-process'
]


PREFS = {
    'profile': {
        'content_settings': {
            'exceptions': {
                # Allow flash for all sites
                'plugins': {
                    'http://*,*': {
                        'setting': 1
                    },
                    'https://*,*': {
                        'setting': 1
                    }
                }
            }
        }
    },
    'session': {
        'restore_on_startup': 4,  # 4 = Use startup_urls
        'startup_urls': ['about:blank']
    }
}


class ChromeBrowser:
    def __init__(self, log_file_path, debugging_port=9222, chrome_executable='chromium-browser'):
        self._log_file_path = log_file_path
        self._debugging_port = debugging_port
        self._chrome_executable = chrome_executable

        self._temp_dir = tempfile.TemporaryDirectory()
        temp_dirname = self._temp_dir.name
        user_data_dir = Path(temp_dirname) / 'chrome-profile'
        user_data_dir.mkdir()
        default_dir = user_data_dir / 'Default'
        default_dir.mkdir()
        with (default_dir / 'Preferences').open('w') as f:
            json.dump(PREFS, f)
        self._start_chrome(user_data_dir)

    def stop(self):
        self._kill_everything()
        self._temp_dir.cleanup()

    def get_browser(self):
        return self.browser

    def _start_chrome(self, user_data_dir):
        extra_opts = [
            '--remote-debugging-port={}'.format(self._debugging_port),
            '--user-data-dir={}'.format(user_data_dir),
        ]
        command = [self._chrome_executable] + CHROME_OPTIONS + extra_opts
        logging.info(command)

        # ENV: https://bugs.chromium.org/p/chromedriver/issues/detail?id=1699
        os.environ["DBUS_SESSION_BUS_ADDRESS"] = "/dev/null"

        # Log stderr to error_log
        error_log = open(self._log_file_path, 'w+')
        self._p = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=error_log)

        # Wait until Chrome is started
        max_tries = 200
        while max_tries > 0:
            try:
                self.browser = pychrome.Browser(url='http://127.0.0.1:{}'.format(self._debugging_port))
                break
            except (MaxRetryError, ConnectionError):
                time.sleep(0.2)
            max_tries -= 1
        else:
            raise ChromeBrowserStartupError('Could not create pychrome browser instance.')

        # Wait until Chrome is ready
        max_tries = 500
        while max_tries > 0:
            try:
                version = self.browser.version()
                logging.info(version)
                break
            except (MaxRetryError, ConnectionError):
                time.sleep(0.2)
            max_tries -= 1
        else:
            raise ChromeBrowserStartupError('Could not connect to Chrome')

    def _kill_everything(self, timeout=3, only_children=False):
        pid = self._p.pid
        # First, we take care of the children.
        procs = psutil.Process(pid).children()
        # Suspend first before sending SIGTERM to avoid thundering herd problems
        for p in procs:
            with suppress(psutil.NoSuchProcess):
                p.suspend()
        # Be nice. Ask them first to terminate, before we kill them.
        for p in procs:
            with suppress(psutil.NoSuchProcess):
                p.terminate()
        # This delivers the SIGTERM right after resuming, so no chance to
        # terminate by broken pipes etc. first.
        for p in procs:
            with suppress(psutil.NoSuchProcess):
                p.resume()
        gone, alive = psutil.wait_procs(procs, timeout=timeout)
        # They are still alive. Kill'em all. No mercy anymore.
        if alive:
            for p in alive:
                with suppress(psutil.NoSuchProcess):
                    p.kill()
            psutil.wait_procs(alive, timeout=timeout)
        if not only_children:
            # Time for pid to go ...
            with suppress(psutil.NoSuchProcess):
                p = psutil.Process(pid)
                p.terminate()
                with suppress(psutil.TimeoutExpired):
                    p.wait(timeout)
                if p.is_running():
                    p.kill()
                    with suppress(psutil.TimeoutExpired):
                        p.wait(timeout)
