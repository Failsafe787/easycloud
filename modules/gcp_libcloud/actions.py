"""
Google Cloud Platform Agent Actions Implementation
"""

__author__ = "Davide Monfrecola, Stefano Garione, Giorgio Gambino, Luca Banzato"
__copyright__ = "Copyright (C) 2019"
__credits__ = ["Andrea Lombardo", "Irene Lovotti"]
__license__ = "GPL v3"
__version__ = "0.10.0"
__maintainer__ = "Luca Banzato"
__email__ = "20005492@studenti.uniupo.it"
__status__ = "Prototype"

import logging
import time


class GCPAgentActions:

    def clone_instance(self, instance_id):
        """
        Clone an instance if it hasn't been already cloned

        Args:
            self (MetaManager): The platform manager object
            instance_id (str): The id of the instance to clone
        """
        if GCPAgentActions.is_clonable(self, instance_id):
            logging.debug("Cloning instance " + instance_id + "...")
            try:
                instance = self.gcp_client.ex_get_node(instance_id)
                # Clone only if the instance is running
                if instance.state == "running":
                    instance_clone = self.gcp_client.create_node(name=instance.name + "-clone-" + str(int(time.time())),
                                                                 size=instance.size,
                                                                 image=instance.image)
                    if instance_clone is None:
                        logging.error("An error has occurred while cloning the instance " + instance_id + "!")
                    else:
                        self.cloned_instances.append(instance_id)
                        logging.debug("Instance " + instance_id + " cloned successfully!")
                else:
                    logging.debug("The instance" + instance_id + " is not in a running state (currently: " + instance.state + "). Clonation aborted!")
            except Exception as e:
                logging.error("An error has occurred while cloning the instance " + instance_id + ": " + str(e))
        else:
            logging.error("The " + instance_id + " has already been cloned!")

    def is_clonable(self, instance_id):
        """
        Check if the VM corresponding to the provided instance_id
        has already been cloned

        Args:
            self (MetaManager): The platform manager object
            instance_id (str): An instance id

        Returns:
            bool: True if it has already been cloned, False otherwise
        """
        if instance_id in self.cloned_instances:
            return False
        else:
            return True

    def alarm(self, instance_id):
        """
        Trigger an alarm (reported in logs/cloudtui-fts.log)

        Args:
            self (MetaManager): The platform manager object
            instance_id (str): An instance id
        """
        logging.debug("Alarm triggered for instance " + instance_id)
