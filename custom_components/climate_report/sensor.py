from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.const import PERCENTAGE, UnitOfTemperature

from .entity import ClimateReportEntity


@dataclass(frozen=True, kw_only=True)
class ClimateSensorDescription(SensorEntityDescription):
    summary_key: str


SENSORS = (
    ClimateSensorDescription(key="mean_temperature", translation_key="mean_temperature", summary_key="mean_temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE),
    ClimateSensorDescription(key="mean_humidity", translation_key="mean_humidity", summary_key="mean_humidity", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.HUMIDITY),
    ClimateSensorDescription(key="temperature_year_delta", translation_key="temperature_year_delta", summary_key="temperature_year_delta", native_unit_of_measurement=UnitOfTemperature.CELSIUS),
    ClimateSensorDescription(key="humidity_year_delta", translation_key="humidity_year_delta", summary_key="humidity_year_delta", native_unit_of_measurement="pp"),
    ClimateSensorDescription(key="coverage", translation_key="coverage", summary_key="coverage", native_unit_of_measurement=PERCENTAGE),
    ClimateSensorDescription(key="last_report", translation_key="last_report", summary_key="generated_at", device_class=SensorDeviceClass.TIMESTAMP),
)


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(ClimateReportSensor(entry, description) for description in SENSORS)


class ClimateReportSensor(ClimateReportEntity, SensorEntity):
    def __init__(self, entry, description):
        super().__init__(entry, description.key)
        self.entity_description = description

    @property
    def native_value(self):
        value = self.summary.get(self.entity_description.summary_key)
        if self.entity_description.key == "coverage" and value is not None:
            return round(float(value) * 100, 1)
        if self.entity_description.key == "last_report" and value is not None:
            return datetime.fromisoformat(value)
        return value

    @property
    def extra_state_attributes(self):
        return self.summary if self.entity_description.key == "last_report" else None
