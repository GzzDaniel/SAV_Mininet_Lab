#!/usr/bin/env python3

"""
this module does not filter, only logs source IPs of packets that hit the queue.
"""

from netfilterqueue import NetfilterQueue
from scapy.all import IP
import subprocess

def handle_packet(pkt):
    packet = IP(pkt.get_payload())
    src_ip = packet.src

    # Append src IP to log file
    with open("/home/ubuntu/urpf-demo/logs/base_log.txt", "a") as f:
        f.write(src_ip + "\n")
        f.flush()

    pkt.accept()

if __name__ == "__main__":
    nfq = NetfilterQueue()
    nfq.bind(1, handle_packet)

    try:
        print("Logging packet source IPs to logs/base_log.txt")
        nfq.run()
    except KeyboardInterrupt:
        print("\nStopping.")
    
    nfq.unbind()
