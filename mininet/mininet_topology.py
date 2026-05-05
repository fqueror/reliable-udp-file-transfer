from mininet.node import OVSController
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.cli import CLI


class MultipleHostsOneSwitch(Topo):
    def build(self):
        switch = self.addSwitch('s1')  # Create a switch.

        # Create two hosts:
        server = self.addHost('server')
        client1 = self.addHost('client1')
        client2 = self.addHost('client2')

        # Connect hosts to the switch:
        self.addLink(server, switch, cls=TCLink, loss=10)
        self.addLink(client1, switch, cls=TCLink)
        self.addLink(client2, switch, cls=TCLink)


if __name__ == '__main__':
    setLogLevel('info')

    net = Mininet(topo=MultipleHostsOneSwitch(), controller=OVSController,
                  link=TCLink)
    net.start()

    CLI(net)  # Run the CLI for user interaction.

    net.stop()
