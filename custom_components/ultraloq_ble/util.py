"""Utilities for Ultraloq Bluetooth Integration."""
from __future__ import annotations

from utecio.api import UtecClient, InvalidCredentials

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import LOGGER, UL_ERRORS


async def async_validate_api(hass: HomeAssistant, email: str, password: str) -> bool:
    """Get data from API."""

    client = UtecClient(
        email=email, password=password, session=async_get_clientsession(hass)
    )

    try:
        await client._fetch_token()
        await client._login()
    except UL_ERRORS as err:
        LOGGER.error(f"Failed to get information from UTEC servers: {err}")
        raise ConnectionError from err
    except InvalidCredentials as err:
        LOGGER.error(f"Failed to login to UTEC servers: {err}")
        raise InvalidCredentials

    locks: list = await client.get_json()
    if not locks:
        LOGGER.error("Could not retrieve any locks from Utec servers")
        raise NoDevicesError
    else:
        return True


class NoDevicesError(Exception):
    """No Locks from UTECIO API."""
