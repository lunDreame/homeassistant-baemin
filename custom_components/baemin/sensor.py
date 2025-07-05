"""Sensor platform for Baemin."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription

from .const import DOMAIN, LOGGER
from .device import BaeminDevice
from .baemin_api import BaeminApi


@dataclass(frozen=True, kw_only=True)
class BaeminSensorEntityDescription(SensorEntityDescription):
    """Describes Baemin sensor entity."""
    transph_fn: Callable[..., dict]
    value_fn: Callable[..., str]
    sensor_data: Callable[..., dict | list]
    sensor_name: str

SENSORS: tuple[BaeminSensorEntityDescription, ...] = (
    BaeminSensorEntityDescription(
        key="favaddr",
        has_entity_name=True,
        icon=None,
        device_class=None,
        translation_key="favaddr",
        transph_fn=lambda data: {"title": data["address"]["title"] if data.get("nickName", "") == "" else data["nickName"]},
        value_fn=lambda
            data: f"{data['address']['sido']} {data['address']['gugun']} {data['address']['road']} {data['address']['detail']}",
        sensor_data=lambda api: api.data.bamin_address["favorite"],
        sensor_name="주소"
    ),
    BaeminSensorEntityDescription(
        key="noraddr",
        has_entity_name=True,
        icon=None,
        device_class=None,
        translation_key="noraddr",
        transph_fn=lambda data: {"title": data.get("nickName", data["address"]["title"])},
        value_fn=lambda
            data: f"{data['address']['sido']} {data['address']['gugun']} {data['address']['road']} {data['address']['detail']}",
        sensor_data=lambda api: api.data.bamin_address["normal"],
        sensor_name="주소"
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    api: BaeminApi = hass.data[DOMAIN][entry.entry_id]

    entities: list[BaeminSensorList | BaeminSensor] = []

    for sensor in SENSORS:
        sensor_data = sensor.sensor_data(api)
        if isinstance(sensor_data, list):
            for data in sensor_data:
                entities.append(BaeminSensorList(api, sensor, data))
        else:
            entities.append(BaeminSensor(api, sensor))

    if entities:
        async_add_entities(entities)


class BaeminSensorList(BaeminDevice, SensorEntity):
    """Representation of a Baemin sensor."""

    def __init__(self, api: BaeminApi, description: BaeminSensorEntityDescription, data: dict) -> None:
        """Initialize the sensor."""
        super().__init__(api, description)
        self.entity_description = description
        self.translation_placeholders = description.transph_fn(data)
        self.unique_id = f"{api.entry.unique_id}_{description.key}_{self.translation_placeholders['title']}"
        self.data = data

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        return self.description.value_fn(self.data)


class BaeminSensor(BaeminDevice, SensorEntity):
    """Representation of a Baemin sensor."""

    def __init__(self, api: BaeminApi, description: BaeminSensorEntityDescription) -> None:
        """Initialize the sensor."""
        super().__init__(api, description)
        self.entity_description = description

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        return self.description.sensor_data(self.api)
