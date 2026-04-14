#!/usr/bin/env python3

from netfilterqueue import NetfilterQueue
from scapy.all import IP
import subprocess

LOGFILE = "/home/ubuntu/urpf-demo/logs/strict_log.txt"

def get_expected_interface(src_ip):
    result = subprocess.run(
        ["ip", "route", "get", src_ip],
        capture_output=True, text=True
    )
    if result.returncode == 0 and "dev" in result.stdout:  # make sure dev is in output to ve able to split the string in case output is successful but empty
        return result.stdout.split("dev")[1].strip().split()[0]
    # didnt find interface
    return None

def get_packet_interface(pkt):
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

def handle_packet(pkt):
    packet = IP(pkt.get_payload())
    src_ip = packet.src

    expected_interface = get_expected_interface(src_ip)
    packet_interface = get_packet_interface(pkt)

    if expected_interface is None:
        with open(LOGFILE, "a") as f:
            f.write(f"[DROP] src={src_ip} no route found\n")
            f.flush()
        pkt.drop()
        return

    if packet_interface == expected_interface:
        with open(LOGFILE, "a") as f:
            f.write(f"[ACCEPT] src={src_ip} arrived on {packet_interface} expected {expected_interface}\n")
            f.flush()
        pkt.accept()
    else:
        with open(LOGFILE, "a") as f:
            f.write(f"[DROP] src={src_ip} arrived on {packet_interface} but expected {expected_interface}\n")
            f.flush()
        pkt.drop()


if __name__ == "__main__":
    nfq = NetfilterQueue()
    nfq.bind(1, handle_packet)

    try:
        print("Strict uRPF running, logging to logs/strict_log.txt")
        nfq.run()
    except KeyboardInterrupt:
        print("\nStopping.")

    nfq.unbind()
