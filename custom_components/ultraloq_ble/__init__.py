"""Ultraloq Bluetooth Component."""
from __future__ import annotations

from utecio.api import UtecClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    LOGGER,
    PLATFORMS,
    UPDATE_LISTENER,
    UTEC_LOCKDATA,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Lock from a config entry."""

    client = UtecClient(
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
        session=async_get_clientsession(hass),
    )
    devices = await client.get_ble_devices()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {UTEC_LOCKDATA: devices}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    update_listener = entry.add_update_listener(async_update_options)
    hass.data[DOMAIN][entry.entry_id][UPDATE_LISTENER] = update_listener

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Ultraloq config entry."""

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        update_listener = hass.data[DOMAIN][entry.entry_id][UPDATE_LISTENER]
        update_listener()
        del hass.data[DOMAIN][entry.entry_id]
        if not hass.data[DOMAIN]:
            del hass.data[DOMAIN]
    return unload_ok


# async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
#     """ Migrate old entry. """

#     if entry.version in [1,2]:
#         if entry.version == 1:
#             email = entry.data[CONF_USERNAME]
#         else:
#             email = entry.data[CONF_EMAIL]
#         password = entry.data[CONF_PASSWORD]

#         LOGGER.debug(f'Migrate config entry unique id to {email}')
#         entry.version = 3

#         hass.config_entries.async_update_entry(
#             entry,
#             data={
#                 CONF_EMAIL: email,
#                 CONF_PASSWORD: password,
#             },
#             options={CONF_ZONE_METHOD: DEFAULT_ZONE_METHOD},
#             unique_id=email,
#         )
#     return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""

    await hass.config_entries.async_reload(entry.entry_id)
