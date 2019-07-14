"""
A class representing a module of EasyCloud
"""

import modules

from configparser import SafeConfigParser
from importlib import import_module
from os import sep

__author__ = "Davide Monfrecola, Stefano Garione, Giorgio Gambino, Luca Banzato"
__copyright__ = "Copyright (C) 2019"
__credits__ = ["Andrea Lombardo", "Irene Lovotti"]
__license__ = "GPL v3"
__version__ = "0.10.0"
__maintainer__ = "Luca Banzato"
__email__ = "20005492@studenti.uniupo.it"
__status__ = "Prototype"


class Module:

    def __init__(self, platform):
        """
        Initializes parser object and reads all the informations regarding a module

        Args:
            platform (str): platform name
        """
        self.__platform = platform
        self.parser = SafeConfigParser()
        self.parser.read("modules" + sep + self.__platform + sep + "manifest.inf")
        self.read_plat_details()

    def read_plat_details(self):
        """
        Read platform details (name, etc)
        """
        self.platform_name = self.parser.get("manifest", "platform_name")
        self.package_name = self.parser.get("manifest", "package_name")
        self.manager_name = self.parser.get("manifest", "manager_name")
        self.dependencies = self.parser.get("manifest", "dependencies").replace(" ", "").replace("\n", "").split(",")
        self.module_version = self.parser.get("manifest", "module_version")
        self.release_date = self.parser.get("manifest", "release_date")
        self.license = self.parser.get("manifest", "license")
        self.author = self.parser.get("manifest", "author")
        self.email = self.parser.get("manifest", "email")

    def load_manager_class(self):
        """
        Assign a manager to this module
        """
        _manager = import_module(
            "." + self.package_name + "." + "manager", modules.__name__)
        self.manager_class = getattr(_manager, self.manager_name)
