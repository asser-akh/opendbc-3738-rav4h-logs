"""Write a sanitized rlog: keep CAN and control/planning messages, drop location, identity, camera, audio, text logs.

Usage: sanitize.py <schema-dir> <in rlog.zst> <out rlog.zst>
"""
import sys, collections, capnp, zstandard
S, src, dst = sys.argv[1:4]
capnp.remove_import_hook()
log = capnp.load(S + "/openpilot/cereal/log.capnp", imports=[S + "/openpilot/cereal", S + "/opendbc_repo/opendbc/car", S + "/openpilot/cereal/include"])
KEEP = {"can", "sendcan", "pandaStates", "carParams", "carState", "carControl", "carOutput", "liveTracks",
        "radarState", "modelV2", "drivingModelData", "selfdriveState", "onroadEvents", "controlsState",
        "longitudinalPlan", "driverAssistance", "liveCalibration", "managerState", "radarTracks",
        "carStateSP", "carControlSP", "selfdriveStateSP", "onroadEventsSP", "longitudinalPlanSP", "carParamsSP"}
raw = zstandard.ZstdDecompressor().stream_reader(open(src, "rb")).read()
out, kept, dropped = [], collections.Counter(), collections.Counter()
for m in log.Event.read_multiple_bytes(raw):
    w = m.which()
    if w not in KEEP:
        dropped[w] += 1
        continue
    if w == "carParams":
        b = m.as_builder()
        b.carParams.carVin = ""
        out.append(b.to_bytes())
    else:
        out.append(m.as_builder().to_bytes())
    kept[w] += 1
open(dst, "wb").write(zstandard.ZstdCompressor(level=19).compress(b"".join(out)))
print(dst, "kept", sum(kept.values()), "dropped", sum(dropped.values()), "dropped types:", ",".join(sorted(dropped)))
