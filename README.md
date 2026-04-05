# SAV_Mininet_Lab

Lab to test Source Address Validation methods using mininet emulation and FRR open source routing
strict and loose are provided by the linux OS
use vtysh to access routing console

the router configuration can be found in the rn folders where n is the number of the router.
the routers are configured for bgp where r3 can be easily set to prefer routing to r2 or r4.

- quick demo -
run config_frr.sh to install the router configurations in each namespace

use packetsend.py to send a spoofed packet from d3 to d1
sav loose might be enabled in some network components by os default

credits:

this article helped me set up the lab
https://medium.com/@jmwanderer/fun-with-routing-protocols-8a0677aab2fc

made for CSE4402-Network Security by Professor Amir Herzberg for my Fall 2025 semester
targetRIBtables.png was made using https://bgpsimulator.com/