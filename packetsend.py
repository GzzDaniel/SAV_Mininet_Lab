#!/usr/bin/env python3

from scapy.all import IP, UDP, Raw, send, ICMP

def main():
    d4address = "10.102.0.251"
    d1address = "10.100.0.251"
    d3address = "10.101.0.251"
    d5address = "10.105.0.251"
    r2address = "10.1.0.0"
    notInTopology = "10.5.0.2"
    
    # writing a message helps confirm the packet received was this script
    payload = "HELLO FROM D3"
    
    packet = (
    IP(src= r2address, dst=d1address) /
    UDP(sport=4444, dport=9999) /
    Raw(load=payload)
    )

    print("[*] Sending UDP packet with payload: '{}'".format(payload))
    send(packet, count=1, verbose=1)
    print("[*] Done.")

if __name__ == "__main__":
    main()