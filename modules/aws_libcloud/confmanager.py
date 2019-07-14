"""
Amazon Web Services configuration manager
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


class AWSConfManager(MetaConfManager):

    def __init__(self):
        """
        Init method (object initialization)
        """
        super().__init__("aws_libcloud")

    def read_login_data(self):
        """
        Read login data from settings.cfg
        """
        self.ec2_access_key_id = self.get_parameter("aws", "ec2_access_key_id", return_type=str)
        self.ec2_secret_access_key = self.get_parameter("aws", "ec2_secret_access_key", return_type=str)
        self.ec2_session_token = self.get_parameter("aws", "ec2_session_token", return_type=str)
        self.ec2_default_region = self.get_parameter("aws", "ec2_default_region", return_type=str)
        logging.debug("AWS login data read")

    def read_platform_options(self):
        """
        Read platform-specific options from settings.cfg
        """
        # Free Tier settings
        self.freetier_only = self.get_parameter("freetier", "freetier_only", return_type=bool)
        self.freetier_instance_types = self.parser.get(
            "freetier", "freetier_instance_types").replace(" ", "").replace("\n", "").split(",")
        self.freetier_images_ids = self.parser.get(
            "freetier", "freetier_images_ids").replace(" ", "").replace("\n", "").split(",")
        # Filters (for images, Amazon has 30.000+ images available)
        self.images_filters = self.parser.get(
            "filters", "images_filters").replace(" ", "").replace("\n", "").split(",")
        logging.debug("AWS platform options read")
