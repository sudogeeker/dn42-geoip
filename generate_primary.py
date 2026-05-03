#!/usr/bin/env python3
"""Generate geoip_primary.csv from DN42 registry data (RFC 8805 geofeed format)."""

import os
import sys
import csv
import ipaddress
from validate import valid_cidr, valid_country

REGISTRY_PATH = 'registry_repo'
OUTPUT_PATH = 'geoip_primary.csv'
INETNUM_DIR = os.path.join(REGISTRY_PATH, 'data', 'inetnum')
INET6NUM_DIR = os.path.join(REGISTRY_PATH, 'data', 'inet6num')


def parse_rpsl_file(filepath):
    """Parse an RPSL file and return a dict of key -> value.

    Handles continuation lines (indented lines that append to the previous key).
    """
    result = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line:
                continue
            if line[0] in (' ', '\t'):
                continue
            if ':' not in line:
                continue
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()
            result[key] = value
    return result


def prefix_sort_key(prefix_str):
    """Return a sort key for an IP prefix string."""
    try:
        net = ipaddress.ip_network(prefix_str.strip(), strict=False)
        return (net.version, int(net.network_address), net.prefixlen)
    except ValueError:
        return (0, 0, 0)


def generate():
    if not os.path.isdir(REGISTRY_PATH):
        print(f"Error: registry not found at {REGISTRY_PATH}", file=sys.stderr)
        sys.exit(1)

    entries = []

    for label, data_dir in [('inetnum', INETNUM_DIR), ('inet6num', INET6NUM_DIR)]:
        if not os.path.isdir(data_dir):
            print(f"Warning: {data_dir} not found, skipping", file=sys.stderr)
            continue

        for filename in os.listdir(data_dir):
            filepath = os.path.join(data_dir, filename)
            if not os.path.isfile(filepath):
                continue

            data = parse_rpsl_file(filepath)
            cidr = data.get('cidr')
            country = data.get('country')

            if not cidr or not country:
                continue

            if not valid_cidr(cidr, filepath):
                continue
            if not valid_country(country):
                print(f"SKIP invalid country [{country}] from {filepath}", file=sys.stderr)
                continue

            entries.append((cidr, country))

    entries.sort(key=lambda e: prefix_sort_key(e[0]))

    with open(OUTPUT_PATH, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['# prefix', 'country_code'])
        for cidr, country in entries:
            writer.writerow([cidr, country])

    print(f"Generated {OUTPUT_PATH} with {len(entries)} entries")


if __name__ == "__main__":
    generate()
