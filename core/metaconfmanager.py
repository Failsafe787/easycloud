"""
Common base class for all the configuration managers
"""

from abc import ABC, abstractmethod
from configparser import SafeConfigParser
from os import sep
from tui.simpletui import SimpleTUI

__author__ = "Davide Monfrecola, Stefano Garione, Giorgio Gambino, Luca Banzato"
__copyright__ = "Copyright (C) 2019"
__credits__ = ["Andrea Lombardo", "Irene Lovotti"]
__license__ = "GPL v3"
__version__ = "0.10.0"
__maintainer__ = "Luca Banzato"
__email__ = "20005492@studenti.uniupo.it"
__status__ = "Prototype"


class MetaConfManager(ABC):

    def __init__(self, platform):
        """
        Initializes parser object

        Args:
            platform (str): platform module directory name
        """
        self.platform = platform
        self.parser = SafeConfigParser()
        self.parser.read("modules" + sep + self.platform + sep + "settings.cfg")
        self.read_login_data()
        self.read_platform_options()
        self.read_options()

    @abstractmethod
    def read_login_data():
        pass

    @abstractmethod
    def read_platform_options():
        pass

    def read_options(self):
        """
        Reads options values from [options] section
        """
        self.monitor_fetch_period = self.get_parameter("options", "monitor_fetch_period", return_type=int)
        self.granularity = self.get_parameter("options", "granularity", return_type=int)
        self.window_size = self.get_parameter("options", "window_size", return_type=int)
        self.minimum_positive = self.get_parameter("options", "minimum_positive", return_type=int)

    def ask_for_data(self, section_name, param_name, return_type=None, regex=None):
        """
        Ask for user input if a parameter is not defined

        Args:
            param_name (str): the name of the missing parameter
            return_type (<return_type>, optional): the return type assigned to user input
            regex (str): the regular expression the input must follow

        Returns:
            <return_type>: user input of type <return_type>
        """
        return SimpleTUI.input_dialog("Missing value",
                                      question="A parameter required by this module has not been defined in settings.cfg!\n"
                                      "Please, define a value to assign to \"" + param_name + "\" (\"" + section_name + "\" section)",
                                      return_type=return_type,
                                      regex=regex,
                                      pause_on_exit=False,
                                      cannot_quit=True)

    def get_parameter(self, section, option, return_type=None, regex=None):
        """
        Return the parameter stored in the module configuration file or
        ask the user to provide it

        Args:
            section (str): name of the section (a name surrounded with square brackets
                           inside the configuration file)
            option (str): name of the parameter
            return_type (<return_type>, optional): the return type assigned to user input,
                                                   if not specified in the configuration
                                                   file
            regex (str): the regular expression the input must follow, if a user input is
                         required

        Returns:
            <return_type>: user input of type <return_type>
        """
        if self.parser.has_option(section, option):
            value = self.parser.get(section, option)
            if return_type == bool:
                if value in ["True", "true"]:
                    return True
            else:
                return return_type(value)
        else:
            return self.ask_for_data(section, option, regex=regex, return_type=return_type)
