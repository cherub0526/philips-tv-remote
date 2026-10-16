"""Ambilight style selector for a Philips TV."""

from __future__ import annotations

from typing import TypedDict

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import PhilipsTVConfigEntry, PhilipsTVDataUpdateCoordinator
from .entity import PhilipsTVEntity

OFF_LABEL = "Off"

_STYLE_LABELS = {
    "FOLLOW_VIDEO": "Follow Video",
    "FOLLOW_AUDIO": "Follow Audio",
    "FOLLOW_COLOR": "Follow Color",
}

# Acronyms that title-casing would otherwise mangle (VU -> "Vu", ISF -> "Isf").
_TOKEN_OVERRIDES = {"VU": "VU", "ISF": "ISF"}


class AmbilightCurrentConfiguration(TypedDict, total=False):
    """Payload for the Ambilight current-configuration endpoint."""

    styleName: str
    menuSetting: str


def _friendly_style(style_name: str) -> str:
    return _STYLE_LABELS.get(style_name, style_name.replace("_", " ").title())


def _friendly_token(token: str) -> str:
    parts = [_TOKEN_OVERRIDES.get(part, part.title()) for part in token.split("_")]
    return " ".join(parts)


def _build_option_map(
    styles: dict,
) -> dict[str, AmbilightCurrentConfiguration]:
    """Map each selectable label to the config that activates it."""
    options: dict[str, AmbilightCurrentConfiguration] = {
        OFF_LABEL: {"styleName": "OFF"}
    }
    for key, config in styles.items():
        style_name = config.get("styleName") or key
        if style_name == "OFF":
            continue
        menu_settings = config.get("menuSettings")
        if menu_settings:
            friendly = _friendly_style(style_name)
            for menu_setting in menu_settings:
                label = f"{friendly}: {_friendly_token(menu_setting)}"
                options[label] = {
                    "styleName": style_name,
                    "menuSetting": menu_setting,
                }
            continue
        if style_name == "LOUNGE":
            options["Lounge"] = {"styleName": "LOUNGE"}
            continue
        if style_name.startswith("GAMEBAR_STYLE_"):
            number = style_name.rsplit("_", 1)[-1]
            options[f"Game {number}"] = {"styleName": style_name}
            continue
        # Remaining styles (MANUAL, EXPERT, GRID, FLAG, APP, and any other
        # bare style) need extra parameters, so they are not one-shot options.
    return options


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PhilipsTVConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    # More than the always-present OFF style means the TV has real Ambilight.
    if len(coordinator.api.ambilight_styles) > 1:
        async_add_entities([PhilipsTVAmbilight(coordinator)])


class PhilipsTVAmbilight(PhilipsTVEntity, SelectEntity):
    """Ambilight style, exposed as a one-shot style selector."""

    _attr_name = "Ambilight"

    def __init__(self, coordinator: PhilipsTVDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.unique_id}_ambilight"
        self._options = _build_option_map(coordinator.api.ambilight_styles)

    @property
    def options(self) -> list[str]:
        return list(self._options)

    @property
    def current_option(self) -> str | None:
        api = self.coordinator.api
        config = api.ambilight_current_configuration
        if (
            config is None
            or config.get("styleName") == "OFF"
            or api.ambilight_power != "On"
        ):
            return OFF_LABEL
        for label, candidate in self._options.items():
            if candidate["styleName"] != config.get("styleName"):
                continue
            candidate_menu = candidate.get("menuSetting")
            if candidate_menu is not None and candidate_menu != config.get(
                "menuSetting"
            ):
                continue
            return label
        return None

    async def async_select_option(self, option: str) -> None:
        api = self.coordinator.api
        config = self._options[option]
        if option == OFF_LABEL:
            await api.setAmbilightCurrentConfiguration({"styleName": "OFF"})
        else:
            await api.setAmbilightPower("On")
            await api.setAmbilightCurrentConfiguration(config)
        await self.coordinator.async_request_refresh()
