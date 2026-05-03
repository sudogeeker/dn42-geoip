#!/usr/bin/env python3
"""Merge geoip_primary_nt.csv and geoip_manual_nt.csv into geofeed_nt.csv.

Manual entries override primary entries for the same prefix.
Output follows NextTrace 6-column format:
  IP_CDIR,LtdCode,ISO3166-2,CityName,ASN,IPWhois
"""

import csv
import sys
import os

PRIMARY_PATH = 'geoip_primary_nt.csv'
MANUAL_PATH = 'geoip_manual_nt.csv'
OUTPUT_PATH = 'geofeed_nt.csv'
HEADER = '# IP_CDIR,LtdCode,ISO3166-2,CityName,ASN,IPWhois'


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
          f"{manual_count} manual = {len(seen)} total")


if __name__ == "__main__":
    merge_csv()
