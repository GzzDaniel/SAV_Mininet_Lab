# 🛡️ Source Address Validation Lab (Mininet + FRR)

A hands-on lab for experimenting with **Source Address Validation (SAV)** techniques using:

- 🧪 Mininet (network emulation)
- 🧭 FRRouting (FRR)
- 🐧 Linux kernel features (rp_filter)

---

## 📌 Overview

This lab demonstrates how different SAV methods behave in a simulated network environment.

- **Strict mode** and **Loose mode** are implemented by the Linux OS
- Routing is handled using **BGP via FRR**
- Use `vtysh` to access router configurations

Each router is preconfigured and organized into folders:

```
r1/
r2/
r3/
r4/
...
```

Router **r3** can be modified to prefer routing via:
- `r2` or
- `r4`

---

## ⚙️ Setup Instructions

This lab is to be used in a virtual machine with mininet. a virtual machine can be found in the following link https://medium.com/@jmwanderer/fun-with-routing-protocols-8a0677aab2fc

### 1. Configure routers

Run the setup script to load FRR configs into each namespace:

```bash
./config_frr.sh
```

---

### 2. Access router CLI

Use:

```bash
vtysh
```

Or per namespace:

```bash
vtysh -N r1
```

---

## 🚀 Quick Demo

### Send spoofed packet and read received contents

From host `d3`, run:

```bash
d1 tcpdump -nn -i d1-eth0 -w /home/ubuntu/bgp/d1_capture.pcap &
sudo ./packetsend.py
d1 pkill -INT tcpdump
d1 tcpdump -nn -XX -r d1_capture.pcap
```

This sends a ** packet** to `d1`.

---

## ⚠️ Notes

- Some nodes may already have **loose urpf enabled by default** via Linux kernel settings
- Behavior may vary depending on `rp_filter` configuration

---

## 🧠 Concepts Tested

- Source Address Validation (SAV)
- Strict vs Loose filtering
- BGP route selection impact on SAV
- Spoofed packet detection

---

## 📁 Project Structure

```
.
├── config_frr.sh        # Loads router configs
├── packetsend.py       # Sends spoofed packets
├── r1/                 # Router configs
├── r2/
├── r3/
├── r4/
└── targetRIBtables.png # Routing visualization
```

---

## 🙏 Credits

- Setup inspiration from:  
  https://medium.com/@jmwanderer/fun-with-routing-protocols-8a0677aab2fc

- RIB visualization created with:  
  https://bgpsimulator.com/

---

## 🎓 Academic Context

Created for:

**CSE4402 – Network Security**  
Professor Amir Herzberg  
Fall 2025