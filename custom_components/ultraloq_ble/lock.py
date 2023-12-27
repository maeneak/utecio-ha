"""Lock platform for Ultraloq integration."""
from __future__ import annotations

from typing import Any

from utecio.ble.lock import UtecBleLock

from homeassistant.components import bluetooth
from homeassistant.components.lock import LockEntity, LockEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_LOCKED, STATE_LOCKING, STATE_UNLOCKED
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, UL_COORDINATOR
from .coordinator import UltraloqDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set Up Ultraloq Lock Entities."""

    coordinator: UltraloqDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        UL_COORDINATOR
    ]

    entities = []

    for lock in coordinator.data:
        add = UtecLock(coordinator, lock)
        entities.append(add)

    async_add_entities(entities)


class UtecLock(CoordinatorEntity, LockEntity):
    """Representation of Ultraloq Device."""

    def __init__(self, coordinator, lock: UtecBleLock) -> None:
        """Initialize the Lock."""
        super().__init__(coordinator)
        self.lock: UtecBleLock = lock
        mac_uuid = bluetooth.async_ble_device_from_address(
            coordinator.hass, self.lock.mac_uuid
        )
        self.lock.mac_uuid = mac_uuid if mac_uuid else self.lock.mac_uuid
        if self.lock.wurx_uuid:
            wurx_uuid = bluetooth.async_ble_device_from_address(
                coordinator.hass, self.lock.wurx_uuid
            )
            self.lock.wurx_uuid = wurx_uuid if wurx_uuid else self.lock.wurx_uuid

    # @property
    # def device_info(self) -> dict[str, Any]:
    #     """Return device registry information for this entity."""

    #     return self.lock.config

    @property
    def unique_id(self) -> str:
        """Sets unique ID for this entity."""

        return str(self.lock.mac_uuid) + "_" + self.lock.model

    @property
    def name(self) -> str:
        """Return name of the entity."""

        return str(self.lock.name)

    async def async_lock(self, **kwargs):
        """Lock the lock."""
        await self.lock.lock()
        self._attr_is_locked = True

    async def async_unlock(self, **kwargs):
        """Unlock the lock."""
        await self.lock.unlock()
        self._attr_is_locked = False
