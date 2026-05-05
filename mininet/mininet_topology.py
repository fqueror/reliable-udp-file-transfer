from mininet.node import OVSController
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.cli import CLI


class MultipleHostsOneSwitch(Topo):
    # TODO Debemos lograr tener _loss_ de 10% y subir/bajar archivos de 5MBs en
    # TODO menos de 2 mins.
    def build(self, loss=0):
        switch = self.addSwitch('s1')  # Create a switch.

        # Create two hosts:
        server = self.addHost('server')
        client1 = self.addHost('client1')
        client2 = self.addHost('client2')

        # Connect hosts to the switch:
        self.addLink(server, switch, cls=TCLink)
        self.addLink(client1, switch, cls=TCLink, loss=loss)
        self.addLink(client2, switch, cls=TCLink, loss=loss)


if __name__ == '__main__':
    setLogLevel('info')

    net = Mininet(topo=MultipleHostsOneSwitch(loss=5.1),
                  controller=OVSController,
                  link=TCLink)
    net.start()

    CLI(net)  # Run the CLI for user interaction.

    net.stop()
