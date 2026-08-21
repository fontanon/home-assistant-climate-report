FROM ghcr.io/home-assistant/base:latest

ARG BUILD_ARCH
ARG BUILD_VERSION

RUN apk add --no-cache python3

COPY rootfs /
COPY app /opt/climate-report/app
COPY templates /opt/climate-report/templates

RUN chmod a+x /etc/services.d/climate-report/run

LABEL \
  io.hass.name="Climate Report" \
  io.hass.description="Weekly indoor temperature and humidity reports from Home Assistant statistics" \
  io.hass.type="app" \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.arch="${BUILD_ARCH}"
