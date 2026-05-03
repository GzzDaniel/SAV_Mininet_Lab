#!/usr/bin/env python3

import os
import sys
import subprocess
from netfilterqueue import NetfilterQueue
from scapy.all import IP, TCP
from scapy.contrib.bgp import BGPHeader, BGPUpdate


LOGFILE = f"/home/ubuntu/urpf-demo/logs/feasible_log.txt"


def log(msg):
    with open(LOGFILE, "a") as f:
        f.write(msg + "\n")
        f.flush()
        
def log_packet(packet, pkt):
    src_ip = packet[IP].src
    dst_ip = packet[IP].dst
    packet_interface = get_packet_interface(pkt)
    has_bgp = packet.haslayer(BGPHeader)
    layers = packet.summary()

    if packet.haslayer(TCP):
        sport = packet[TCP].sport
        dport = packet[TCP].dport
        flags = packet[TCP].flags
        log(f"[PKT] src={src_ip} dst={dst_ip} iface={packet_interface} proto=TCP sport={sport} dport={dport} flags={flags} bgp={has_bgp}")
        log(f"[PKT] layers={layers}")
    elif packet.haslayer(UDP):
        sport = packet[UDP].sport
        dport = packet[UDP].dport
        log(f"[PKT] src={src_ip} dst={dst_ip} iface={packet_interface} proto=UDP sport={sport} dport={dport} bgp={has_bgp}")
        log(f"[PKT] layers={layers}")
    else:
        log(f"[PKT] src={src_ip} dst={dst_ip} iface={packet_interface} proto={packet.proto} bgp={has_bgp}")
        log(f"[PKT] layers={layers}")

def get_packet_interface(pkt):
    """used to get interface packet arrived on for non BGP packets"""
    # nfqueue provides the interface index, we convert it to a name
    result = subprocess.run(
        ["ip", "link", "show"],
        capture_output=True, text=True
    )
    ifindex = pkt.indev  # gets number of interface packet arrived on
    # gets interface name based on number
    for line in result.stdout.splitlines():
        if line.startswith(f"{ifindex}:"):
            return line.split(":")[1].strip().split("@")[0]
    # packets leaving router will return indev 0, which is not in iplink show output
    return None

def srcIP_to_interface(nexthop_ip):
    """Given a nexthop IP, return the local interface used to reach it"""
    result = subprocess.run(
        ["ip", "route", "get", nexthop_ip],
        capture_output=True, text=True
    )
    if result.returncode == 0 and "dev" in result.stdout:
        return result.stdout.split("dev")[1].strip().split()[0]
    return None


bgp_neighbors = set()

def load_bgp_neighbors(router_name):
    """Parse neighbor IPs from /etc/frr/{router_name}/frr.conf"""
    conf_path = f"/etc/frr/{router_name}/frr.conf"
    neighbors = set()
    try:
        with open(conf_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("neighbor ") and "remote-as" in line:
                    neighbors.add(line.split()[1])
        log(f"[CONFIG] Loaded {len(neighbors)} BGP neighbors from {conf_path}: {neighbors}")
    except FileNotFoundError:
        log(f"[CONFIG] {conf_path} not found — BGP packets from all peers will be dropped")
    return neighbors


# prefix -> list of interfaces that announced it
# e.g. {"10.101.0.0/24": ["r1-eth1", "r1-eth3"]}
bgp_rib = {}
def updateRIB(packet):
    """updates the RIB table given a bgp packet

    BGP message types (RFC 4271):
      1 - OPEN:         initiates a BGP session; exchanges version, AS number, hold time, and BGP identifier
      2 - UPDATE:       advertises new routes or withdraws previously announced routes
      3 - NOTIFICATION: reports an error condition; the session is closed immediately after sending
      4 - KEEPALIVE:    confirms the session is still alive (sent periodically within the hold time)
      5 - ROUTE-REFRESH: requests a peer to re-advertise its Adj-RIB-Out (RFC 2918)
    """
    try:
        bgp = packet[BGPHeader]
        # in case there are multiple bgp messages
        while bgp:
            if bgp.type == 2:  # UPDATE message
                update = BGPUpdate(bytes(bgp.payload))

                # resolve the peer IP to a local interface
                peer_ip = packet[IP].src
                iface = resolve_nexthop_to_iface(peer_ip)

                if iface is None:
                    log(f"[BGP] Could not resolve interface for peer {peer_ip}")
                    bgp = bgp.payload.payload if hasattr(bgp.payload, 'payload') else None
                    continue

                # parse announced prefixes (NLRI)
                # if statement prevents attribvute error
                if hasattr(update, 'nlri') and update.nlri:
                    for prefix in update.nlri:
                        prefix_str = str(prefix.prefix) + "/" + str(prefix.prefixlen)
                        if prefix_str not in bgp_rib:
                            bgp_rib[prefix_str] = []
                        if iface not in bgp_rib[prefix_str]:
                            bgp_rib[prefix_str].append(iface)
                        log(f"[BGP] UPDATE prefix={prefix_str} via peer={peer_ip} iface={iface}")

                # parse withdrawn prefixes
                if hasattr(update, 'withdrawn_routes') and update.withdrawn_routes:
                    for prefix in update.withdrawn_routes:
                        prefix_str = str(prefix.prefix) + "/" + str(prefix.prefixlen)
                        if prefix_str in bgp_rib and iface in bgp_rib[prefix_str]:
                            bgp_rib[prefix_str].remove(iface)
                            log(f"[BGP] WITHDRAW prefix={prefix_str} via peer={peer_ip} iface={iface}")
                        if prefix_str in bgp_rib and not bgp_rib[prefix_str]:
                            del bgp_rib[prefix_str]

            if hasattr(bgp.payload, 'payload'):
                bgp = bgp.payload.payload  
            else:
                bgp = None

    except Exception as e:
        log(f"[BGP] Parse error: {e}")

def get_feasible_interfaces(src_ip):
    """Look up feasible interfaces for a source IP from our local BGP RIB"""
    matched = []
    for prefix, ifaces in bgp_rib.items():
        net, length = prefix.split("/")
        # check if src_ip falls within this prefix
        import ipaddress
        if ipaddress.ip_address(src_ip) in ipaddress.ip_network(prefix, strict=False):
            matched.extend(ifaces)
    return list(set(matched))

def check_feasible_urpf(pkt, packet):
    src_ip = packet[IP].src
    packet_interface = get_packet_interface(pkt)

    feasible_interfaces = get_feasible_interfaces(src_ip)

    # fall back to kernel routing table if RIB has no entry yet
    if not feasible_interfaces:
        result = subprocess.run(
            ["ip", "route", "show", "match", src_ip],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "dev" in line:
                    iface = line.split("dev")[1].strip().split()[0]
                    if iface not in feasible_interfaces:
                        feasible_interfaces.append(iface)

    if not feasible_interfaces:
        log(f"[DROP] src={src_ip} no route found")
        pkt.drop()
        return

    if packet_interface is None:
        log(f"[DROP] src={src_ip} could not determine incoming interface")
        pkt.drop()
        return

    if packet_interface in feasible_interfaces:
        log(f"[ACCEPT] src={src_ip} arrived on {packet_interface} feasible={feasible_interfaces}")
        pkt.accept()
    else:
        log(f"[DROP] src={src_ip} arrived on {packet_interface} not in feasible={feasible_interfaces}")
        pkt.drop()

def handle_packet(pkt):
    packet = IP(pkt.get_payload())
    log_packet(packet, pkt)
    if packet.haslayer(TCP):
        
        if (flags == "S") or (flags == "SA") or (flags == "A") or (flags == "FA") or (flags == "FPA"):
            pkt.accept()
            return
        if packet.haslayer(BGPHeader):
            src_ip = packet[IP].src
            if src_ip not in bgp_neighbors:
                log(f"[DROP] BGP from unconfigured peer {src_ip}")
                pkt.drop()
                return
            updateRIB(packet)
            pkt.accept()
            return
        pkt.drop()  # port 179 but no BGPHeader and not a known TCP flag
        return
    
    # non-BGP traffic — run feasible path uRPF check
    #check_feasible_urpf(pkt, packet)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: feasible_module.py <router-name>  (e.g. r1)")
        sys.exit(1)
    bgp_neighbors = load_bgp_neighbors(sys.argv[1])

    nfq = NetfilterQueue()
    nfq.bind(1, handle_packet)

    try:
        log("Feasible path uRPF running, logging to logs/feasible_log.txt")
        nfq.run()
    except KeyboardInterrupt:
        print("\nStopping.")

    nfq.unbind()