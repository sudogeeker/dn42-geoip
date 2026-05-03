#!/usr/bin/env python3
"""Merge geoip_primary.csv and geoip_manual.csv into geofeed.csv.

Manual entries override primary entries for the same prefix (deduplication).
Output follows RFC 8805 geofeed format.
"""

import csv
import sys
import os
from validate import valid_cidr, valid_country

PRIMARY_PATH = 'geoip_primary.csv'
MANUAL_PATH = 'geoip_manual.csv'
OUTPUT_PATH = 'geofeed.csv'
HEADER = '# prefix,country_code,region,city,postal_code'


def merge_csv():
    if not os.path.exists(PRIMARY_PATH):
        print(f"Error: {PRIMARY_PATH} not found.", file=sys.stderr)
        sys.exit(1)

    seen = set()
    rows = []

    try:
        with open(PRIMARY_PATH, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or row[0].startswith('#'):
                    continue
                prefix = row[0].strip()
                if prefix and prefix not in seen:
                    seen.add(prefix)
                    rows.append(row)
    except Exception as e:
        print(f"Error reading {PRIMARY_PATH}: {e}", file=sys.stderr)
        sys.exit(1)

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
                    if country and not valid_country(country):
                        print(f"SKIP invalid country [{country}] in manual entry {prefix}",
                              file=sys.stderr)
                        continue
                    if prefix in seen:
                        rows = [r for r in rows if r[0].strip() != prefix]
                        seen.discard(prefix)
                    seen.add(prefix)
                    rows.append(row)
        except Exception as e:
            print(f"Error reading {MANUAL_PATH}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Note: {MANUAL_PATH} not found, using primary data only.")

    rows.sort(key=lambda r: r[0].strip())

    try:
        with open(OUTPUT_PATH, 'w', encoding='utf-8', newline='') as f:
            f.write(HEADER + '\n')
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            for row in rows:
                writer.writerow(row)
    except Exception as e:
        print(f"Error writing {OUTPUT_PATH}: {e}", file=sys.stderr)
        sys.exit(1)

    manual_count = len(seen) - primary_count if os.path.exists(MANUAL_PATH) else 0
    print(f"Merged into {OUTPUT_PATH}: {primary_count} primary + "
          f"{len(seen) - primary_count} manual = {len(seen)} total")


if __name__ == "__main__":
    merge_csv()
