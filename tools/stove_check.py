#!/usr/bin/env python3
"""Read-only LAN check of a TYWE1S pellet stove running stock Tuya firmware.

Prints the stove's datapoints decoded the same way the tuya-local profile in
../tuya-local/ maps them. Use it to confirm the enum strings your stove sends
before trusting the profile, and to confirm LAN control still works after the
stove's internet access is blocked.

Needs the device id and local key from your own Tuya account (tuya-local's
cloud-assisted setup shows both). Nothing is written to the stove.

    uv run --with tinytuya tools/stove_check.py            # one status read
    uv run --with tinytuya tools/stove_check.py --watch    # stream changes

Settings come from the environment (keep them out of git):
    STOVE_IP, STOVE_ID, STOVE_KEY, STOVE_VERSION (default 3.3)
"""

import argparse
import json
import os
import sys

import tinytuya

# DP 104 fault bitmap, from the repo's error-code table (sensor.yaml / README).
FAULTS = {
    1: "ESC2 protection sensor short",
    2: "ESO2 protection sensor open",
    4: "ESC1 exhaust sensor short (or overheat on P1)",
    8: "ESO1 exhaust sensor open",
    16: "ESC3 room sensor short",
    32: "ESO3 room sensor open",
    256: "MCU comms failed",
    2048: "E5 door open",
    4096: "E7 power was lost",
    16384: "E1 fire went out (out of pellets?)",
    32768: "E2 ignition failed",
}


def decode(dps):
    unit = dps.get("105", "F")
    lines = []
    if "1" in dps:
        lines.append(f"power (1)        : {'ON' if dps['1'] else 'OFF'}")
    if "4" in dps:
        lines.append(f"power level (4)  : {dps['4']!r}")
    if "101" in dps:
        lines.append(f"ECO mode (101)   : {dps['101']!r}")
    if "105" in dps:
        lines.append(f"temp unit (105)  : {dps['105']!r}")
    for dp, label in (("106", "set temp"), ("107", "room temp"),
                      ("108", "exhaust temp"), ("109", "protect temp")):
        if dp in dps:
            lines.append(f"{f'{label} ({dp})':<17}: {dps[dp]} {unit}")
    if "104" in dps:
        code = int(dps["104"])
        names = [n for bit, n in FAULTS.items() if code & bit]
        unknown = code & ~sum(FAULTS)
        if unknown:
            names.append(f"unknown bits 0x{unknown:x}")
        lines.append(f"fault (104)      : {code} {names or ['none']}")
    known = {"1", "4", "101", "104", "105", "106", "107", "108", "109"}
    extra = {k: v for k, v in dps.items() if k not in known}
    if extra:
        lines.append(f"other DPs        : {extra}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--watch", action="store_true",
                    help="keep the connection open and print every update")
    args = ap.parse_args()

    try:
        ip, dev_id, key = (os.environ[v] for v in
                           ("STOVE_IP", "STOVE_ID", "STOVE_KEY"))
    except KeyError as e:
        sys.exit(f"missing environment variable {e}")
    version = float(os.environ.get("STOVE_VERSION", "3.3"))

    stove = tinytuya.Device(dev_id, ip, key, version=version)
    status = stove.status()
    if "Error" in status:
        sys.exit(f"stove returned an error: {json.dumps(status)}\n"
                 "Wrong key/version, or another app holds the stove's only "
                 "local connection.")
    print("raw DPS:", json.dumps(status.get("dps", {})))
    print(decode(status.get("dps", {})))
    if not args.watch:
        return

    stove.set_socketPersistent(True)
    print("\nwatching for changes (Ctrl-C to stop)...")
    while True:
        msg = stove.receive()
        if msg and "dps" in msg:
            print("\nupdate:", json.dumps(msg["dps"]))
            print(decode(msg["dps"]))
        else:
            stove.heartbeat()


if __name__ == "__main__":
    main()
