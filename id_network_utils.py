# -*- coding: utf-*-
# utilities for network
import netifaces
import nmap
import socket
import subprocess

HOSTNAME_KEY: str = 'hostname'
IP_V4_KEY: str = 'ipv4'
MAC_ADDRESS_KEY: str = 'mac'
VENDOR_KEY: str = 'vendor'
_ADDR_KEY: str = 'addr'


def find_wifi_ssid() -> str:
    try:
        output = subprocess.check_output(['sudo', 'iwgetid'])
        return str(output).split('"')[1]
    except Exception:
        return None


def find_all_ip_v4() -> list:
    results: list = list()
    for iface in netifaces.interfaces():
        try:
            inet_addresses = netifaces.ifaddresses(iface)[netifaces.AF_INET]
            lo: bool = False
            for inet_address in inet_addresses:
                if _ADDR_KEY in inet_address and inet_address[_ADDR_KEY].startswith('127'):
                    lo = True
                    break
            if lo:
                continue
            for inet_address in inet_addresses:
                if _ADDR_KEY in inet_address:
                    results.append(inet_address[_ADDR_KEY])
        except KeyError:
            pass
    return results


def find_local_mac_address(ip_v4: str) -> str:
    for iface in netifaces.interfaces():
        try:
            for inet_address in netifaces.ifaddresses(iface)[netifaces.AF_INET]:
                if _ADDR_KEY in inet_address and inet_address[_ADDR_KEY] == ip_v4:
                    for mac_address in netifaces.ifaddresses(iface)[netifaces.AF_LINK]:
                        if _ADDR_KEY in mac_address:
                            return mac_address[_ADDR_KEY].upper()
        except KeyError:
            pass
    return None


def find_ip_v4() -> str:
    addresses: list = find_all_ip_v4()
    if len(addresses) > 0:
        return addresses[0]
    return '127.0.0.1'


def scan_network(ip_v4: str) -> list:
    nm: nmap.PortScanner = nmap.PortScanner()
    net: str = ip_v4.rsplit('.', 1)[0] + '.0/24'
    # print('Scanning network:', net)
    nm.scan(hosts=net, arguments='-sPn', sudo=True)
    hosts: list = nm.all_hosts()
    unique_results: dict = dict()
    result: dict = dict()
    result[IP_V4_KEY] = find_ip_v4()
    result[MAC_ADDRESS_KEY] = find_local_mac_address(result[IP_V4_KEY])
    result[HOSTNAME_KEY] = socket.gethostbyaddr(result[IP_V4_KEY])[0]
    unique_results[result[IP_V4_KEY]] = result
    for host in hosts:
        data = nm[host]
        if data:
            addresses = data['addresses']
            hostnames = data['hostnames']
            vendor = data['vendor']
            if not addresses:
                continue
            ip: str = addresses['ipv4']
            result: dict = None
            if ip in unique_results:
                result = unique_results[ip]
            else:
                result = dict()
                result[IP_V4_KEY] = ip
            if 'mac' in addresses:
                result[MAC_ADDRESS_KEY] = addresses['mac'].upper()
                if vendor and result[MAC_ADDRESS_KEY] in vendor:
                    result[VENDOR_KEY] = vendor[result['mac']]
            if hostnames and len(hostnames) > 0 and 'name' in hostnames[0]:
                result[HOSTNAME_KEY] = hostnames[0]['name']
            unique_results[result[IP_V4_KEY]] = result
    results: list = list()
    for k, v in unique_results.items():
        results.append(v)
    return results


def is_reachable(ip_v4: str, mac_addresses: list, scan_results: list = None) -> bool:
    results: list = scan_results
    if scan_results is None:
        results = scan_network(ip_v4)
    for data in results:
        if MAC_ADDRESS_KEY in data:
            if data[MAC_ADDRESS_KEY] in mac_addresses:
                return True
    return False
