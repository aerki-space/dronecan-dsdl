#!/usr/bin/env python3
"""Draw the wire layout of every aerki message, straight from the DSDL sources, to docs/img/layout.png.

Field widths are the encoded bit lengths reported by the DroneCAN parser, and the frame counts
come from encoding a worst-case message with pydronecan's own transport code.

    pip install matplotlib && python3 tools/plot_layout.py
"""
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dronecan  # noqa: E402
from dronecan import transport  # noqa: E402

import validate  # noqa: E402

OUT = os.path.join(os.path.dirname(validate.ROOT), 'docs', 'img', 'layout.png')
INK, MUTED = '#1f2328', '#656d76'
COLOURS = {'timestamp': '#8c959f', 'id': '#bf8700', 'position': '#0969da', 'value': '#1a7f37',
           'state': '#8250df', 'array': '#cf222e'}


SHORT = {'position_error': 'pos. σ', 'peak_temperature': 'peak °C', 'temperature': 'temp.',
         'supply_voltage': 'supply V', 'beams_per_scan': 'beams', 'frame_index': 'frame #', 'beam_azimuth': 'beam az',
         'beam_elevation': 'beam el', 'radial_velocity': 'velocity', 'sensor_id': 'id', 'error_flags': 'error flags',
         'mode': 'mode', 'tx_enabled': '', 'scan_complete': '', 'latitude_deg_1e7': 'latitude',
         'longitude_deg_1e7': 'longitude', 'voc_index': 'VOC', 'confidence': 'conf.', 'humidity': 'RH',
         'status': 'st.', 'track_id': 'track', 'frame_rate': 'rate'}


def kind(name, ftype):
    if name == 'timestamp':
        return 'timestamp'
    if name.endswith('_id') or name == 'frame_index':
        return 'id'
    if any(k in name for k in ('lat', 'lon', 'azimuth', 'elevation', 'range', 'position')):
        return 'position'
    if ftype.category == ftype.CATEGORY_ARRAY:
        return 'array'
    if any(k in name for k in ('mode', 'status', 'flags', 'enabled', 'complete')):
        return 'state'
    return 'value'


def frame_counts(msg):
    out = []
    for fd in (False, True):
        t = transport.Transfer(payload=msg, source_node_id=10, transfer_id=0, transfer_priority=16,
                               service_not_message=False, canfd=fd)
        out.append(len(t.to_frames()))
    return out


def worst_case(name):
    A = dronecan.thirdparty.aerki
    if name == 'aerki.radar.Detections':
        return A.radar.Detections(targets=[A.radar.Target()] * 16)
    ns, short = name.split('.')[1:]
    return getattr(getattr(A, ns), short)()


def main():
    dronecan.load_dsdl(validate.ROOT)
    types = [t for t in validate.load() if t.kind == t.KIND_MESSAGE and t.default_dtid is not None]
    types.sort(key=lambda t: t.default_dtid, reverse=True)
    target = next(t for t in validate.load() if t.full_name == 'aerki.radar.Target')

    rows = [(t.full_name, f'ID {t.default_dtid}', t.fields, frame_counts(worst_case(t.full_name))) for t in types]
    rows.append(('aerki.radar.Target', 'nested, ×16 in Detections', target.fields, None))
    max_bits = max(sum(f.type.get_max_bitlen() for f in r[2] if f.type.category != f.type.CATEGORY_ARRAY)
                   for r in rows)
    scale = 1.0 / max(max_bits, 1)

    fig, ax = plt.subplots(figsize=(12, 1.25 * len(rows) + 1.2))
    for i, (name, tag, fields, frames) in enumerate(rows):
        y = len(rows) - 1 - i
        x = 0.0
        for f in fields:
            arr = f.type.category == f.type.CATEGORY_ARRAY
            bits = 32 if arr else f.type.get_max_bitlen()
            w = bits * scale
            k = kind(f.name, f.type)
            ax.add_patch(Rectangle((x, y), w, 0.62, fc=COLOURS[k], ec='white', lw=1.2, alpha=0.9 if not arr else 0.75,
                                   hatch='//' if arr else None))
            label = f'{f.name}[≤{f.type.max_size}]' if arr else SHORT.get(f.name, f.name)
            if label:
                ax.text(x + w / 2, y + 0.31, label, ha='center', va='center', fontsize=7, color='white')
            x += w
        total = (t.get_max_bitlen() if (t := next((t for t in types if t.full_name == name), None)) else
                 target.get_max_bitlen())
        ax.text(-0.01, y + 0.42, name, ha='right', va='center', fontsize=9.5, fontweight='bold', color=INK)
        ax.text(-0.01, y + 0.12, tag, ha='right', va='center', fontsize=8, color=MUTED)
        info = f'≤ {validate.size_bytes(total)} B'
        if frames:
            info += f'   ·   {frames[0]} classic CAN / {frames[1]} CAN FD frames'
        ax.text(x + 0.012, y + 0.31, info, va='center', fontsize=8.5, color=INK)
    for b in range(0, max_bits + 1, 8):
        ax.axvline(b * scale, color='#eaeef2', lw=0.6, zorder=0)
    handles = [Rectangle((0, 0), 1, 1, fc=c, ec='none') for c in COLOURS.values()]
    ax.legend(handles, ['time', 'identifiers', 'geometry', 'measurements', 'state', 'arrays'], frameon=False,
              ncol=6, loc='upper center', bbox_to_anchor=(0.5, 0.0), fontsize=8.5)
    ax.set_title('aerki DroneCAN messages on the wire (fields to scale, arrays shortened; faint lines every byte)',
                 loc='left', fontsize=11, fontweight='bold', color=INK)
    ax.set_xlim(-0.01, 1.42)
    ax.set_ylim(-0.25, len(rows) - 0.2)
    ax.axis('off')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, dpi=160, bbox_inches='tight')
    print('wrote', os.path.relpath(OUT, os.path.dirname(validate.ROOT)))


if __name__ == '__main__':
    main()
