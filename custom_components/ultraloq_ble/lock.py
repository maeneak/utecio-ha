"""Lock platform for Ultraloq integration."""
from __future__ import annotations

from typing import Any
from datetime import timedelta

from bleak.backends.device import BLEDevice
from utecio.lock import UtecBleLock

from homeassistant.components import bluetooth
from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later

from .const import DOMAIN, UTEC_LOCKDATA, DEFAULT_SCAN_INTERVAL, LOGGER


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set Up Ultraloq Lock Entities."""

    data: list[UtecBleLock] = hass.data[DOMAIN][entry.entry_id][UTEC_LOCKDATA]
    scan_interval = timedelta(
        seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    entities = []

    for lock in data:
        add = UtecLock(hass, lock, scan_interval=scan_interval)
        entities.append(add)

    async_add_entities(new_entities=entities)


class UtecLock(LockEntity):
    """Representation of Ultraloq Device."""

    def __init__(
        self, hass: HomeAssistant, lock: UtecBleLock, scan_interval: timedelta
    ) -> None:
        """Initialize the Lock."""
        super().__init__()
        self.lock: UtecBleLock = lock
        self._attr_is_locked = True
        self.lock.async_device_callback = self.async_device_callback
        self.scaninterval = scan_interval
        self.update_track = None

    @property
    def should_poll(self) -> bool:
        return False

    async def async_device_callback(self, device: str) -> BLEDevice | Any:
        """Return BLEDevice from HA bleak instance if available."""
        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, device, connectable=True
        )
        return ble_device if ble_device else device

    # @property
    # def device_info(self) -> dict[str, Any]:
    #     """Return device registry information for this entity."""

    #     return self.lock.config

    @property
    def unique_id(self) -> str:
        """Sets unique ID for this entity."""

        return "ul_" + device_registry.format_mac(self.lock.mac_uuid)

    @property
    def name(self) -> str:
        """Return name of the entity."""

        return self.lock.name

    async def async_added_to_hass(self):
        self.update_track = async_call_later(
            self.hass, timedelta(seconds=2), lambda Now: self.request_update()
        )

    async def async_will_remove_from_hass(self):
        if self.update_track:
            self.update_track()

    def request_update(self):
        if self.update_track:
            self.update_track()

        if self.enabled and self.hass and not self._update_staged:
            self.schedule_update_ha_state(force_refresh=True)
            self.update_track = async_call_later(
                self.hass, self.scaninterval, lambda Now: self.request_update()
            )

    async def async_update(self, **kwargs):
        """Update the lock."""
        LOGGER.debug("Updating %s with scan interval: %s", self.name, self.scaninterval)
        await self.lock.update()

    async def async_lock(self, **kwargs):
        """Lock the lock."""
        self._attr_is_locked = True
        await self.lock.lock()
        self.schedule_update_ha_state(force_refresh=False)

    async def async_unlock(self, **kwargs):
        """Unlock the lock."""
        self._attr_is_locked = False
        await self.lock.unlock()
        self.schedule_update_ha_state(force_refresh=False)
        async_call_later(
            self.hass,
            timedelta(seconds=self.lock.autolock_time),
            lambda Now: self._set_state_locked(),
        )

    def _set_state_locked(self):
        LOGGER.debug("Autolock %s", self.name)
        self._attr_is_locked = True
        self.schedule_update_ha_state(force_refresh=False)
