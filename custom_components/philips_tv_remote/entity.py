"""Shared base entity for the Philips TV Remote integration."""

from __future__ import annotations

from homeassistant.helpers.device_info import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PhilipsTVDataUpdateCoordinator


class PhilipsTVEntity(CoordinatorEntity[PhilipsTVDataUpdateCoordinator]):
    """Read projection over the coordinator's PhilipsTV client."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: PhilipsTVDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        system = coordinator.system or {}
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(coordinator.unique_id))},
            manufacturer="Philips",
            model=system.get("model"),
            name=system.get("name") or "Philips TV",
            serial_number=system.get("serialnumber"),
        )

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success
