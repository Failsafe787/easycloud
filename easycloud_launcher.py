"""
EasyCloud Launcher script
"""

import logging
import os
import signal
import sys

from core.easycloud import EasyCloud

__author__ = "Davide Monfrecola, Stefano Garione, Giorgio Gambino, Luca Banzato"
__copyright__ = "Copyright (C) 2019"
__credits__ = ["Andrea Lombardo", "Irene Lovotti"]
__license__ = "GPL v3"
__version__ = "0.10.0"
__maintainer__ = "Luca Banzato"
__email__ = "20005492@studenti.uniupo.it"
__status__ = "Prototype"

VERSION = "0.10.0 (Preview)"


def signal_handler(signal, frame):
    """
    Handles a Ctrl+C command gracefully while executing the application

    Args:
        signal (<signal>): the signal to process
        frame (<stack_frame>): pointer of the frame that was interrupted by the signal
    """
    os.system("cls" if os.name == "nt" else "clear")
    logging.debug("Ctrl+C pressed. Application closed!")
    sys.exit(0)


def help():
    """
    Print the help message
    """
    _help_message = "\n"
    _help_message += "EasyCloud " + VERSION + "\n"
    _help_message += "Usage: easycloud.sh [--libcloud-debug] || [--no-libs-check] || [--help] || [--version]\n"
    _help_message += "\n"
    _help_message += "Optional arguments:\n"
    _help_message += "    --libcloud-debug    display all the outgoing HTTP requests and all the\n"
    _help_message += "                        incoming HTTP responses made by libcloud in logs/libcloud_debug.log\n"
    _help_message += "                        (This setting works only if the application has been executed using\n"
    _help_message += "                        the shipped shell script)\n"
    _help_message += "    --no-libs-check     disable the dependencies check for each module at the\n"
    _help_message += "                        start of EasyCloud"
    _help_message += "    --help              display this message\n"
    _help_message += "    --version           display the application version\n"
    print(_help_message)


def version():
    """
    Print the application version
    """
    print(VERSION)


def run_debug():
    """
    Run the application with debug flags
    """
    print("Debug Mode for Libcloud can only be activated through the shell script shipped with EasyCloud!")


def run(no_libs_check=False):
    """
    Start EasyCloud

    Args:
        no_libs_check (bool, optional): disable libraries check at each module loading phase (default: False)
    """
    logging.basicConfig(filename="logs" + os.sep + "easycloud.log",
                        format="[%(levelname)s] %(asctime)s - %(module)s(line %(lineno)d): %(message)s",
                        datefmt="%d/%m/%Y, %H:%M:%S",
                        level=logging.DEBUG,
                        filemode="a")
    signal.signal(signal.SIGINT, signal_handler)
    easycloud = EasyCloud()
    easycloud.start(no_libs_check=no_libs_check)


if __name__ == "__main__":

    if len(sys.argv) == 1:
        run()
    elif len(sys.argv) == 2:
        if sys.argv[1] == "--libcloud-debug":
            run_debug()
        elif sys.argv[1] == "--version":
            version()
        elif sys.argv[1] == "--no-libs-check":
            run(no_libs_check=True)
        else:
            help()
    else:
        help()
