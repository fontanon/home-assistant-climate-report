FROM ghcr.io/home-assistant/base:latest

ARG BUILD_ARCH
ARG BUILD_VERSION

RUN apk add --no-cache python3

COPY rootfs /
COPY app /opt/weekly-climate-report/app
COPY templates /opt/weekly-climate-report/templates

RUN chmod a+x /etc/services.d/weekly-climate-report/run

LABEL \
  io.hass.name="Weekly Climate Report" \
  io.hass.description="Weekly room climate reports from Home Assistant statistics" \
  io.hass.type="app" \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.arch="${BUILD_ARCH}"
