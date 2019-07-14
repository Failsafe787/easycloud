"""
Openstack configuration manager
"""

import logging

from core.metaconfmanager import MetaConfManager

__author__ = "Davide Monfrecola, Stefano Garione, Giorgio Gambino, Luca Banzato"
__copyright__ = "Copyright (C) 2019"
__credits__ = ["Andrea Lombardo", "Irene Lovotti"]
__license__ = "GPL v3"
__version__ = "0.10.0"
__maintainer__ = "Luca Banzato"
__email__ = "20005492@studenti.uniupo.it"
__status__ = "Prototype"


class ChameleonCloudConfManager(MetaConfManager):

    def __init__(self):
        """
        Init method (object initialization)
        """
        super().__init__("chameleon_libcloud")

    def read_login_data(self):
        """
        Read login data from settings.cfg
        """
        # URL Regex took from http://www.noah.org/wiki/RegEx_Python#URL_regex_pattern
        self.os_auth_url = self.get_parameter("openstack", "os_auth_url",
                                              return_type=str,
                                              regex="http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
        self.os_username = self.get_parameter("openstack", "os_username", return_type=str)
        self.os_password = self.get_parameter("openstack", "os_password", return_type=str)
        self.os_project_name = self.get_parameter("openstack", "os_project_name", return_type=str)
        self.os_project_id = self.get_parameter("openstack", "os_project_id", return_type=str)
        self.os_region = self.get_parameter("openstack", "os_region", return_type=str)
        logging.debug("OpenStack login data read")

    def read_platform_options(self):
        self.demo_reservation_id = self.get_parameter("re_demo", "demo_reservation_id", return_type=str)
        """
        Read platform-specific options from settings.cfg
        """
        # Nothing to do here
        pass
