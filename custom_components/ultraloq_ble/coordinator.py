"""DataUpdateCoordinator for the Ultraloq integration."""
from __future__ import annotations

from datetime import timedelta

from .const import LOGGER

from utecio.client import UtecClient


from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER

class UltraloqDataUpdateCoordinator(DataUpdateCoordinator):
    """Ultraloq Data Update Coordinator."""

    data: []

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the Ultraloq coordinator."""

        self.client = UtecClient(
            entry.data[CONF_EMAIL],
            entry.data[CONF_PASSWORD],
            session=async_get_clientsession(hass),
        )
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> list[UtecBleLock]:
        """Fetch data from UTEC."""

        try:
            data = await self.client.get_Ultraloq_data()
        except UltraloqAuthError as error:
            raise ConfigEntryAuthFailed from error
        except UltraloqError as error:
            raise UpdateFailed(error) from error
        except Exception as error:
            raise UpdateFailed(error) from error
        if not data.pets:
            raise UpdateFailed("No Pets found")
        return data
