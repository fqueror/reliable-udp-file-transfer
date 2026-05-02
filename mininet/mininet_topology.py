from mininet.node import OVSController
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.cli import CLI


class TwoHostsOneSwitch(Topo):
    def build(self, loss=0):
        switch = self.addSwitch('s1')  # Create a switch.

        # Create two hosts:
        server = self.addHost('server')
        client = self.addHost('client')

        # Connect hosts to the switch:
        self.addLink(server, switch, cls=TCLink)
        self.addLink(client, switch, cls=TCLink, loss=loss)


if __name__ == '__main__':
    setLogLevel('info')

    net = Mininet(topo=TwoHostsOneSwitch(loss=5.1), controller=OVSController,
                  link=TCLink)
    net.start()

    CLI(net)  # Run the CLI for user interaction.

    net.stop()
