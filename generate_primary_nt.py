#!/usr/bin/env python3
"""Generate NextTrace-format geoip_primary_nt.csv from DN42 registry.
Format: IP_CDIR,LtdCode,ISO3166-2,CityName,ASN,IPWhois

ASN is extracted from matching route/route6 objects.
IPWhois uses the mnt-by field from the inetnum/inet6num object.
"""

import os
import sys
import csv
import ipaddress

REGISTRY_PATH = 'registry_repo'
OUTPUT_PATH = 'geoip_primary_nt.csv'

DIRS = [
    ('inetnum',  'route'),
    ('inet6num', 'route6'),
]


def parse_rpsl_file(filepath):
    result = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line or line[0] in (' ', '\t'):
                continue
            if ':' not in line:
                continue
            key, _, value = line.partition(':')
            result.setdefault(key.strip(), []).append(value.strip())
    return result


def prefix_sort_key(prefix_str):
    try:
        net = ipaddress.ip_network(prefix_str.strip(), strict=False)
        return (net.version, int(net.network_address), net.prefixlen)
    except ValueError:
        return (0, 0, 0)


def build_route_map(data_dir):
    """Map CIDR filename -> list of ASN strings from route objects."""
    route_map = {}
    route_dir = os.path.join(REGISTRY_PATH, 'data', data_dir)
    if not os.path.isdir(route_dir):
        return route_map

    for filename in os.listdir(route_dir):
        filepath = os.path.join(route_dir, filename)
        if not os.path.isfile(filepath):
            continue
        data = parse_rpsl_file(filepath)
        origins = data.get('origin', [])
        if origins:
            route_map[filename] = origins
    return route_map


def generate():
    if not os.path.isdir(REGISTRY_PATH):
        print(f"Error: registry not found at {REGISTRY_PATH}", file=sys.stderr)
        sys.exit(1)

    route4_map = build_route_map('route')
    route6_map = build_route_map('route6')
    route_maps = {'inetnum': route4_map, 'inet6num': route6_map}

    entries = []

    for obj_dir, route_dir in DIRS:
        data_path = os.path.join(REGISTRY_PATH, 'data', obj_dir)
        if not os.path.isdir(data_path):
            print(f"Warning: {data_path} not found, skipping", file=sys.stderr)
            continue

        route_map = route_maps[obj_dir]

        for filename in os.listdir(data_path):
            filepath = os.path.join(data_path, filename)
            if not os.path.isfile(filepath):
                continue

            data = parse_rpsl_file(filepath)
            cidr = data.get('cidr', [''])[0]
            country = data.get('country', [None])[0]
            mnt_by = data.get('mnt-by', [''])[0]

            if not cidr or not country:
                continue

            routes = route_map.get(filename, [])
            asn = ';'.join(routes) if routes else ''

            entries.append((cidr, country, '', '', asn, mnt_by))

    entries.sort(key=lambda e: prefix_sort_key(e[0]))

    with open(OUTPUT_PATH, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['# IP_CDIR', 'LtdCode', 'ISO3166-2', 'CityName', 'ASN', 'IPWhois'])
        for row in entries:
            writer.writerow(row)

    print(f"Generated {OUTPUT_PATH} with {len(entries)} entries")


if __name__ == "__main__":
    generate()
