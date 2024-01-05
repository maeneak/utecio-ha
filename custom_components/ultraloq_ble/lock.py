"""Lock platform for Ultraloq integration."""
from __future__ import annotations

from typing import Any
from datetime import timedelta

from bleak.backends.device import BLEDevice
from utecio.lock import UtecBleLock
from utecio.enums import ULLockStatus
from .const import DEFAULT_SCAN_INTERVAL

from homeassistant.components import bluetooth
from homeassistant.components.lock import LockEntity, LockEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_LOCKED, STATE_LOCKING, STATE_UNLOCKED
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, UTEC_LOCKDATA

SCAN_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set Up Ultraloq Lock Entities."""

    data: list[UtecBleLock] = hass.data[DOMAIN][entry.entry_id][UTEC_LOCKDATA]

    entities = []

    for lock in data:
        add = UtecLock(lock)
        entities.append(add)

    async_add_entities(entities)


class UtecLock(LockEntity):
    """Representation of Ultraloq Device."""

    def __init__(self, lock: UtecBleLock) -> None:
        """Initialize the Lock."""
        self.lock: UtecBleLock = lock
        self._attr_is_locked = True
        self.lock.async_device_callback = self.async_device_callback

    async def async_device_callback(self, device: str) -> BLEDevice | Any:
        """Return BLEDevice from HA bleak instance if available."""
        ble_device = bluetooth.async_ble_device_from_address(self.hass, device)
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

    async def async_update(self, **kwargs):
        """Update the lock."""
        await self.lock.update()
        self._attr_is_locked = self.lock.lock_status = ULLockStatus.LOCKED

    async def async_lock(self, **kwargs):
        """Lock the lock."""
        self._attr_is_locked = True
        self.schedule_update_ha_state(force_refresh=False)
        await self.lock.lock()

    async def async_unlock(self, **kwargs):
        """Unlock the lock."""
        self._attr_is_locked = False
        self.schedule_update_ha_state(force_refresh=False)
        await self.lock.unlock()
