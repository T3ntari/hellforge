"""Multi-file project builder — generates .ei + parts/ + .enx structure."""

import os


def build_project(source_path, output_text, events, bpm, target_ver, source_ver):
    """Build a multi-file project from converted output.
    Creates directory structure with index.ei, parts/, and project.enx."""
    base_name = os.path.splitext(os.path.basename(source_path))[0]
    out_dir = f"{base_name}_ported_{target_ver}"

    os.makedirs(out_dir, exist_ok=True)
    parts_dir = os.path.join(out_dir, "parts")
    os.makedirs(parts_dir, exist_ok=True)

    # Split events by channel (normalize None to 0 for sorting)
    ch_events = {}
    for e in events:
        ch = e.get("channel")
        if ch is None:
            ch = 0
        if ch not in ch_events:
            ch_events[ch] = []
        ch_events[ch].append(e)

    # Write part files
    part_names = {}
    for i, (ch, ch_evs) in enumerate(sorted(ch_events.items())):
        part_name = f"part_{i + 1}"
        part_names[ch] = part_name
        output_text_ch = _events_to_source(ch_evs, bpm, target_ver)
        with open(os.path.join(parts_dir, f"{part_name}.e"), "w", encoding="utf-8") as f:
            f.write(f"// Channel {ch}\n")
            f.write(output_text_ch)

    # Write index.ei
    with open(os.path.join(out_dir, "index.ei"), "w", encoding="utf-8") as f:
        f.write(f'project "{base_name}"\n')
        f.write(f"tempo {int(bpm)}\n\n")
        for ch, name in sorted(part_names.items()):
            f.write(f'include "parts/{name}.e" as {name}\n')
        f.write("\nsection \"Main\" {\n")
        for ch, name in sorted(part_names.items()):
            f.write(f"    play {name}\n")
        f.write("}\n")

    # Write project.enx for v4 output
    if target_ver == "v4":
        with open(os.path.join(out_dir, "project.enx"), "w", encoding="utf-8") as f:
            f.write(f"#ENX v1\n")
            f.write(f'project "{base_name} (Ported to v4)"\n')
            f.write(f'order "index.ei"\n')

    # Write conversion report
    with open(os.path.join(out_dir, "port_report.txt"), "w", encoding="utf-8") as f:
        f.write(f"Portbaby Conversion Report\n")
        f.write(f"{'='*40}\n")
        f.write(f"Source: {os.path.basename(source_path)}\n")
        f.write(f"From: {source_ver}  To: {target_ver}\n")
        f.write(f"Events: {len(events)}\n")
        f.write(f"Channels: {len(ch_events)}\n")
        f.write(f"Parts: {len(part_names)}\n")

    print(f"  \u2713 Project created: {out_dir}/")
    print(f"    index.ei ({len(part_names)} parts)")
    if target_ver == "v4":
        print(f"    project.enx")
    print(f"    parts/ ({len(part_names)} files)")
    print(f"    port_report.txt")

    return out_dir


def _events_to_source(events, bpm, target_ver):
    """Convert events to source text for the target version, preserving CH binding."""
    from ep_compiler.import_midi import events_to_e_source
    return events_to_e_source(events, bpm, human=False)  # always use machine format for parts
