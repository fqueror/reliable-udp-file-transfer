from lib.settings import UPLOAD, DOWNLOAD, START_SERVER, LOW_VERBOSITY, \
    HIGH_VERBOSITY
from lib.protocol.stop_and_wait import STOP_AND_WAIT_ID
from lib.protocol.go_back_n import GO_BACK_N_ID
from lib.protocol.protocol import Protocol
import argparse
import pathlib


class SpacedHelpFormatter(argparse.HelpFormatter):
    def _format_action_invocation(self, action):
        if not action.option_strings:
            return super()._format_action_invocation(action)

        return ", ".join(action.option_strings)


def get_args(prog: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=prog,
                                     formatter_class=SpacedHelpFormatter)

    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument("-q", "--quiet", action="store_true",
                                 help="decrease output verbosity")
    verbosity_group.add_argument("-v", "--verbose", action="store_true",
                                 help="increase output verbosity")

    if prog == UPLOAD or prog == DOWNLOAD:
        parser.add_argument("-H", "--host", action="store",
                            help="server IP address", metavar="ADDR")
        parser.add_argument("-p", "--port", action="store", type=int,
                            help="server port")

        if prog == UPLOAD:
            parser.add_argument("-s", "--src", action="store",
                                type=pathlib.Path, required=True,
                                help="source file path", metavar="FILEPATH")
        elif prog == DOWNLOAD:
            parser.add_argument("-d", "--dst", action="store",
                                default=pathlib.Path("."), type=pathlib.Path,
                                help="destination file path",
                                metavar="FILEPATH")

        parser.add_argument("-n", "--name", action="store", help="file name",
                            metavar="FILENAME")
        parser.add_argument("-r", "--protocol", action="store",
                            choices=[STOP_AND_WAIT_ID, GO_BACK_N_ID],
                            help="error recovery protocol", metavar="PROTOCOL")

    elif prog == START_SERVER:
        parser.add_argument("-H", "--host", action="store", default="0.0.0.0",
                            help="service IP address", metavar="ADDR")
        parser.add_argument("-p", "--port", action="store", type=int,
                            help="service port")
        parser.add_argument("-s", "--storage", action="store",
                            help="storage directory path", metavar="DIRPATH")

    return parser.parse_args()


def validate_args(args: argparse.Namespace):
    if args.host is None or args.port is None:
        print("Host and port must be specified.")
        exit(1)

    protocol = Protocol.from_str(args.protocol)
    if args.quiet:
        protocol.set_verbosity_level(LOW_VERBOSITY)
    elif args.verbose:
        protocol.set_verbosity_level(HIGH_VERBOSITY)

    return protocol
