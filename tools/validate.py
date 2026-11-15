#!/usr/bin/env python3
"""Validate the aerki DSDL namespace.

Parses aerki/ together with every namespace shipped with the DroneCAN tools (standard
uavcan, dronecan, ardupilot and the known vendors), so any data-type-ID collision is an
error. Also enforces the ID ranges in docs/id-allocation.md and prints a size table.

    python3 tools/validate.py            # exit 1 on any problem
"""
import os
import sys

import dronecan
from dronecan import dsdl

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'aerki'))
SPECS = os.path.join(os.path.dirname(dronecan.__file__), 'dsdl_specs')
SHIPPED = [os.path.join(SPECS, d) for d in sorted(os.listdir(SPECS)) if os.path.isdir(os.path.join(SPECS, d))]

# sub-namespace -> (first, last) allowed message IDs; services share one block
MESSAGE_RANGES = {'radar': (20400, 20409), 'sensor': (20410, 20429)}
SERVICE_RANGE = (230, 239)


def load():
    return sorted((t for t in dsdl.parse_namespaces([ROOT] + SHIPPED) if t.full_name.startswith('aerki.')),
                  key=lambda t: t.full_name)


def check(types):
    problems = []
    for t in types:
        sub = t.full_name.split('.')[1]
        dtid = t.default_dtid
        if dtid is None:
            continue
        if t.kind == t.KIND_SERVICE:
            lo, hi = SERVICE_RANGE
        else:
            if sub not in MESSAGE_RANGES:
                problems.append(f'{t.full_name}: no message ID range allocated for aerki.{sub}')
                continue
            lo, hi = MESSAGE_RANGES[sub]
        if not lo <= dtid <= hi:
            problems.append(f'{t.full_name}: ID {dtid} outside the aerki.{sub} range {lo}-{hi}')
    return problems


def size_bytes(bits):
    return (bits + 7) // 8


def main():
    try:
        types = load()
    except dsdl.DsdlException as e:
        print('DSDL error:', e)
        return 1
    for t in types:
        if t.kind == t.KIND_SERVICE:
            print(f'{t.full_name:26s} service {t.default_dtid:>5}  request <= {size_bytes(t.get_max_bitlen_request())} B, '
                  f'response <= {size_bytes(t.get_max_bitlen_response())} B')
        else:
            dtid = t.default_dtid if t.default_dtid is not None else '-'
            print(f'{t.full_name:26s} message {dtid:>5}  <= {size_bytes(t.get_max_bitlen())} B  '
                  f'signature 0x{t.get_data_type_signature():016x}')
    problems = check(types)
    for p in problems:
        print('ERROR:', p)
    print(f'{len(types)} types, {len(problems)} problem(s), no ID collisions with {len(SHIPPED)} shipped namespaces')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
