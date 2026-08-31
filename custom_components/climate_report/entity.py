from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_UPDATE


class ClimateReportEntity(Entity):
    _attr_has_entity_name = True

    def __init__(self, entry, key: str) -> None:
        self.entry = entry
        self.key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Climate Report",
            manufacturer="Climate Report",
            model="Home Assistant app",
        )

    @property
    def summary(self):
        return self.hass.data[DOMAIN][self.entry.entry_id]["summary"]

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_UPDATE, self._handle_update
            )
        )

    def _handle_update(self, entry_id: str) -> None:
        if entry_id == self.entry.entry_id:
            self.async_write_ha_state()
