"""Lock platform for Ultraloq integration."""
from __future__ import annotations
import asyncio

from typing import Any
from datetime import timedelta

from bleak.backends.device import BLEDevice
from utecio.ble.lock import UtecBleLock
from utecio.ble.device import UtecBleNotFoundError, UtecBleDeviceError

from homeassistant.components import bluetooth
from homeassistant.components.lock import (
    LockEntity,
    LockEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later

from .const import DOMAIN, UTEC_LOCKDATA, DEFAULT_SCAN_INTERVAL, LOGGER


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set Up Ultraloq Lock Entities."""

    data: list[UtecBleLock] = hass.data[DOMAIN][entry.entry_id][UTEC_LOCKDATA]
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    entities = []

    for lock in data:
        add = UtecLock(hass, lock, scan_interval=scan_interval)
        entities.append(add)
    async_add_entities(new_entities=entities)


class UtecLock(LockEntity):
    """Representation of Ultraloq Device."""

    _attr_supported_features = [LockEntityFeature.OPEN]

    def __init__(
        self, hass: HomeAssistant, lock: UtecBleLock, scan_interval: int
    ) -> None:
        """Initialize the Lock."""
        super().__init__()
        self.lock: UtecBleLock = lock
        self._attr_is_locked = True
        self.lock.async_bledevice_callback = self.async_bledevice_callback
        self.scaninterval = scan_interval
        self.update_track_cancel = None
        self._cancel_unavailable_track = None
        # uteclogger.setLevel(LOGGER.level)

    @property
    def should_poll(self) -> bool:
        """False if entity pushes its state to HA."""
        return False

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
        """Run when entity about to be added to hass."""
        address = self.lock.wurx_uuid if self.lock.wurx_uuid else self.lock.mac_uuid
        self.async_on_remove(
            bluetooth.async_track_unavailable(
                self.hass,
                self._unavailable_callback,
                address,
                connectable=True,
            )
        )
        self.async_on_remove(
            bluetooth.async_register_callback(
                self.hass,
                self._available_callback,
                {"address": address},
                bluetooth.BluetoothScanningMode.ACTIVE,
            )
        )
        self.schedule_update_lock_state(2)
        return await super().async_added_to_hass()

    async def async_will_remove_from_hass(self):
        """Run when entity will be removed from hass."""
        if self.update_track_cancel:
            self.update_track_cancel()
        return await super().async_will_remove_from_hass()

    async def async_bledevice_callback(self, device: str) -> BLEDevice | Any:
        """Return BLEDevice from HA bleak instance if available."""
        return bluetooth.async_ble_device_from_address(
            self.hass, device, connectable=True
        )

    @callback
    def _unavailable_callback(self, info: bluetooth.BluetoothServiceInfoBleak) -> None:
        self.update_track_cancel()
        LOGGER.debug("%s unavailable.", self.lock.name)
        self._attr_available = False
        self.async_write_ha_state()

    @callback
    def _available_callback(
        self,
        info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        self._attr_available = True
        self.async_write_ha_state()
        self.schedule_update_lock_state(2)

    def schedule_update_lock_state(self, offset: int):
        """Schedule an update from the lock."""
        if self.update_track_cancel:
            self.update_track_cancel()
        if self._attr_available:
            self.update_track_cancel = async_call_later(
                self.hass,
                timedelta(seconds=offset),
                lambda Now: asyncio.run(self.request_update()),
            )

    async def request_update(self):
        """Request an update of the lock state."""
        if self.update_track_cancel:
            self.update_track_cancel()

        if self.enabled and self.hass and not self._update_staged:
            self.schedule_update_ha_state(force_refresh=True)
            self.schedule_update_lock_state(self.scaninterval)

    async def async_update(self, **kwargs):
        """Update the lock."""
        LOGGER.debug("Updating %s with scan interval: %s", self.name, self.scaninterval)
        try:
            await self.lock.async_update_status()
            LOGGER.info("(%s) Updated.", self.name)
        except (UtecBleDeviceError, UtecBleNotFoundError) as e:
            LOGGER.error(e)

    async def async_lock(self, **kwargs):
        """Lock the lock."""
        try:
            await self.lock.async_lock()
            self._attr_is_locked = True
            self.async_write_ha_state()
        except (UtecBleDeviceError, UtecBleNotFoundError) as e:
            LOGGER.error(e)

    async def async_unlock(self, **kwargs):
        """Unlock the lock."""
        try:
            await self.lock.async_unlock()
            self._attr_is_locked = False
            self.schedule_update_ha_state(force_refresh=False)
            if self.lock.capabilities.autolock:
                async_call_later(
                    self.hass,
                    timedelta(seconds=self.lock.autolock_time),
                    lambda Now: self._set_state_locked(),
                )
        except (UtecBleDeviceError, UtecBleNotFoundError) as e:
            LOGGER.error(e)

    async def async_open(self, **kwargs: Any) -> None:
        """Open the door latch."""
        return await self.async_unlock(**kwargs)

    def _set_state_locked(self):
        LOGGER.debug("Autolock %s", self.name)
        self._attr_is_locked = True
        self.async_write_ha_state()
