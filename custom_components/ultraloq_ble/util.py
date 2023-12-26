"""Utilities for Ultraloq Bluetooth Integration."""
from __future__ import annotations

from utecio.client import UtecClient

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import LOGGER, TIMEOUT, UL_ERRORS


async def async_validate_api(hass: HomeAssistant, email: str, password: str) -> bool:
    """Get data from API."""

    client = UtecClient(
        email=email, password=password, session=async_get_clientsession(hass)
    )

    try:
        await client.login()
    except UL_ERRORS as err:
        LOGGER.error(f"Failed to get information from UTEC servers: {err}")
        raise ConnectionError from err

    locks: list = await client.get_all_devices()
    if not locks:
        LOGGER.error("Could not retrieve any locks from Utec servers")
        raise NoLocksError
    else:
        return True


class NoLocksError(Exception):
    """No Locks from UTECIO API."""
