"""Sensor platform for ultraloq_ble."""
from __future__ import annotations

from homeassistant.components.sensor import  SensorEntityDescription
from homeassistant.components.lock import LockEntity, LockEntityDescription

from .const import DOMAIN
from .coordinator import UltraloqBleDataUpdateCoordinator
from .entity import IntegrationUltraloqEntity

ENTITY_DESCRIPTIONS = (
    LockEntityDescription(
        key="ultraloq_ble",
        name="Ultraloq Lock",
        icon="mdi:lock-outline",
    ),
)

async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the lock platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices(
        IntegrationUltraloqLock(
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )

class IntegrationUltraloqLock(IntegrationUltraloqEntity, LockEntity):
    """ultraloq_ble Sensor class."""

    def __init__(
        self,
        coordinator: UltraloqBleDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self.name = "Test"
        self.is_locked = True

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._id

    @property
    def name(self):
        """Return the name of the lock."""
        return self._name

    @property
    def is_locked(self):
        """Return true if lock is locked."""
        return self._is_locked

    async def async_lock(self, **kwargs):
        """Lock the lock."""
        # Implement the logic to lock the physical/digital lock
        # Update self._is_locked and perform the lock operation
        self._is_locked = True
        # Your code to perform the lock operation goes here

    async def async_unlock(self, **kwargs):
        """Unlock the lock."""
        # Implement the logic to unlock the physical/digital lock
        # Update self._is_locked and perform the unlock operation
        self._is_locked = False