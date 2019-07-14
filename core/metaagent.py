"""
EasyCloud Metaagent component, used to execute all the commands
the RuleEngine module issues for a specific platform
"""

import logging

from core.actionbinder import get_actions

__author__ = "Davide Monfrecola, Stefano Garione, Giorgio Gambino, Luca Banzato"
__copyright__ = "Copyright (C) 2019"
__credits__ = ["Andrea Lombardo", "Irene Lovotti"]
__license__ = "GPL v3"
__version__ = "0.10.0"
__maintainer__ = "Luca Banzato"
__email__ = "20005492@studenti.uniupo.it"
__status__ = "Prototype"


class MetaAgent:

    def __init__(self, commands_queue, manager):
        """
        Init method (object initialization)

        Args:
            commands_queue (Queue): message queue used for receiving commands from
                                    the platform RuleEngine
            manager (str): The Manager class name
        """
        self.commands_queue = commands_queue
        self.manager = manager
        # Set MetaAgent Enabled
        self._stop = False

    def stop(self):
        """
        Stop the MetaAgent
        """
        self._stop = True

    def run(self):
        """
        Main agent loop
        """
        try:
            while not self._stop:
                command = self.commands_queue.get()
                logging.debug("Command received: " + str(command))
                self.execute_command(command)
        except Exception as e:
            logging.error("An exception has occourred: " + str(e))

    def execute_command(self, command):
        """
        Execute a command issued by the RuleEngine

        Args:
            command (str): The command name
        """
        try:
            all_actions = get_actions(self.manager.__class__.__name__)
            action_method = getattr(self.manager, all_actions[command["action"]])
        except AttributeError:
            logging.error("Error: the " + self.manager.platform_name + " module has no action called " + command["action"])
        except Exception as e:
            logging.error("An exception has occourred: " + str(e))
        logging.debug("Executing \"" + command["action"] + "\" for instance " + command["instance_id"])
        action_method(command["instance_id"])
