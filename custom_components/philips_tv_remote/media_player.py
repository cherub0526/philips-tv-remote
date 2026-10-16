"""Media player entity for a Philips TV."""

from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import PhilipsTVConfigEntry, PhilipsTVDataUpdateCoordinator
from .entity import PhilipsTVEntity

SUPPORT_PHILIPS_TV = (
    MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.STOP
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PhilipsTVConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([PhilipsTVMediaPlayer(entry.runtime_data)])


def _application_label(application: dict) -> str | None:
    return application.get("label") or application.get("name")


class PhilipsTVMediaPlayer(PhilipsTVEntity, MediaPlayerEntity):
    """The TV itself, projected as a media player."""

    _attr_name = None
    _attr_device_class = MediaPlayerDeviceClass.TV
    _attr_supported_features = SUPPORT_PHILIPS_TV

    def __init__(self, coordinator: PhilipsTVDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = str(coordinator.unique_id)

    @property
    def state(self) -> MediaPlayerState:
        if self.coordinator.api.powerstate == "On":
            return MediaPlayerState.ON
        return MediaPlayerState.OFF

    @property
    def volume_level(self) -> float | None:
        return self.coordinator.api.volume

    @property
    def is_volume_muted(self) -> bool | None:
        return self.coordinator.api.muted

    @property
    def source_list(self) -> list[str]:
        api = self.coordinator.api
        names = [
            label
            for app in (api.applications or {}).values()
            if (label := _application_label(app))
        ]
        names += [
            name
            for source in (api.sources or {}).values()
            if (name := source.get("name"))
        ]
        return names

    @property
    def source(self) -> str | None:
        api = self.coordinator.api
        current = api.application
        if current:
            for app in (api.applications or {}).values():
                if app.get("intent") == current:
                    return _application_label(app)
        if api.source_id and api.sources:
            source = api.sources.get(api.source_id)
            if source:
                return source.get("name")
        return None

    async def async_select_source(self, source: str) -> None:
        api = self.coordinator.api
        for app in (api.applications or {}).values():
            if _application_label(app) == source:
                await api.setApplication(app.get("intent"))
                await self.coordinator.async_request_refresh()
                return
        for source_id, candidate in (api.sources or {}).items():
            if candidate.get("name") == source:
                await api.setSource(source_id)
                await self.coordinator.async_request_refresh()
                return

    async def async_turn_on(self) -> None:
        await self.coordinator.turn_on()

    async def async_turn_off(self) -> None:
        await self.coordinator.turn_off()

    async def async_set_volume_level(self, volume: float) -> None:
        await self.coordinator.api.setVolume(volume, self.coordinator.api.muted)
        await self.coordinator.async_request_refresh()

    async def async_mute_volume(self, mute: bool) -> None:
        await self.coordinator.api.setVolume(self.coordinator.api.volume, mute)
        await self.coordinator.async_request_refresh()

    async def async_volume_up(self) -> None:
        await self.coordinator.api.sendKey("VolumeUp")
        await self.coordinator.async_request_refresh()

    async def async_volume_down(self) -> None:
        await self.coordinator.api.sendKey("VolumeDown")
        await self.coordinator.async_request_refresh()

    async def async_media_play(self) -> None:
        await self.coordinator.api.sendKey("PlayPause")
        await self.coordinator.async_request_refresh()

    async def async_media_pause(self) -> None:
        await self.coordinator.api.sendKey("Pause")
        await self.coordinator.async_request_refresh()

    async def async_media_stop(self) -> None:
        await self.coordinator.api.sendKey("Stop")
        await self.coordinator.async_request_refresh()

    async def async_media_next_track(self) -> None:
        await self.coordinator.api.sendKey("Next")
        await self.coordinator.async_request_refresh()

    async def async_media_previous_track(self) -> None:
        await self.coordinator.api.sendKey("Previous")
        await self.coordinator.async_request_refresh()
