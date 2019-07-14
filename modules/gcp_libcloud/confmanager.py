"""
Google Cloud Platform configuration manager
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


class GCPConfManager(MetaConfManager):

    def __init__(self):
        """
        Init method (object initialization)
        """
        super().__init__("gcp_libcloud")

    def read_login_data(self):
        """
        Read login data from settings.cfg
        """
        self.gcp_access_key_id = self.get_parameter("gcp", "gcp_access_key_id", return_type=str)
        self.gcp_secret_access_key = self.get_parameter("gcp", "gcp_secret_access_key", return_type=str)
        self.gcp_datacenter = self.get_parameter("gcp", "gcp_datacenter", return_type=str)
        self.gcp_project = self.get_parameter("gcp", "gcp_project", return_type=str)
        # URL Regex took from http://www.noah.org/wiki/RegEx_Python#URL_regex_pattern
        self.gcp_auth_uri = self.get_parameter("gcp", "gcp_auth_uri",
                                               return_type=str,
                                               regex="http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
        self.gcp_token_uri = self.get_parameter("gcp", "gcp_token_uri",
                                                return_type=str,
                                                regex="http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
        self.gcp_redirect_uri = self.parser.get("gcp", "gcp_redirect_uri").replace(
            " ", "").replace("\n", "").split(",")
        logging.debug("GCP login data read")

    def read_platform_options(self):
        """
        Read platform-specific options from settings.cfg
        """
        # Always Free settings
        self.alwaysfree_only = self.get_parameter("alwaysfree", "alwaysfree_only", return_type=bool)
        self.alwaysfree_instance_types = self.parser.get(
            "alwaysfree", "alwaysfree_instance_types").replace(" ", "").replace("\n", "").split(",")
        self.alwaysfree_zones = self.parser.get(
            "alwaysfree", "alwaysfree_zones").replace(" ", "").replace("\n", "").split(",")
        logging.debug("GCP platform options read")
