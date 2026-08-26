# Dockerfile for lab IPX DRA (freeDiameter)
# MOCK: freeDiameter DRA/DEA. Production: commercial IPX DRA. Not a SEPP.
# Do not bind-mount this directory over /etc/freeDiameter (hides package files).

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        freediameter \
        freediameter-extensions \
        ca-certificates \
        findutils \
    && rm -rf /var/lib/apt/lists/*

COPY dra.conf.template rt.conf.template /opt/ntn-lab/freeDiameter/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /opt/ntn-lab/freeDiameter
EXPOSE 3868/tcp 3868/sctp 3869/tcp

ENTRYPOINT ["/entrypoint.sh"]
