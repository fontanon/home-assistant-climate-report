from homeassistant.components.button import ButtonEntity

from .entity import ClimateReportEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([GenerateReportButton(entry)])


class GenerateReportButton(ClimateReportEntity, ButtonEntity):
    _attr_translation_key = "generate"
    _attr_icon = "mdi:file-chart-outline"

    def __init__(self, entry):
        super().__init__(entry, "generate")

    async def async_press(self) -> None:
        await self.hass.services.async_call(
            "hassio",
            "addon_stdin",
            {"addon": self.entry.data["addon_slug"], "input": {"command": "generate"}},
            blocking=False,
        )
