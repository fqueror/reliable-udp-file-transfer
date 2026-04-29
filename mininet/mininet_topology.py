
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.node import OVSController

class TwoHostOneSwitchTopology(Topo):
    def build(self):
        # Create a switch
        switch = self.addSwitch('s1')

        # Create two hosts
        #cliente
        host1 = self.addHost('h1')
        #servidor
        host2 = self.addHost('h2')

        # Connect hosts to the switch
        self.addLink(host1, switch)
        self.addLink(host2, switch)
    
if __name__ == '__main__':

    setLogLevel('info')

    # Create the network with the custom topology
    topo = TwoHostOneSwitchTopology()
    net = Mininet(topo=topo, controller=OVSController)

    # Start the network
    net.start()

    # Run the CLI for user interaction
    CLI(net)

    # Stop the network after exiting the CLI
    net.stop()