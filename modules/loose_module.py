#!/usr/bin/env python3

from netfilterqueue import NetfilterQueue
from scapy.all import IP
import subprocess

LOGFILE = "/home/ubuntu/urpf-demo/logs/loose_log.txt"

def handle_packet(pkt):
    packet = IP(pkt.get_payload())
    src_ip = packet.src

   # Check if any route exists for the source IP
    result = subprocess.run(
        ["ip", "route", "get", src_ip],
        capture_output=True, text=True
    )

    if result.returncode == 0:
        # A route exists — ACCEPT
        with open(LOGFILE, "a") as f:
            f.write(f"[ACCEPT] src={src_ip} route exists: {result.stdout.strip()}\n")
            f.flush()
        pkt.accept()
    else:
        # No route exists — DROP
        with open(LOGFILE, "a") as f:
            f.write(f"[DROP] src={src_ip} no route found\n")
            f.flush()
        pkt.drop()


if __name__ == "__main__":
    nfq = NetfilterQueue()
    nfq.bind(1, handle_packet)

    try:
        print("Logging packet source IPs to logs/loose_log.txt")
        nfq.run()
    except KeyboardInterrupt:
        print("\nStopping.")
    
    nfq.unbind()
