# Local Home Assistant control: no flashing, no stove downtime

This guide is for owners who want local Home Assistant control of a TYWE1S pellet stove (Cleveland Iron Works / Master Forge / Nemaxx family) but can't take the stove apart or leave it down.

**Bottom line:** keep the stock TYWE1S firmware. Move the stove from the vendor app into **Tuya Smart** (or Smart Life). Let the [tuya-local](https://github.com/make-all/tuya-local) integration fetch the stove's local key. Then control the stove over the LAN with the profile in [`tuya-local/`](../tuya-local/pellet_stove_tywe1s.yaml). That gives Home Assistant the same datapoints the vendor app has, plus decoded fault codes. Nothing is soldered or flashed. The stove keeps heating the whole time, because pairing only touches the WiFi module. Once it works, block the stove's internet access and delete the vendor app.

The ESPHome routes below are still worth having. They are the way to get the advanced mods (ultra-low burn, PID auger control, remote error reset, real-time temperatures). You can do them later, on your own schedule, without a heating outage.

---

## 1. What the repo and its discussions establish

All 30 upstream discussions and 6 issues were reviewed. The facts that drive the recommendation:

| Fact | Source |
|---|---|
| The WiFi module is a **plug-in daughterboard** (N12210) on the display board. It only relays TuyaMCU messages at 9600 baud between the display MCU and the cloud. | README; discussions #18, #23 |
| **The stove runs normally with the WiFi module unplugged.** Vendors have even shipped displays without one. | #18 ("can either be installed, or not"), #31 ("The stove will work without the Wifi module plugged in") |
| The module needs only **RX, TX, +5 V and GND**. Any ESP8266/ESP32 can replace it. | #23, #32, #33 |
| Datapoints: 1 power, 4 power level P1–P4, 101 ECO1/ECO2, 104 fault bitmap, 105 temperature unit, 106 set temp, 107 room temp, 108 exhaust temp, 109 protect temp. All temperatures are reported in **°F**. | README; #18; #31 |
| A Master Forge owner already read these DPs with **LocalTuya**, without flashing anything. | #18 / issue #2 |
| The MCU pushes temperatures only about **every 60 s** over TuyaMCU. Faster updates need a tap on the display↔MCU UART, which is a hardware mod. | #28, #30, #33 |
| Remote error reset ("thumbs up" press), ultra-low P5 and PID burn control all need **board mods plus an ESP32**. | #32, #34, #41, #42 |
| Some EU stoves (Justfire, "Fire@home" app) use **Blynk, not Tuya**, and none of this applies to them. | #31, README |

### Your stove, as checked from the LAN and the phone

- A passive `tinytuya scan` (UDP broadcast listen) found the stove broadcasting **product key `8Dj5zVjGqPSXaUgf`** (the same key as in this repo's README) on **Tuya LAN protocol 3.3**. Both tuya-local and LocalTuya support 3.3.
- The vendor app named in the manual is **"Smart Stove" by NHHATC** (`com.hanks.smartstove`, v1.1.1). Its Android components are all `com.thingclips.*`. ThingClips is Tuya's renamed SDK, so this is a white-label **Tuya OEM app** and the stove lives on Tuya's ordinary cloud. The app requests location, Bluetooth scan, camera and microphone. That is the generic Tuya OEM template: Android only requires location to scan WiFi during pairing.

## 2. The options, ranked

| | Path | Hardware work | Stove downtime | What you get | Status |
|---|---|---|---|---|---|
| **A** | **Stock firmware + tuya-local** (this guide) | none | **none** | Power, set temp, P1–P4, ECO1/2, room/exhaust/protect temps, decoded faults | **Recommended now** |
| B | ESPHome on the TYWE1S, or a pre-flashed spare ESP module | unplug a daughterboard; solder flash leads or wire a D1 mini | **none** (the stove heats without the module) | Same DPs as A, but no Tuya code left, and logic runs on the chip | Optional later; fixed config in this repo |
| C | jazzmonger's ESP32 "ultimate" board | cut traces on the MCU board, tap display UART, extra wires | a few hours, in the off-season | Ultra-low P5, PID auger, real-time temps, remote error reset, pellet level | Off-season project |
| D | Over-the-air flash (tuya-convert, cloudcutter, OpenBeken) | none | none | ESPHome without opening the stove | **Doesn't work here**, see §5 |

## 3. Path A step by step

Steps marked **[you]** need the stove, your phone or your accounts.

### 3.1 Move the stove into Tuya Smart / Smart Life

1. **[you]** In **Smart Stove**, open the stove's settings and choose **Remove device** (pick "disconnect and wipe data" if offered). On Tuya devices this resets the WiFi module into pairing mode. The stove keeps heating, since only the WiFi module resets.
2. **[you]** If the module's LED isn't blinking quickly, put it in pairing mode by hand. The owner's manual says: **press and hold the connection button on the back of the display panel for 3 seconds** until the indicator blinks. Hold again to switch to the slow-blink "AP" pairing mode if fast-blink pairing fails.
3. **[you]** Connect your phone to the **2.4 GHz** WiFi network. The TYWE1S has no 5 GHz radio. If your router broadcasts separate 2.4 and 5 GHz network names, pick the 2.4 GHz one, or the app hands the stove a network it can't join.
4. **[you]** In **Tuya Smart** (or Smart Life), tap **+ → Add device**. **The auto-scan will not find the stove.** It only finds Bluetooth devices and pairing hotspots, and the TYWE1S is WiFi-only. Open the **Add Manually** tab and pick **Small Home Appliances → Heater (Wi-Fi)**. The category only changes the instructions shown. Enter the 2.4 GHz network name and password, confirm the LED is blinking fast, and wait up to two minutes. Android asks for location during pairing. Grant it **"Only this time"**.
5. **[you]** If fast-blink pairing fails, hold the panel button 3 s again until the LED blinks slowly (about once every 2 s). On the app's "confirm indicator" screen, use the mode switch at the top right to choose **AP mode** (also called compatible mode). Then join the stove's `SmartLife-XXXX` hotspot when the app asks.
6. **[you]** Check that the stove shows up and responds in Tuya Smart.

Tuya Smart accepted this stove's OEM product (`8Dj5zVjGqPSXaUgf`) on the first stove tried. If it refuses yours (some OEM products are locked to their brand app), re-add the stove in Smart Stove and use **Path B** instead.

### 3.2 Install tuya-local and the stove profile in Home Assistant

1. Install **Tuya Local** from HACS (`make-all/tuya-local`).
2. Copy [`tuya-local/pellet_stove_tywe1s.yaml`](../tuya-local/pellet_stove_tywe1s.yaml) to `<HA config>/custom_components/tuya_local/devices/`. Restart Home Assistant. **Copy it again after every tuya-local update**: the integration replaces that folder.
3. **[you]** Go to **Settings → Devices & services → Add integration → Tuya Local** and choose the cloud-assisted login. It asks for the **User Code** from Tuya Smart (**Me → ⚙ Settings → Account and Security → User Code**). Then scan the QR code it shows with Tuya Smart. No Tuya developer account is needed.
4. Choose the stove. tuya-local fills in the device id, local key and IP address. It should offer **"Pellet stove"** as the top match.

You get these entities:

| Entity | DP | Notes |
|---|---|---|
| `climate` (heat / off, target temp, room temp, presets **P1–P4**) | 1, 106, 107, 4 | °F from the stove, so HA doesn't double-convert (the old °F/°C bug) |
| `select` ECO mode (ECO1 / ECO2) | 101 | ECO1 heats to the setpoint and then shuts down; ECO2 drops to P4 at the setpoint |
| `sensor` Exhaust temperature | 108 | updates about every 60 s |
| `sensor` Protection temperature (diagnostic) | 109 | |
| `binary_sensor` Problem, with `fault_code` and `description` attributes | 104 | e.g. `e2_ignition_failed`, `e1_fire_out`, `e5_door_open`. `fault_code` is the raw bitmap. `description` decodes one fault at a time; `tools/stove_check.py` decodes combinations. |

Two values in the profile are assumptions you may need to change:

- **Units.** The climate entity follows the stove's unit setting (DP 105), but the exhaust and protection sensors are fixed to °F. Keep the stove's front panel on **F** (password `1109` menu, upstream discussion #12). If you switch it to C, change the `unit: F` lines in the profile to `unit: C`.
- **Set-temperature range.** The 50–90 °F limit is only a UI clamp, a guess. The stove's real limits are in the Tuya data model ("Query Things Data Model" on platform.tuya.com). Widen the `range` if the stove accepts more.

**If the profile doesn't match** (tuya-local logs a `LOCAL DPS` warning), compare the logged values with the `dps_val` strings in the profile. The enum strings `p1`–`p4` / `ECO1`/`ECO2` come from a sibling stove on the same controller (tuya-local [#3596](https://github.com/make-all/tuya-local/issues/3596)). Yours may differ in case or wording. You can also check the stove outside HA with [`tools/stove_check.py`](../tools/stove_check.py):

```sh
STOVE_IP=... STOVE_ID=... STOVE_KEY=... uv run --with tinytuya tools/stove_check.py
```

Many Tuya devices accept **only one local connection**. Disable the HA integration entry while you run the script.

### 3.3 Cut the stove off from the cloud (optional, recommended)

1. **[you]** Give the stove a DHCP reservation on your router.
2. **[you]** Block that IP from the WAN (internet), but keep LAN traffic allowed. Local control on protocol 3.3 uses TCP 6668 and UDP 6666/6667 broadcasts, all of which stay on the LAN.
3. **Watch it for a day** before you rely on it. Make sure HA still updates, and that the module doesn't reboot-loop looking for the cloud. `tools/stove_check.py --watch` helps here.
4. Uninstall **Smart Stove**. Keep the stove in your Tuya Smart account. **Re-pairing creates a new local key**, so after any re-pair, reconfigure the tuya-local entry.

Schedules set in the vendor app stop working once the stove is offline. Use HA automations instead. The stove's own front-panel weekly timer is unaffected.

### 3.4 Automations

The automations in this repo (`automations.yaml`, `sensor.yaml`: "Goodbye!" restart, over-temp, smoothing) work unchanged in logic. Only the entity ids change from the ESPHome names to the tuya-local ones. The fault text sensor in `sensor.yaml` is no longer needed, because the problem sensor's `description` attribute already decodes DP 104.

## 4. Path B with zero heating downtime (optional, later)

Because the stove runs without its WiFi module, flashing never needs a heating outage:

- **Flash the stock module on the bench.** Power the stove off for a minute, unplug the TYWE1S daughterboard, power the stove back on (it heats without WiFi), and flash the module at your desk:
  1. Back up the stock firmware first: `esptool --port /dev/ttyUSB0 read_flash 0x0 0x100000 tywe1s-stock.bin`.
  2. Flash the fixed [`ESPHome basic config for TYWE1S chip flash.yaml`](../ESPHome%20basic%20config%20for%20TYWE1S%20chip%20flash.yaml) with ESPHome. Flash leads, 3.3 V only: 3V3, GND, U0TX, U0RX, and GPIO0 held to GND at boot (README).
  3. Plug the module back in.

  Later updates go over the air: the build uses 410 KB of the 1 MB flash.
- **Or build a spare and swap it in.** Wire a D1 mini (ESP8266) or ESP32 D1 mini to a plug that matches the daughterboard header, flash it ahead of time, and swap it in within minutes. Community-reported header pinout, looking at the back of the display board with the buzzer top-left, using the header nearest you: **pin 1 = +5 V, pin 5 = RX, pin 6 = TX**. GPIO13 goes to RX and GPIO15 goes to TX (#33, jwaz73). GND was taken from the module's pairing-button leg (#32). **Check these with a multimeter before you power anything.** The MCU side is 5 V logic; a level shifter on the MCU→ESP line is cheap insurance (#30, #34, #41).

If ESPHome logs `Initialization failed at init_state 0` over and over, the module isn't hearing the MCU. On a D1-mini swap, **swap the RX/TX wires first**: the header labels are from the module's point of view. Don't touch the config. If swapping doesn't help, the stove may not be TuyaMCU at all; the Justfire/Blynk stoves in #31 fail exactly this way.

The fixed basic config builds on ESPHome 2026.10.1. Earlier revisions failed to build, used the wrong UART pins (GPIO1/3 instead of GPIO13/15), and logged over the UART shared with the MCU. Those are fixed in this fork's PR #1.

## 5. Why not flash it over the air?

- **tuya-convert** is the only OTA flasher that ever supported ESP8266 Tuya modules. Tuya patched the hole (PSK identity "02") in early 2020, and the project's README says there is no workaround. The project was last updated in Sept 2024. A stove sold in 2021 or later and already paired in its app is almost certainly patched.
- **tuya-cloudcutter** supports Beken BK7231T/N and Realtek RTL87xx chips only. **OpenBeken** is firmware for those chips. Neither applies to the ESP8266-based TYWE1S. They would only matter if a newer stove shipped a WB2S/CB2S/CBU-type module instead.
- Tuya's LAN protocol has **no firmware-update command**. Firmware updates come only from the Tuya cloud.

## Sources

- Upstream repo and discussions: <https://github.com/jazzmonger/wood-pellet-stove-with-TYWE1S-Tuya-chip/discussions>
- tuya-local device-config docs: <https://github.com/make-all/tuya-local/blob/main/custom_components/tuya_local/devices/README.md>
- tuya-local issue #3596, a sibling stove's local DPS and Tuya data model: <https://github.com/make-all/tuya-local/issues/3596>
- tinytuya: <https://github.com/jasonacox/tinytuya>
- tuya-convert (patch status in its README): <https://github.com/ct-Open-Source/tuya-convert>
- tuya-cloudcutter (supported chips): <https://github.com/tuya-cloudcutter/tuya-cloudcutter>
- Cleveland Iron Works owner's manual, "Smart Stove WiFi Connection": <https://pdf.lowes.com/productdocuments/7f8c5f48-4d5a-4cb1-92df-4710000d5c93/60766462.pdf>

## How the profile was validated

- Validated by tuya-local's own config tests (`tests/test_device_config.py`, 33 passed) and its `yamllint` rules, at tuya-local commit `2454696` (2026-10-27).
- `util.best_match` scores it the **100% best match among 1,783 bundled configs** for the expected stove DPS, with or without the optional DP 105.
- **Not yet confirmed against a live stove.** The first `LOCAL DPS` line from the real stove is the final check (§3.2).
