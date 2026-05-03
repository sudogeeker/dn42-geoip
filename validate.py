"""Shared validation for CIDR and country fields."""

import ipaddress
import re
import sys

COUNTRY_RE = re.compile(r'^[A-Z]{2}$')
ASN_RE = re.compile(r'^AS\d+(;AS\d+)*$')


def valid_cidr(cidr, source=''):
    """Check that cidr is a valid IP network address (strict: host bits must be zero)."""
    try:
        ipaddress.ip_network(cidr.strip(), strict=True)
        return True
    except ValueError as e:
        print(f"SKIP invalid cidr [{cidr}] from {source}: {e}", file=sys.stderr)
        return False


def valid_country(code):
    """Check that country is a 2-letter uppercase ISO 3166-1 alpha-2 code."""
    return bool(COUNTRY_RE.match(code))


def valid_asn(asn):
    """Check that ASN is empty or valid ASxxxxx format (possibly semicolon-separated)."""
    if not asn:
        return True
    return bool(ASN_RE.match(asn))
