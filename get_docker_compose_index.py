#!/usr/bin/env python3
# Retrieve the docker-compose scale index for a service
import psutil
import socket
import dns.resolver
import dns.reversename
import re

def get_scale_index():
    # Get the IP address of the eth0 interface
    addrs = psutil.net_if_addrs()
    ip_address = None
    for addr in addrs.get('eth0', []):
        if addr.family == socket.AF_INET:
            ip_address = addr.address
            break
    if not ip_address:
        raise Exception("No IP address found for eth0")

    # Perform reverse DNS lookup
    try:
        rev_name = dns.reversename.from_address(ip_address)
        hostname = str(dns.resolver.resolve(rev_name, "PTR")[0])
    except Exception as e:
        raise Exception(f"Reverse DNS lookup failed: {e}")

    # Extract the suffix using a regular expression
    match = re.search(r'^.*-(\d+)\..*$', hostname)
    if match:
        return match.group(1)
    else:
        raise Exception(f"Failed to extract scale index from hostname: {hostname}")

scale_index = get_scale_index()
print(scale_index)
