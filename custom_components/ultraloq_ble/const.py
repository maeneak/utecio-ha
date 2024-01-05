""" Constants for Whistle """

import asyncio
import logging

from aiohttp.client_exceptions import ClientConnectionError

from homeassistant.const import Platform

LOGGER = logging.getLogger(__package__)

DEFAULT_SCAN_INTERVAL = 180
DOMAIN = "ultraloq_ble"
PLATFORMS = [Platform.LOCK]

DEFAULT_NAME = "Ultraloq Bluetooth"
TIMEOUT = 20

UL_ERRORS = (asyncio.TimeoutError, ClientConnectionError)

CONF_ZONE_METHOD = "zone_method"
DEFAULT_ZONE_METHOD = "Utec"
ZONE_METHODS = ["Utec", "Home Assistant"]

UPDATE_LISTENER = "update_listener"
UTEC_LOCKDATA = "utec_data"
