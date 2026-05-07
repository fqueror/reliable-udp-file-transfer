from mininet.node import OVSController
from mininet.term import tunnelX11
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.log import error
from mininet.cli import CLI


class MultipleHostsOneSwitch(Topo):
    def build(self):
        switch = self.addSwitch('s1')

        server = self.addHost('server')
        client1 = self.addHost('client1')
        client2 = self.addHost('client2')
        client3 = self.addHost('client3')
        client4 = self.addHost('client4')

        self.addLink(server, switch, cls=TCLink, loss=10)
        self.addLink(client1, switch, cls=TCLink)
        self.addLink(client2, switch, cls=TCLink)
        self.addLink(client3, switch, cls=TCLink)
        self.addLink(client4, switch, cls=TCLink)


class CustomCLI(CLI):
    """
    AI-generated with the sole purpose of providing us with a better `xterm`
    experience; mainly because the default's font size is too small.
    """

    def _make_xterm(self, node):
        display, tunnel = tunnelX11(node, None)
        if display is None:
            return []

        command = [
            'xterm',
            '-title', '"%s"' % node.name,
            '-fa', 'Monospace',
            '-fs', "10",
            '-display', display,
            '-e', 'env TERM=ansi bash'
        ]
        terminal = node.popen(command)
        return [tunnel, terminal] if tunnel else [terminal]

    def do_xterm(self, line, term='xterm'):
        """Spawn xterm(s) for the given node(s) with custom font size."""
        if term != 'xterm':
            return super().do_xterm(line, term=term)

        args = line.split()
        if not args:
            error('Usage: `xterm server client1 …`\n')
            return

        for arg in args:
            if arg not in self.mn:
                error("node '%s' not in network\n" % arg)
                continue
            node = self.mn[arg]
            self.mn.terms += self._make_xterm(node)


if __name__ == '__main__':
    net = Mininet(topo=MultipleHostsOneSwitch(), controller=OVSController,
                  link=TCLink)

    net.start()
    CustomCLI(net)  # Run the CLI for user interaction.

    net.stop()
