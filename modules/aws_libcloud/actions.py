"""
Amazon Web Services Agent Actions Implementation
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


class AWSAgentActions:

    def clone_instance(self, instance_id):
        """
        Clone an instance if it hasn't been already cloned

        Args:
            self (MetaManager): The platform manager object
            instance_id (str): The id of the instance to clone
        """
        if AWSAgentActions.is_clonable(self, instance_id):
            logging.debug("Cloning instance " + instance_id + "...")
            try:
                instance = self.ec2_client.list_nodes(ex_node_ids=[instance_id])[0]
                # Clone only if the instance is running
                if instance.state == "running":
                    instance_clone = self.ec2_client.create_node(name=instance.name + "-clone-" + str(int(time.time())),
                                                                 image=self.ec2_client.get_image(instance.extra["image_id"]),
                                                                 size=self._get_instance_type_from_instance(instance),
                                                                 ex_keyname=instance.extra["key_name"],
                                                                 ex_security_groups=self._get_security_groups_from_instance(instance),
                                                                 ex_mincount=1,
                                                                 ex_maxcount=1)
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
            logging.debug("The " + instance_id + " has already been cloned!")

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
