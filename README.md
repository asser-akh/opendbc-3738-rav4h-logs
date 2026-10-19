# Sanitized rlogs for commaai/opendbc#3738

Toyota `RADAR_PRE_FAULT` raising `radarUnavailableTemporary` with `RADAR_STATUS = 1`, which shows up as a `commIssue` soft disable on a stock-longitudinal car.

- **Car:** `TOYOTA_RAV4H` (2016-18 RAV4 Hybrid, TSS-P, DSU present, stock longitudinal).
- **Device:** comma four.
- **Software:** sunnypilot 2026.003.000 `staging`, commit 4063760 (opendbc b2acec1d, includes #3452). MADS on.
- **Drive:** one highway drive, 2026-10-15 00:27 to 01:06 UTC, dry, about 105 to 115 km/h.

## Segments

Route `00000088--ac850ae5f6`. Each file is one 60-second segment.

| Segment | Content |
|---|---|
| 33 | normal operation before the first onset |
| 34 | onset 00:28:47, cleared after 1.8 s (alert only, no disengagement) |
| 36 | normal |
| 37 | onset 00:31:10, 24.8 s; soft disable, openpilot cancel, driver re-engage cancelled again |
| 40 | normal |
| 41, 42 | onset 00:35:58, 36 s total |
| 63 | normal |
| 64 | onset 00:58:14, 8.4 s; soft disable and cancel |
| 65 | normal |
| 66 | onset 01:00:28, 31 s, `INVALID_COUNTER` peak 2643 |
| 70, 71 | onset 01:05:04, cleared 01:05:12 |

## What was kept and removed

The logs were sanitized with `sanitize.py` in this repo.

- **Kept:** `can` (all buses, including bus 1), `sendcan`, `pandaStates`, `carParams` (VIN blanked), `carState`, `carControl`, `carOutput`, `radarTracks`, `radarState`, `modelV2`, `drivingModelData`, `selfdriveState`, `onroadEvents`, `controlsState`, `longitudinalPlan`, `driverAssistance`, `liveCalibration`, `managerState`, and the sunnypilot `*SP` counterparts.
- **Removed:** `initData`, all GNSS and location messages, camera, encode and thumbnail messages, driver monitoring, audio, text logs, and other sensors.

The files are zstd-compressed capnp event streams, readable with `LogReader`.

## Observations, decoded from these files

- **Radar status:** `RADAR_STATUS` (0x123) stays 1 in every status frame. `RADAR_PRE_FAULT` goes 0 to 3 exactly when `INVALID_COUNTER` reaches 1358 (idle 137, steps of 257) and clears when it falls back. The peak is 2643, below the 2659 at which the car reports the radar dirty.
- **No dropouts:** radar track frames keep arriving at 20 Hz, `radarTracks.errors.canError` never sets, and the bus-1 error counters stay flat.
- **No radar targets before onset:** there are 0 valid radar tracks in the 5 s before every onset (empty road). The flag clears when a lead appears.
- **The car sees no fault:** `ACC_CONTROL.RADAR_DIRTY = 0`, `ACC_MALFUNCTION = 0` and `PCM_CRUISE_2.ACC_FAULTED = 0` throughout. Stock ACC stays active until openpilot sends `ACC_CONTROL.CANCEL_REQ` after the `commIssue` soft disable. In segment 37 the car accepts a driver SET/RES during the pre-fault, and openpilot cancels it again about 0.2 s later.
- **Nothing unusual transmitted:** `sendcan` contains only 0x2E4, 0x412 and 0x343. There are no 0x7xx diagnostic frames on any bus.
