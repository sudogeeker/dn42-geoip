#!/usr/bin/env python3
"""Merge geoip_primary_nt.csv and geoip_manual.csv into geofeed_nt.csv.

Manual entries override primary entries for the same prefix.
Output follows NextTrace 6-column format:
  IP_CDIR,LtdCode,ISO3166-2,CityName,ASN,IPWhois

For manual entries, ASN and IPWhois are looked up from the primary data:
first by exact prefix match, then by the smallest containing prefix.
"""

import csv
import sys
import os
import ipaddress
from validate import valid_cidr, valid_country

PRIMARY_PATH = 'geoip_primary_nt.csv'
MANUAL_PATH = 'geoip_manual.csv'
OUTPUT_PATH = 'geofeed_nt.csv'
HEADER = '# IP_CDIR,LtdCode,ISO3166-2,CityName,ASN,IPWhois'


def load_primary(path):
    """Load primary data and return (rows, prefix_lookup).

    prefix_lookup maps prefix -> (asn, ipwhois)
    """
    rows = []
    lookup = {}
    seen = set()

    with open(path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or row[0].startswith('#'):
                continue
            prefix = row[0].strip()
            if not prefix or prefix in seen:
                continue
            seen.add(prefix)
            rows.append(row)
            asn = row[4].strip() if len(row) > 4 else ''
            whois = row[5].strip() if len(row) > 5 else ''
            if asn or whois:
                lookup[prefix] = (asn, whois)

    return rows, lookup


def best_match(prefix, lookup):
    """Find the smallest containing prefix in lookup for the given prefix."""
    try:
        net = ipaddress.ip_network(prefix.strip(), strict=False)
    except ValueError:
        return '', ''

    best_len = -1
    best = ('', '')

    for p, (asn, whois) in lookup.items():
        try:
            p_net = ipaddress.ip_network(p.strip(), strict=False)
        except ValueError:
            continue
        if p_net.version != net.version:
            continue
        if p_net.prefixlen > best_len and p_net.supernet_of(net):
            best_len = p_net.prefixlen
            best = (asn, whois)

    return best


def merge_csv():
    if not os.path.exists(PRIMARY_PATH):
        print(f"Error: {PRIMARY_PATH} not found.", file=sys.stderr)
        sys.exit(1)

    rows, primary_lookup = load_primary(PRIMARY_PATH)
    seen = {r[0].strip() for r in rows}
    primary_count = len(rows)

    if os.path.exists(MANUAL_PATH):
        try:
            with open(MANUAL_PATH, 'r', encoding='utf-8', newline='') as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row or row[0].startswith('#'):
                        continue
                    prefix = row[0].strip()
                    if not prefix:
                        continue
                    if not valid_cidr(prefix, f'{MANUAL_PATH} manual entry'):
                        continue
                    country = row[1].strip() if len(row) > 1 else ''
                    region = row[2].strip() if len(row) > 2 else ''
                    city = row[3].strip() if len(row) > 3 else ''
                    if country and not valid_country(country):
                        print(f"SKIP invalid country [{country}] in manual entry {prefix}",
                              file=sys.stderr)
                        continue

                    if prefix in seen:
                        # Remove existing primary entry
                        rows = [r for r in rows if r[0].strip() != prefix]
                        seen.discard(prefix)

                    # Lookup ASN/IPWhois: exact match first, then longest prefix match
                    asn, whois = primary_lookup.get(prefix, ('', ''))
                    if not asn and not whois:
                        asn, whois = best_match(prefix, primary_lookup)

                    seen.add(prefix)
                    rows.append([prefix, country, region, city, asn, whois])
        except Exception as e:
            print(f"Error reading {MANUAL_PATH}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Note: {MANUAL_PATH} not found, using primary data only.")

    rows.sort(key=lambda r: r[0].strip())

    with open(OUTPUT_PATH, 'w', encoding='utf-8', newline='') as f:
        f.write(HEADER + '\n')
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        for row in rows:
            writer.writerow(row)

    manual_count = len(seen) - primary_count if os.path.exists(MANUAL_PATH) else 0
    print(f"Merged into {OUTPUT_PATH}: {primary_count} primary + "
          f"{manual_count} manual = {len(seen)} total")


if __name__ == "__main__":
    merge_csv()
