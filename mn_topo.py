#!/usr/bin/python3
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI


class LinuxRouter(Node):
    def config(self, **params):
        super(LinuxRouter, self).config(**params)

    def terminate(self):
        super(LinuxRouter, self).terminate()


class NetworkTopo(Topo):
    def build(self, **_opts):
        # Add 2 routers with two different subnets
        r1 = self.addHost('r1', cls=LinuxRouter, ip='10.1.0.1/24')
        r2 = self.addHost('r2', cls=LinuxRouter, ip='10.1.0.2/24')
        r3 = self.addHost('r3', cls=LinuxRouter, ip='10.2.0.2/24')
        r4 = self.addHost('r4', cls=LinuxRouter, ip='10.3.0.2/24')
        r5 = self.addHost('r5', cls=LinuxRouter, ip='10.5.0.2/24')

        # Add 2 switches, two for each subnet
        s1 = self.addSwitch('s1')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')
        s5 = self.addSwitch('s5')

        # Add router-router link in a new subnet
        self.addLink(r1,
                     r2,
                     intfName1='r1-eth1',
                     intfName2='r2-eth1',
                     params1={'ip': '10.1.0.1/24'},
                     params2={'ip': '10.1.0.2/24'})
        self.addLink(r2,
                     r3,
                     intfName1='r2-eth2',
                     intfName2='r3-eth1',
                     params1={'ip': '10.2.0.1/24'},
                     params2={'ip': '10.2.0.2/24'})
        self.addLink(r3,
                     r4,
                     intfName1='r3-eth2',
                     intfName2='r4-eth1',
                     params1={'ip': '10.3.0.1/24'},
                     params2={'ip': '10.3.0.2/24'})
        self.addLink(r1,
                     r4,
                     intfName1='r1-eth3',
                     intfName2='r4-eth3',
                     params1={'ip': '10.4.0.1/24'},
                     params2={'ip': '10.4.0.2/24'})
        self.addLink(r2,
                     r5,
                     intfName1='r2-eth3',
                     intfName2='r5-eth1',
                     params1={'ip': '10.5.0.1/24'},
                     params2={'ip': '10.5.0.2/24'})

        # Connect switches to routers
        self.addLink(s1,
                     r1,
                     intfName2='r1-eth2',
                     params2={'ip': '10.100.0.1/24'})

        self.addLink(s3,
                     r3,
                     intfName2='r3-eth3',
                     params2={'ip': '10.101.0.1/24'})

        self.addLink(s4,
                     r4,
                     intfName2='r4-eth2',
                     params2={'ip': '10.102.0.1/24'})
        
        self.addLink(s5,
                     r5,
                     intfName2='r4-eth2',
                     params2={'ip': '10.105.0.1/24'})


        # Adding hosts with a default route
        d1 = self.addHost(name='d1',
                          ip='10.100.0.251/24',
                          defaultRoute='via 10.100.0.1')
        d3 = self.addHost(name='d3',
                          ip='10.101.0.251/24',
                          defaultRoute='via 10.101.0.1')
        d4 = self.addHost(name='d4',
                          ip='10.102.0.251/24',
                          defaultRoute='via 10.102.0.1')
        d5 = self.addHost(name='d5',
                          ip='10.105.0.251/24',
                          defaultRoute='via 10.105.0.1')
 
        # Add host-switch links
        self.addLink(d1, s1)
        self.addLink(d3, s3)
        self.addLink(d4, s4)
        self.addLink(d5, s5)
def run():
    topo = NetworkTopo()
    net = Mininet(topo=topo)

    info(net['r1'].cmd("/usr/lib/frr/frrinit.sh start 'r1'"))
    info(net['r2'].cmd("/usr/lib/frr/frrinit.sh start 'r2'"))
    info(net['r3'].cmd("/usr/lib/frr/frrinit.sh start 'r3'"))
    info(net['r4'].cmd("/usr/lib/frr/frrinit.sh start 'r4'"))
    info(net['r5'].cmd("/usr/lib/frr/frrinit.sh start 'r5'"))

    net.start()
    CLI(net)

    info(net['r1'].cmd("/usr/lib/frr/frrinit.sh stop 'r1'"))
    info(net['r2'].cmd("/usr/lib/frr/frrinit.sh stop 'r2'"))
    info(net['r3'].cmd("/usr/lib/frr/frrinit.sh stop 'r3'"))
    info(net['r4'].cmd("/usr/lib/frr/frrinit.sh stop 'r4'"))
    info(net['r5'].cmd("/usr/lib/frr/frrinit.sh stop 'r5'"))

    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()


