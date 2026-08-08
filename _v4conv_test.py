import sys
sys.path.insert(0, r'C:\Users\sambodhi\Downloads\E\piano-dsl')
from ep_compiler.compile import compile_source
from plugins.portbaby.v1_to_v4 import convert

events = []
for i in range(24):
    events.append({
        "timestamp": i * 100, "midi": 60 + i, "duration": 80,
        "velocity": 90, "pan": 0.0, "bend": 0, "channel": None,
    })
out = convert(events, 120)
print(out)
print("=== ROUND-TRIP ===")
ev2, bp2 = compile_source(out)
orig = sorted((e["timestamp"], e["midi"], e["duration"]) for e in events)
new = sorted((e["timestamp"], e["midi"], e["duration"]) for e in ev2)
print(f"original: {len(orig)}, compiled: {len(new)}")
print("IDENTICAL" if orig == new else "MISMATCH!")

# Also test with channel + velocity ramp
events2 = []
for i in range(10):
    events2.append({
        "timestamp": i * 250, "midi": 48 + i * 2, "duration": 200,
        "velocity": 60 + i * 6, "pan": 0.0, "bend": 0, "channel": 1,
    })
out2 = convert(events2, 120)
print("\n=== CHANNEL + VELOCITY RAMP ===")
print(out2)
ev3, _ = compile_source(out2)
orig2 = sorted((e["timestamp"], e["midi"], e["duration"], e["velocity"], e.get("channel")) for e in events2)
new2 = sorted((e["timestamp"], e["midi"], e["duration"], e["velocity"], e.get("channel")) for e in ev3)
print("IDENTICAL" if orig2 == new2 else f"MISMATCH! {len(orig2)} vs {len(new2)}")
