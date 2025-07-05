"""Base class for Baemin devices."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.entity import Entity, DeviceInfo
from homeassistant.core import callback

from .const import DOMAIN, MANUFACTURER, MODEL, LOGGER
from .baemin_api import BaeminApi


class BaeminBase(Entity):
    """Base class for Baemin devices."""

    def __init__(self, api: BaeminApi, description) -> None:
        """Initialize the Baemin device."""
        self.api = api
        self.description = description

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry information for this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.api.entry.unique_id}_{self.description.sensor_name}")},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=self.description.sensor_name,
        )


class BaeminDevice(BaeminBase, Entity):
    """Base class for Baemin devices."""

    def __init__(self, api: BaeminApi, description) -> None:
        """Initialize the Baemin device."""
        super().__init__(api, description)

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return whether the entity registry is enabled."""
        return True

    async def async_added_to_hass(self):
        """Called when added to Hass."""

    async def async_will_remove_from_hass(self) -> None:
        """Called when removed from Hass."""

    @callback
    def async_restore_last_state(self, last_state) -> None:
        """Restore the last state."""

    @property
    def available(self) -> bool:
        """Return whether the device is available."""
        return True

    @property
    def should_poll(self) -> bool:
        """Return whether polling is needed."""
        return True
