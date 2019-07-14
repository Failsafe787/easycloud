"""
A simple script that allows the installation of all the libraries required
in order to use the plugins provided with EasyCloud
"""

import json
import os
import subprocess
import sys

__author__ = "Luca Banzato"
__copyright__ = "Copyright (C) 2019"
__credits__ = ["Greenstick"]
__license__ = "GPL v3"
__version__ = "0.10.0"
__maintainer__ = "Luca Banzato"
__email__ = "20005492@studenti.uniupo.it"
__status__ = "Prototype"


def printProgress(iteration, total, description, prefix="", suffix=""):
    """
    Progress function based on ProgressBar by Greenstick (https://stackoverflow.com/users/2206251/greenstick)

    Args:
        iteration (int): current iteration
        total (int): total iterations
        description (str): description string
        prefix (str, optional): prefix string
        suffix (str, optional): suffix string
    """
    print("%s %s/%s: %s %s" % (prefix, iteration, total, description, suffix))


def checkPythonVersion():
    """
    Checks if this program is runned using Python 3

    Raises:
        Exception: an exception if python3 is not used.
    """
    if sys.version_info[0] != 3:  # get python major version
        raise Exception("This program requires Python 3. You're running Python " + str(
            sys.version_info[0]) + "." + str(sys.version_info[1]) + "." + str(sys.version_info[2]) + ".")


def checkPip():
    """
    Checks if the python3-pip package is installed

    Raises:
        Exception: an exception if pip3 is not used.
    """
    try:
        global pip
        import pip
    except ImportError:
        raise Exception(
            "You need to install the \"python3-pip\" package before running this installer.")


def checkIntegrity():
    """
    Checks if the installer is corrupted or has missing files

    Raises:
        Exception: an exception if the "packages" file is missing or corrupted
    """
    # check if packages is a file in the working directory
    if (os.path.isfile("." + os.sep + "packages") is False):
        raise Exception(
            "Integrity check failed due to missing \"packages\" file. Please, obtain a new copy of this installer and try again.")


def installPackage(name, pip_package):
    """
    Installs a pip package and saves the installation informations inside a log file

    Args:
        name (str): package name
        pip_package (str): pip package identifier or url

    Raises:
        Exception: Description
        subprocess.CalledProcessError: Description
    """
    try:
        logfile = open("installer.log", "a+")  # open log in append mode
        subproc = subprocess.Popen([sys.executable, "-m", "pip", "install", "--user",
                                    pip_package], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in subproc.stdout:
            # write the subprocess stdout to the log file
            logfile.write(line.decode(sys.stdout.encoding))
        logfile.close()
        subproc.wait()
        if subproc.returncode:  # raise an exception if the installation encountered a problem
            raise subprocess.CalledProcessError(
                subproc.returncode, " ".join(subproc.args))
    except subprocess.CalledProcessError:
        raise Exception("There was an error while installing the \"" +
                        name + "\" package. Please check the installer.log for details.")


def main():
    """
    The main application
    """
    print("\n")
    print("======================================")
    print("  EasyCloud core libraries installer  ")
    print("======================================")
    print("\n")
    try:
        checkPythonVersion()
        checkIntegrity()
        checkPip()
        print("Installing packages")
        with open('packages') as packages_list:
            try:
                data = json.load(packages_list)
            except Exception:
                raise Exception(
                    "There was an error while reading \"packages\" file. Please check if it is in a valid JSON format.")
            packagesNumber = len(data["packages"])
            currentPackage = 1
            for package in data["packages"]:
                printProgress(currentPackage, packagesNumber, package[
                              "name"], prefix="Installing")
                installPackage(package["name"], package["pip_package"])
                currentPackage += 1
        print("Installation finished!")
    except Exception as e:
        print(str(e) + "\n\nInstallation aborted.\n")


main()
