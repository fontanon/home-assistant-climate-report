FROM python:3.13-alpine

ARG BUILD_ARCH
ARG BUILD_VERSION

COPY app /opt/climate-report/app
COPY templates /opt/climate-report/templates

CMD ["python3", "-u", "/opt/climate-report/app/main.py"]

LABEL \
  io.hass.name="Climate Report" \
  io.hass.description="Weekly indoor temperature and humidity reports from Home Assistant statistics" \
  io.hass.type="app" \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.arch="${BUILD_ARCH}"
