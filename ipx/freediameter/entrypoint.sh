#!/bin/sh
# freeDiameter DRA — do not bind-mount over /etc/freeDiameter (hides package .fdx paths).
set -eu
SRC="${FD_TEMPLATE_DIR:-/opt/ntn-lab/freeDiameter}"
RUNDIR=/run/freeDiameter
mkdir -p "$RUNDIR"

CONF="$RUNDIR/dra.conf"
RT="$RUNDIR/rt.conf"

if [ -f /templates/dra.conf.template ]; then
  SRC=/templates
fi
if [ -f "$SRC/dra.conf.template" ]; then
  cp "$SRC/dra.conf.template" "$CONF"
elif [ -f "$SRC/dra.conf" ]; then
  cp "$SRC/dra.conf" "$CONF"
else
  echo "ERROR: no dra.conf template in $SRC" >&2
  ls -la "$SRC" >&2 || true
  exec sleep infinity
fi

if [ -f "$SRC/rt.conf.template" ]; then
  cp "$SRC/rt.conf.template" "$RT"
elif [ -f "$SRC/rt.conf" ]; then
  cp "$SRC/rt.conf" "$RT"
else
  : > "$RT"
fi
# Comment-only lab template is not valid rt_default input (UNVERIFIED syntax).
if ! grep -qE '^[[:space:]]*[^#[:space:]]' "$RT" 2>/dev/null; then
  : > "$RT"
fi

# Debian/Ubuntu freeDiameter extensions live under /usr/lib, not /etc/freeDiameter.
FDX="$(find /usr/lib /usr/lib64 -name 'dbg_msg_dumps.fdx' 2>/dev/null | head -n1 || true)"
if [ -n "$FDX" ]; then
  FDXDIR="$(dirname "$FDX")"
  sed -i "s|LoadExtension = \"dbg_msg_dumps.fdx\"|LoadExtension = \"${FDXDIR}/dbg_msg_dumps.fdx\"|g" "$CONF"
  if [ -s "$RT" ]; then
    sed -i "s|LoadExtension = \"rt_default.fdx\" : \"/etc/freeDiameter/rt.conf\"|LoadExtension = \"${FDXDIR}/rt_default.fdx\" : \"${RT}\"|g" "$CONF"
  else
    sed -i '/rt_default/d' "$CONF"
  fi
fi

BIN=""
for b in freeDiameterd /usr/bin/freeDiameterd /usr/sbin/freeDiameterd; do
  if command -v "$b" >/dev/null 2>&1 || [ -x "$b" ]; then
    BIN="$b"
    break
  fi
done

if [ -z "$BIN" ]; then
  echo "ERROR: freeDiameterd not found; sleeping so sibling IPX services stay up." >&2
  exec sleep infinity
fi

echo "Starting $BIN -c $CONF"
if ! "$BIN" -c "$CONF"; then
  echo "ERROR: freeDiameterd exited; last conf:" >&2
  cat "$CONF" >&2 || true
  exec sleep infinity
fi
