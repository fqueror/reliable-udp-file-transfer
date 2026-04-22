from .protocol import Protocol
import pathlib
import argparse


class SpacedHelpFormatter(argparse.HelpFormatter):
    def _format_action_invocation(self, action):
        if not action.option_strings:
            return super()._format_action_invocation(action)

        return ", ".join(action.option_strings)


def get_args(prog):
    parser = argparse.ArgumentParser(
        prog=prog, formatter_class=SpacedHelpFormatter)

    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument("-v", "--verbose", action="store_true",
                                 help="increase output verbosity")
    verbosity_group.add_argument(
        "-q", "--quiet", action="store_true", help="decrease output verbosity")

    if prog == "upload" or prog == "download":
        parser.add_argument("-H", "--host", metavar="ADDR",
                            action="store", help="server IP address")
        parser.add_argument("-p", "--port", action="store", type=int,
                            help="server port")

        if prog == "upload":
            parser.add_argument("-s", "--src", metavar="FILEPATH",
                                action="store", type=pathlib.Path,
                                help="source file path")
        elif prog == "download":
            parser.add_argument("-d", "--dst", metavar="FILEPATH",
                                action="store", type=pathlib.Path,
                                help="destination file path")

        parser.add_argument("-n", "--name",  metavar="FILENAME",
                            action="store", help="file name")
        parser.add_argument("-r", "--protocol", metavar="PROTOCOL",
                            action="store", type=Protocol.from_str,
                            help="error recovery protocol")

    elif prog == "start-server":
        parser.add_argument("-H", "--host", metavar="ADDR",
                            action="store", help="service IP address")
        parser.add_argument("-p", "--port", action="store", type=int,
                            help="service port")
        parser.add_argument("-s", "--storage", metavar="DIRPATH",
                            action="store", type=pathlib.Path,
                            help="storage directory path")

    return parser.parse_args()
