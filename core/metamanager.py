"""
EasyCloud Generic Manager
"""

import json
import logging
import os
import subprocess

from abc import ABC, abstractmethod
from core.metaagent import MetaAgent
from core.ruleengine import RuleEngine
from queue import Queue
from threading import Thread
from tui.simpletui import SimpleTUI

__author__ = "Davide Monfrecola, Stefano Garione, Giorgio Gambino, Luca Banzato"
__copyright__ = "Copyright (C) 2019"
__credits__ = ["Andrea Lombardo", "Irene Lovotti"]
__license__ = "GPL v3"
__version__ = "0.10.0"
__maintainer__ = "Luca Banzato"
__email__ = "20005492@studenti.uniupo.it"
__status__ = "Prototype"


class MetaManager(ABC):

    def __init__(self):
        self.images = None
        self.instances = None
        self.instance_types = None
        self.security_groups = None
        self.key_pairs = None
        self.floating_ips = None
        self.networks = None
        self.volumes = None
        self.avail_zones = None
        self.monitor = None
        self.rule_engine = None
        self.agent = None
        self.monitoring = False
        self.rules = []
        self.active_rules = []
        self.monitor_cmd_queue = None
        self._read_rules_from_file()

    def menu(self):
        """
        Prints the Manager menu
        Menu ID (for override): "main"
        """
        SimpleTUI.set_console_title(self.platform_name + " (" + self._platform_get_region() + ") - EasyCloud")
        menu_header = self.platform_name + " EasyCloud Manager"
        menu_subheader = ["Region: \033[1;94m" + self._platform_get_region() + "\033[0m"]
        menu_items = ["Create new instance",
                      "Show running instances",
                      "Terminate instance",
                      "Reboot instance",
                      "Manage floating IPs",
                      "Manage volumes",
                      "Extra functions",
                      "Stop monitor" if self.monitoring else "Start monitor",
                      "Manage rules",
                      "Edit configuration file",
                      "Change platform",
                      "Close application"]
        choice = SimpleTUI.print_menu(menu_header, menu_items, menu_subheader)
        try:
            if (not self._platform_is_overridden("main", choice)):
                if choice == 1:  # Create new instance
                    self.create_new_instance()
                    return 0
                elif choice == 2:  # Show running instances
                    SimpleTUI.list_dialog("Instances available",
                                          list_printer=self.print_all_instances)
                    return 0
                elif choice == 3:  # Terminate instance
                    self.instance_action("delete")
                    return 0
                elif choice == 4:  # Reboot instance
                    self.instance_action("reboot")
                    return 0
                elif choice == 5:  # Manage floating IPs
                    self.manage_floating_ips()
                    return 0
                elif choice == 6:  # Manage Volumes
                    self.manage_volumes()
                    return 0
                elif choice == 7:  # Extra Functions
                    self._platform_extra_menu()
                    return 0
                elif choice == 8:  # Start/Stop monitor
                    self.start_stop_monitor()
                    return 0
                elif choice == 9:  # Manage rules
                    self.manage_rules()
                    return 0
                elif choice == 10:  # Edit configuration file
                    result = self.edit_configuration()
                    return result
                elif choice == 11:  # Change platform
                    return 1
                elif choice == 12:  # Close application
                    return 2
                else:
                    SimpleTUI.msg_dialog("Error", "Unimplemented functionality", SimpleTUI.DIALOG_ERROR)
                    return 0
            else:
                return self._platform_override_menu("main", choice)
        except Exception as e:
            SimpleTUI.exception_dialog(e)

    @abstractmethod
    def _platform_is_overridden(self, menu, index):
        pass

    @abstractmethod
    def _platform_override_menu(self, menu, index):
        pass

    @abstractmethod
    def _platform_extra_menu(self):
        """
        Prints the extra Functions Menu (specific for each platform)
        """
        pass

    @abstractmethod
    def connect(self):
        """
        Connection to the endpoint specified in the configuration file
        """
        pass

    # =============================================================================================== #
    #                                           List printers                                         #
    # =============================================================================================== #

    def print_all_images(self):
        """
        Print all available images
        """
        table_header = ["ID", "Name", "Image ID", "Status"]
        table_body = self._platform_list_all_images()
        SimpleTUI.print_table(table_header, table_body)
        if len(self.images) == 0:
            SimpleTUI.info("There are no images available")
        return len(self.images)

    @abstractmethod
    def _platform_list_all_images(self):
        pass

    def print_all_availability_zones(self):
        """
        Print availability zones (Unused until now)
        """
        table_header = ["ID", "Name", "Zone State", "Region Name"]
        table_body = self._platform_list_all_availability_zones()
        SimpleTUI.print_table(table_header, table_body)
        if len(self.avail_zones) == 0:
            SimpleTUI.info("There are no availability zones available")
        return len(self.avail_zones)

    @abstractmethod
    def _platform_list_all_availability_zones():
        pass

    def print_all_instance_types(self):
        """
        Print all instance types
        """
        table_header = ["ID", "Instance Type ID", "vCPUs", "Ram (GB)", "Disk (GB)"]
        table_body = self._platform_list_all_instance_types()
        SimpleTUI.print_table(table_header, table_body)
        if len(self.instance_types) == 0:
            SimpleTUI.info("There are no instance types available")
        return len(self.instance_types)

    @abstractmethod
    def _platform_list_all_instance_types(self):
        pass

    def print_all_security_groups(self):
        """
        Print all security groups
        """
        table_header = ["ID", "SG name", "SG description"]
        table_body = self._platform_list_all_security_groups()
        SimpleTUI.print_table(table_header, table_body)
        if len(self.security_groups) == 0:
            SimpleTUI.info("There are no security groups available")
        return len(self.security_groups)

    @abstractmethod
    def _platform_list_all_security_groups(self):
        pass

    def print_all_networks(self):
        """
        Print id and other useful informations of all networks available
        """
        table_header = ["ID", "Network name", "Network ID"]
        table_body = self._platform_list_all_networks()
        SimpleTUI.print_table(table_header, table_body)
        if len(self.networks) == 0:
            SimpleTUI.info("There are no networks available")
        return len(self.networks)

    @abstractmethod
    def _platform_list_all_networks(self):
        pass

    def print_all_key_pairs(self):
        """
        Print all key pairs
        """
        table_header = ["ID", "Key name", "Key fingerprint"]
        table_body = self._platform_list_all_key_pairs()
        SimpleTUI.print_table(table_header, table_body)
        if len(self.key_pairs) == 0:
            SimpleTUI.info("There are no key pairs available")
        return len(self.key_pairs)

    @abstractmethod
    def _platform_list_all_key_pairs(self):
        pass

    def print_all_instances(self):
        """
        Print instance id, image id, IP address and state for each active instance
        """
        table_header = ["ID", "Instance Name", "Instance ID",
                        "IP address", "Status", "Key Name", "Avail. Zone"]
        table_body = self._platform_list_all_instances()
        SimpleTUI.print_table(table_header, table_body)
        if len(self.instances) == 0:
            SimpleTUI.info("There are no running or pending instances")
        return len(self.instances)

    @abstractmethod
    def _platform_list_all_instances(self):
        pass

    def print_all_volumes(self):
        """
        Print volumes and some informations
        """
        table_header = ["ID", "Volume Name", "Volume ID",
                        "Creation", "Size (GB)", "Attached To", "Status", "Avail. Zone"]
        table_body = self._platform_list_all_volumes()
        SimpleTUI.print_table(table_header, table_body)
        if len(self.volumes) == 0:
            SimpleTUI.info("There are no volumes available")
        return len(self.volumes)

    @abstractmethod
    def _platform_list_all_volumes(self):
        pass

    def print_all_floating_ips(self):
        """
        Print ip and other useful information of all floating ip available
        """
        table_header = ["ID", "Public Ip",
                        "Floating IP ID", "Associated Instance", "Region"]
        table_body = self._platform_list_all_floating_ips()
        SimpleTUI.print_table(table_header, table_body)
        if len(self.floating_ips) == 0:
            SimpleTUI.info("There are no floating IPs available")
        return len(self.floating_ips)

    @abstractmethod
    def _platform_list_all_floating_ips(self):
        pass

    def print_all_rules(self):
        """
        Print all the available rules

        Returns:
            int: The number of rules printed
        """
        table_header = ["ID", "Name", "Metric", "Threshold", "Operator", "Action", "Status"]
        table_body = self._list_all_rules()
        SimpleTUI.print_table(table_header, table_body)
        if len(self.rules) == 0:
            SimpleTUI.info("There are no rules available")
        return len(self.rules)

    def print_all_active_rules(self):
        """
        Print all the active rules

        Returns:
            int: The number of active rules printed
        """
        table_header = ["ID", "Name", "Metric", "Threshold", "Operator", "Action"]
        table_body = self._list_all_active_rules()
        SimpleTUI.print_table(table_header, table_body)
        if len(self.active_rules) == 0:
            SimpleTUI.info("There are no rules available")
        return len(self.active_rules)

    # =============================================================================================== #
    #                                         List builders                                           #
    # =============================================================================================== #

    def _list_all_rules(self):
        """
        List all the rules
        Format: "ID", "Name", "Metric", "Threshold", "Operator", "Action"

        Returns:
            str[]: List of strings (table body)
        """
        i = 1
        table_body = []
        for rule in self.rules:
            status = None
            if rule["name"] in self.active_rules:
                status = "Enabled"
            else:
                status = "Disabled"
            table_body.append([i, rule["name"], rule["target"], rule["threshold"], rule["operator"], rule["action"], str(status)])
            i = i + 1
        return table_body

    def _list_all_active_rules(self):
        """
        List all the active rules
        Format: "ID", "Name", "Metric", "Threshold", "Operator", "Action"

        Returns:
            str[]: List of strings (table body)
        """
        i = 1
        table_body = []
        for active_rule_name in self.active_rules:
            for rule in self.rules:
                if active_rule_name == rule["name"]:
                    table_body.append([i, rule["name"], rule["target"], rule["threshold"], rule["operator"], rule["action"]])
                    break
            i = i + 1
        return table_body

    # =============================================================================================== #
    #                                       Actions and Menus                                         #
    # =============================================================================================== #

    def create_new_instance(self):
        """
        Start the Create Instance Wizard
        """
        # 1. Instance name
        instance_name = SimpleTUI.input_dialog("Instance name",
                                               question="Insert instance name",
                                               return_type=str,
                                               regex="^[a-zA-Z0-9_-]+$")
        if instance_name is None:
            return
        # 2. Image
        image_index = SimpleTUI.list_dialog("Images available",
                                            self.print_all_images,
                                            question="Select image")
        if image_index is None:
            return
        image = self.images[image_index - 1]
        # 3. Instance Type
        instance_type_index = SimpleTUI.list_dialog("Instance types available",
                                                    self.print_all_instance_types,
                                                    question="Select instance type")
        if instance_type_index is None:
            return
        instance_type = self.instance_types[instance_type_index - 1]
        # 4. Optional steps (depending on the manager) and creation
        try:
            if self._platform_create_new_instance(instance_name, image, instance_type, monitor_cmd_queue=self.monitor_cmd_queue):
                SimpleTUI.msg_dialog("Instance creation", "Instance created!", SimpleTUI.DIALOG_SUCCESS)
            else:
                SimpleTUI.msg_dialog("Instance creation", "There was an error while creating this instance!\n",
                                     SimpleTUI.DIALOG_ERROR)
        except Exception as e:
            SimpleTUI.exception_dialog(e)

    @abstractmethod
    def _platform_create_new_instance(self, instance_name, image, instance_type, commands_queue):
        pass

    def instance_action(self, action):
        """
        Handle instance commands (currently delete and reboot)
        """
        instance_index = SimpleTUI.list_dialog("Instances available",
                                               self.print_all_instances,
                                               question="Please select an instance")
        if instance_index is None:
            return
        instance = self.instances[instance_index - 1]
        # Reboot instance
        if action == "reboot":
            try:
                if self._platform_instance_action(instance, action):
                    SimpleTUI.msg_dialog("Instance reboot", "Instance rebooted!", SimpleTUI.DIALOG_SUCCESS)
                else:
                    SimpleTUI.msg_dialog("Instance reboot", "There was an error while rebooting this instance!",
                                         SimpleTUI.DIALOG_ERROR)
            except Exception as e:
                SimpleTUI.exception_dialog(e)

        # Delete instance
        elif action == "delete":
            try:
                if self._platform_instance_action(instance, action):
                    if self.monitor_cmd_queue is not None and self.is_monitor_running():  # Remove the instance from the monitor
                        self.monitor_cmd_queue.put({"command": "remove", "instance_id": instance.id})
                    SimpleTUI.msg_dialog("Instance termination", "Instance terminated!", SimpleTUI.DIALOG_SUCCESS)
                else:
                    SimpleTUI.msg_dialog("Instance termination", "There was an error while terminating this instance!",
                                         SimpleTUI.DIALOG_ERROR)
            except Exception as e:
                SimpleTUI.exception_dialog(e)
            # if instance_id in self.cloned_instances:
            #    del self.cloned_instances[instance_id]
        # Invalid instance action
        else:
            raise Exception("Unsupported action \"" + action + "\"")

    @abstractmethod
    def _platform_instance_action(self, instance, action):
        pass

    def get_instance_info(self):
        """
        Return a list of instances info
        """
        return self._platform_get_instance_info()

    @abstractmethod
    def _platform_get_instance_info(self):
        pass

    def manage_volumes(self):
        """
        Display a menu with all the actions available regarding volumes
        Menu ID (for override): "volumes"
        """
        while(True):
            menu_header = self.platform_name + " Volumes Manager"
            menu_subheader = ["Region: \033[1;94m" +
                              self._platform_get_region() + "\033[0m"]
            menu_items = ["List all the volumes",
                          "Create a new volume",
                          "Delete an existing volume",
                          "Attach a volume to an instance",
                          "Detach a volume from an instance",
                          "Back to the Main Menu"]
            choice = SimpleTUI.print_menu(menu_header, menu_items, menu_subheader)
            if (not self._platform_is_overridden("volumes", choice)):
                if choice == 1:  # Print all the volumes
                    SimpleTUI.list_dialog("Volumes available",
                                          self.print_all_volumes)
                elif choice == 2:  # Create volume
                    self.create_volume()
                elif choice == 3:  # Delete volume
                    self.delete_volume()
                elif choice == 4:  # Attach volume
                    self.attach_volume()
                elif choice == 5:  # Detach volume
                    self.detach_volume()
                elif choice == 6:  # Back to the main menu
                    break
                else:
                    SimpleTUI.msg_dialog("Error", "Unimplemented functionality", SimpleTUI.DIALOG_ERROR)
            else:
                self._platform_override_menu("volumes", choice)

    def detach_volume(self):
        """
        Start the Detach Volume Wizard
        """
        volume = None
        while(True):
            volume_index = SimpleTUI.list_dialog("Volumes available",
                                                 self.print_all_volumes,
                                                 question="Select the volume to release")
            if volume_index is None:
                return
            volume = self.volumes[volume_index - 1]
            if not self._platform_is_volume_attached(volume):
                SimpleTUI.msg_dialog("Detaching status", "This volume is already detached!",
                                     SimpleTUI.DIALOG_ERROR)
            else:
                break
        # Detach the volume
        SimpleTUI.msg_dialog("Detaching volume", "Detaching the volume, this can take a bit...",
                             SimpleTUI.DIALOG_INFO, pause_on_exit=False, clear_on_exit=False)
        # Check if this volume is detached
        try:
            if self._platform_detach_volume(volume):
                SimpleTUI.msg_dialog("Detaching status", "Volume detached!",
                                     SimpleTUI.DIALOG_SUCCESS)
            else:
                SimpleTUI.msg_dialog("Detaching status", "There was an error while detaching this volume!",
                                     SimpleTUI.DIALOG_ERROR)
        except Exception as e:
            SimpleTUI.exception_dialog(e)

    @abstractmethod
    def _platform_is_volume_attached(self, volume):
        pass

    @abstractmethod
    def _platform_detach_volume(self):
        pass

    def delete_volume(self):
        """
        Start the Delete Volume Wizard
        """
        volume_index = SimpleTUI.list_dialog("Volumes available",
                                             self.print_all_volumes,
                                             question="Select the volume to delete")
        if volume_index is None:
            return
        volume = self.volumes[volume_index - 1]
        try:
            if self._platform_is_volume_attached(volume):
                choice = SimpleTUI.yn_dialog("Detaching status",
                                             "Warning: this volume is associated to an instance. Do you really want to continue?",
                                             warning=True)
                if not choice:
                    return
                else:
                    SimpleTUI.msg_dialog("Detaching volume", "Detaching the volume, this can take a bit...",
                                         SimpleTUI.DIALOG_INFO, pause_on_exit=False, clear_on_exit=False)
                    if not self._platform_detach_volume(volume):
                        SimpleTUI.msg_dialog("Detaching status", "There was an error while detaching this volume!",
                                             SimpleTUI.DIALOG_ERROR)
                        return
            if self._platform_delete_volume(volume):
                SimpleTUI.msg_dialog("Volume deletion", "Volume deleted!",
                                     SimpleTUI.DIALOG_SUCCESS)
            else:
                SimpleTUI.msg_dialog("Volume deletion", "There was an error while deleting this volume!",
                                     SimpleTUI.DIALOG_ERROR)
        except Exception as e:
            SimpleTUI.exception_dialog(e)

    @abstractmethod
    def _platform_delete_volume(self):
        pass

    def attach_volume(self):
        """
        Start the Attach Volume Wizard
        """
        # Select a volume
        volume = None
        while(True):
            volume_index = SimpleTUI.list_dialog("Volumes available",
                                                 self.print_all_volumes,
                                                 question="Select the volume to attach")
            if volume_index is None:
                return
            volume = self.volumes[volume_index - 1]
            if self._platform_is_volume_attached(volume):
                SimpleTUI.msg_dialog("Attaching status", "This volume is already attached to another instance!",
                                     SimpleTUI.DIALOG_ERROR)
            else:
                break
        # Select an instance
        instance_index = SimpleTUI.list_dialog("Instances available",
                                               self.print_all_instances,
                                               question="Please select an instance")
        if instance_index is None:
            return
        instance = self.instances[instance_index - 1]
        # Attach the volume
        try:
            if self._platform_attach_volume(volume, instance):
                SimpleTUI.msg_dialog("Attaching status", "Volume attached!",
                                     SimpleTUI.DIALOG_SUCCESS)
            else:
                SimpleTUI.msg_dialog("Attaching status", "There was an error while attaching this volume to this instance!",
                                     SimpleTUI.DIALOG_ERROR)
        except Exception as e:
            SimpleTUI.exception_dialog(e)

    @abstractmethod
    def _platform_attach_volume(self, volume, instance):
        pass

    def create_volume(self):
        """
        Start the Create Volume Wizard
        """
        # Ask for a volume name
        volume_name = SimpleTUI.input_dialog("Volume name",
                                             question="Insert volume name",
                                             return_type=str,
                                             regex="^[a-zA-Z0-9_-]+$")
        if volume_name is None:
            return
        # Ask for volume size
        volume_size = SimpleTUI.input_dialog("Volume size",
                                             question="Insert volume size (in GB)",
                                             return_type=int)
        if volume_size is None:
            return
        try:
            # Create volume (some additional steps may be required)
            if self._platform_create_volume(volume_name, volume_size):
                SimpleTUI.msg_dialog("Creation status", "Volume created!",
                                     SimpleTUI.DIALOG_SUCCESS)
            else:
                SimpleTUI.msg_dialog("Creation status", "There was an error while creating this volume!",
                                     SimpleTUI.DIALOG_ERROR)
        except Exception as e:
            SimpleTUI.exception_dialog(e)

    @abstractmethod
    def _platform_create_volume(self, volume_name, volume_size):
        pass

    def manage_floating_ips(self):
        """
        Display a menu with all the actions available regarding IP addresses
        Menu ID (for override): "floating_ips"
        """
        while(True):
            menu_header = self.platform_name + " Floating IPs Manager"
            menu_subheader = ["Region: \033[1;94m" +
                              self._platform_get_region() + "\033[0m"]
            menu_items = ["List all the available floating IPs",
                          "Reserve a new Floating IP",
                          "Release a reserved Floating IP",
                          "Asssociate an IP to an instance",
                          "Detach a floating IP from an instance",
                          "Back to the Main Menu"]
            choice = SimpleTUI.print_menu(menu_header, menu_items, menu_subheader)
            if (not self._platform_is_overridden("floating_ips", choice)):
                if choice == 1:  # Print all the floating IPS
                    SimpleTUI.list_dialog("Floating IPs available",
                                          self.print_all_floating_ips)
                elif choice == 2:  # Reserve a floating IP
                    self.reserve_floating_ip()
                elif choice == 3:  # Release a floating IP
                    self.release_floating_ip()
                elif choice == 4:  # Assign IP to an instance
                    self.associate_floating_ip()
                elif choice == 5:  # Detach a floating IP from an instance
                    self.detach_floating_ip()
                elif choice == 6:  # Back to the main menu
                    break
                else:
                    SimpleTUI.msg_dialog("Error", "Unimplemented functionality", SimpleTUI.DIALOG_ERROR)
            else:
                self._platform_override_menu("floating_ips", choice)

    def detach_floating_ip(self):
        """
        Start the Detach Floating IP Wizard
        """
        # Select a floating IP
        floating_ip = None
        while(True):
            floating_ip_index = SimpleTUI.list_dialog("Floating IPs available",
                                                      self.print_all_floating_ips,
                                                      question="Select the floating IP to detach")
            if floating_ip_index is None:
                return
            floating_ip = self.floating_ips[floating_ip_index - 1]
            if not self._platform_is_ip_assigned(floating_ip):
                SimpleTUI.msg_dialog("Detaching status", "This floating IP is already detached!",
                                     SimpleTUI.DIALOG_ERROR)
            else:
                break
        try:
            # Detach this floating IP and poll to check if it is detached
            SimpleTUI.msg_dialog("Detaching status", "Detaching the floating IP, this can take a bit...",
                                 SimpleTUI.DIALOG_INFO, pause_on_exit=False, clear_on_exit=False)
            if self._platform_detach_floating_ip(floating_ip):
                SimpleTUI.msg_dialog("Detaching status", "Floating IP detached!",
                                     SimpleTUI.DIALOG_SUCCESS)
            else:
                SimpleTUI.msg_dialog("Detaching status", "There was an error while detaching this floating IP!",
                                     SimpleTUI.DIALOG_ERROR)
        except Exception as e:
            SimpleTUI.exception_dialog(e)

    @abstractmethod
    def _platform_is_ip_assigned(self, floating_ip):
        pass

    @abstractmethod
    def _platform_detach_floating_ip(self, floating_ip):
        pass

    def release_floating_ip(self):
        """
        Start the Release Floating IP Wizard
        """
        # Select a floating IP
        floating_ip_index = SimpleTUI.list_dialog("Floating IPs available",
                                                  self.print_all_floating_ips,
                                                  question="Select the floating IP to release")
        if floating_ip_index is None:
            return
        floating_ip = self.floating_ips[floating_ip_index - 1]
        # Check if the user want to detach this ip (if attached)
        try:
            if self._platform_is_ip_assigned(floating_ip):
                choice = SimpleTUI.yn_dialog("Detaching status",
                                             "Warning: this IP is associated to an instance. Do you really want to continue?", warning=True)
                if not choice:
                    return
                else:
                    SimpleTUI.msg_dialog("Detaching status", "Detaching the floating IP, this can take a bit...",
                                         SimpleTUI.DIALOG_INFO, pause_on_exit=False, clear_on_exit=False)
                    if not self._platform_detach_floating_ip(floating_ip):
                        SimpleTUI.msg_dialog("Detaching status", "There was an error while detaching this floating IP!",
                                             SimpleTUI.DIALOG_ERROR)
                        return
            # Release IP
            if self._platform_release_floating_ip(floating_ip):
                SimpleTUI.msg_dialog("Releasing status", "Floating IP released!",
                                     SimpleTUI.DIALOG_SUCCESS)
            else:
                SimpleTUI.msg_dialog("Releasing status", "There was an error while releasing this floating IP!",
                                     SimpleTUI.DIALOG_ERROR)
        except Exception as e:
            SimpleTUI.exception_dialog(e)

    @abstractmethod
    def _platform_release_floating_ip(self):
        pass

    def associate_floating_ip(self):
        """
        Start the Associate Floating IP Wizard
        """
        # Select a floating IP
        floating_ip = None
        while(True):
            floating_ip_index = SimpleTUI.list_dialog("Floating IPs available",
                                                      self.print_all_floating_ips,
                                                      question="Select the floating IP to attach")
            if floating_ip_index is None:
                return
            floating_ip = self.floating_ips[floating_ip_index - 1]
            if self._platform_is_ip_assigned(floating_ip):
                SimpleTUI.msg_dialog("Detaching status", "This floating IP is already attached to another instance!",
                                     SimpleTUI.DIALOG_ERROR)
            else:
                break
        # Select an instance
        instance_index = SimpleTUI.list_dialog("Instances available",
                                               self.print_all_instances,
                                               question="Please select an instance")
        if instance_index is None:
            return
        instance = self.instances[instance_index - 1]
        # Associate floating IP
        try:
            if self._platform_associate_floating_ip(floating_ip, instance):
                SimpleTUI.msg_dialog("Association status", "Floating IP associated!",
                                     SimpleTUI.DIALOG_SUCCESS)
            else:
                SimpleTUI.msg_dialog("Association status", "There was an error while associating the floating IP to this instance!",
                                     SimpleTUI.DIALOG_ERROR)
        except Exception as e:
            SimpleTUI.exception_dialog(e)

    @abstractmethod
    def _platform_associate_floating_ip(self, floating_ip, instance):
        pass

    def reserve_floating_ip(self):
        """
        Start the Reserve Floating IP Wizard
        """
        try:
            if self._platform_reserve_floating_ip():
                SimpleTUI.msg_dialog("Reservation status", "Floating IP reserved!",
                                     SimpleTUI.DIALOG_SUCCESS)
            else:
                SimpleTUI.msg_dialog("Association status", "There was an error while reserving a floating IP!",
                                     SimpleTUI.DIALOG_ERROR)
        except Exception as e:
            SimpleTUI.exception_dialog(e)

    @abstractmethod
    def _platform_reserve_floating_ip(self):
        pass

    def edit_configuration(self):
        """
        Edit configuration file
        """
        choice = SimpleTUI.yn_dialog("Edit configuration file", "WARNING: this program will be closed in order to refresh all the settings.\n" +
                                     "All the other platform managers and running monitors will also be closed.\n" +
                                     "Do you really want to continue?", warning=True)
        if choice:
            if os.name == "nt":  # Edit using Notepad (Windows)
                subprocess.run(["notepad.exe", "modules" + os.sep + self.conf.platform + os.sep + "settings.cfg"])
            else:  # Edit using Nano (MacOS and GNU/Linux)
                subprocess.run(
                    ["nano", "modules" + os.sep + self.conf.platform + os.sep + "settings.cfg"])
            return 2  # Tell the main program to quit
        return 0  # Abort

    # =============================================================================================== #
    #                                           RuleEngine                                            #
    # =============================================================================================== #

    def start_stop_monitor(self):
        """
        Start or stop the monitor (intended as Platform Monitor + RuleEngine+ Agent) depending on
        its status
        """
        if self.is_monitor_running():
            SimpleTUI.msg_dialog("Monitor status", "Stopping the monitor, this can take a bit...",
                                 SimpleTUI.DIALOG_INFO, pause_on_exit=False, clear_on_exit=False)
            self.stop_monitor()
            self.monitor = None
            self.rule_engine = None
            self.agent = None
            self.monitoring = False
            SimpleTUI.msg_dialog("Monitor status",
                                 "The " + self.platform_name + " monitor has been successfully terminated!",
                                 SimpleTUI.DIALOG_SUCCESS)
        else:
            logging.debug("Monitor not enabled, starting threads")
            SimpleTUI.msg_dialog("Monitor status", "Starting the monitor, this can take a bit...",
                                 SimpleTUI.DIALOG_INFO, pause_on_exit=False, clear_on_exit=False)
            self.start_monitor()
            SimpleTUI.msg_dialog("Monitor status",
                                 "The " + self.platform_name + " monitor has been successfully started!",
                                 SimpleTUI.DIALOG_SUCCESS)
            self.monitoring = True

    def start_monitor(self):
        """
        Start Monitor, RuleEngine and Agent threads
        """
        # Queue creation
        # Queue used for receiving metrics from the Monitor
        monitor_measurements_queue = Queue()
        # Queue used for sending metrics to the Monitor (add/remove metric measurements to fetch)
        self.monitor_cmd_queue = Queue()
        # Queue used for sending commands
        self.re_cmd_queue = Queue()
        # Queue used in RuleEngine for sending commands to the Agent
        agent_cmd_queue = Queue()
        # Monitor object and thread creation
        logging.debug("MANAGER: " + str(self.re_cmd_queue))
        self.monitor = self._platform_get_monitor(commands_queue=self.monitor_cmd_queue,
                                                  measurements_queue=monitor_measurements_queue)
        self.monitor_thread = Thread(target=self.monitor.run)
        self.monitor_thread.setDaemon(True)
        # RuleEngine object and thread creation
        self.rule_engine = RuleEngine(conf=self.conf,
                                      commands_queue=self.re_cmd_queue,
                                      measurements_queue=monitor_measurements_queue,
                                      agent_queue=agent_cmd_queue)
        self.rule_engine_thread = Thread(target=self.rule_engine.run)
        self.rule_engine_thread.setDaemon(True)
        # Agent object and thread creation
        self.agent = MetaAgent(commands_queue=agent_cmd_queue, manager=self)
        self.agent_thread = Thread(target=self.agent.run)
        self.agent_thread.setDaemon(True)
        # Threads execution
        self.monitor_thread.start()
        logging.debug(self.platform_name + " Monitor Thread Started")
        self.rule_engine_thread.start()
        logging.debug(self.platform_name + "Rule Engine Thread Started")
        self.agent_thread.start()
        logging.debug(self.platform_name + " Agent Thread Started")
        # Send the init message to the RuleEngine
        self.rule_engine.commands_queue.put({"command": "init", "rules": self.rules})
        logging.debug("MANAGER QUEUE SIZE RE: " + str(self.rule_engine.commands_queue.qsize()))
        logging.debug("QUEUE SIZE: " + str(self.re_cmd_queue.qsize()))

    @abstractmethod
    def _platform_get_monitor(self, commands_queue, measurements_queue):
        pass

    def stop_monitor(self):
        """
        Stop Monitor, RuleEngine and Agent threads
        """
        # Ask the objects the threads are executing to stop
        if self.monitor is not None and self.monitor_thread.is_alive():  # Check if monitor is running
            self.monitor.stop()
        if self.rule_engine is not None and self.rule_engine_thread.is_alive():
            self.rule_engine.stop()
        if self.agent is not None and self.agent_thread.is_alive():
            self.agent.stop()
        # Wait for threads closure
        self.monitor_thread.join(5)
        self.rule_engine_thread.join(5)
        self.agent_thread.join(5)

    def is_monitor_running(self):
        """
        Detect if any  of the monitor (intended as Platform Monitor + RuleEngine + Agent) is running

        Returns:
            bool: True if one or more threads are running, False otherwise
        """
        if self.monitor is not None and self.monitor_thread.is_alive():
            return True
        if self.rule_engine is not None and self.rule_engine_thread.is_alive():
            return True
        if self.agent is not None and self.agent_thread.is_alive():
            return True
        return False

    # =============================================================================================== #
    #                                           RuleManager                                           #
    # =============================================================================================== #

    def manage_rules(self):
        """
        MetaManager menu
        """
        while(True):
            menu_header = self.platform_name + " Rule Manager"
            menu_subheader = ["Region: \033[1;94m" + self._platform_get_region() + "\033[0m"]
            menu_items = ["List all the available rules",
                          "Enable a rule",
                          "Disable a rule",
                          "Create a new rule",
                          "Edit a rule",
                          "Delete a rule",
                          "Back to the Main Menu"]
            choice = SimpleTUI.print_menu(menu_header, menu_items, menu_subheader)
            if choice == 1:
                SimpleTUI.list_dialog("Rules available",
                                      self.print_all_rules)
            elif choice == 2:
                self.enable_rule()
            elif choice == 3:
                self.disable_rule()
            elif choice == 4:
                self.create_rule()
            elif choice == 5:
                self.edit_rule()
            elif choice == 6:
                self.delete_rule()
            elif choice == 7:
                break
            else:
                SimpleTUI.msg_dialog("Error", "Unimplemented functionality", SimpleTUI.DIALOG_ERROR)

    # =============================================================================================== #
    #                                       RuleManager - Actions                                     #
    # =============================================================================================== #

    def enable_rule(self):
        """
        Enable a RuleEngine rule
        """
        # Check if the monitor is available looking at the commands_queue status
        if not self.is_monitor_running():
            SimpleTUI.msg_dialog("No Monitor Running", "Cannot perform this operation while the monitor is stopped",
                                 SimpleTUI.DIALOG_ERROR)
            return
        # Select a rule
        rule = None
        while True:
            rule_index = SimpleTUI.list_dialog("Rules available",
                                               self.print_all_rules,
                                               question="Select the rule to enable")
            if rule_index is None:
                return
            rule = self.rules[rule_index - 1]
            if rule["name"] in self.active_rules:
                SimpleTUI.msg_dialog("Rule status", "This rule is already enabled!",
                                     SimpleTUI.DIALOG_ERROR)
            else:
                break
        self.active_rules.append(rule["name"])
        self.re_cmd_queue.put({"command": "enable_rule", "rule_name": rule["name"]})
        SimpleTUI.msg_dialog("Rule status",
                             "This rule has been enabled!\nAll the changes will be applied starting from the next RuleEngine activity.",
                             SimpleTUI.DIALOG_SUCCESS)

    def disable_rule(self):
        """
        Disable a RuleEngine rule
        """
        # Check if the monitor is available looking at the commands_queue status
        if not self.is_monitor_running():
            SimpleTUI.msg_dialog("No Monitor Running", "Cannot perform this operation while the monitor is stopped",
                                 SimpleTUI.DIALOG_ERROR)
            return
        rule_index = SimpleTUI.list_dialog("Rules available",
                                           self.print_all_active_rules,
                                           question="Select the rule to disable")
        if rule_index is None:
            return
        rule_name = self.active_rules[rule_index - 1]
        self.active_rules.remove(rule_name)
        self.re_cmd_queue.put({"command": "disable_rule", "rule_name": rule_name})
        SimpleTUI.msg_dialog("Rule status",
                             "This rule has been disabled!\nAll the changes will be applied starting from the next RuleEngine activity.",
                             SimpleTUI.DIALOG_SUCCESS)

    def create_rule(self):
        """
        Wizard for creating a new rule
        """
        # Base struct
        _rule_params = {}
        # Rule name
        _name = SimpleTUI.input_dialog("Rule name",
                                       question="Insert rule name",
                                       return_type=str,
                                       regex="^[a-zA-Z0-9_-]+$")
        if _name is None:
            return
        _rule_params["name"] = _name
        # Generic metric name (also referenced as "target")
        _target = SimpleTUI.input_dialog("Generic metric name",
                                         question="Insert a generic metric name (please consult rules" + os.sep + "metrics.dct for a list of the ones available)",
                                         return_type=str,
                                         regex="^[a-zA-Z0-9_-]+$")
        if _target is None:
            return
        _rule_params["target"] = _target
        # Operator
        _operator = SimpleTUI.input_dialog("Rule operator",
                                           question="Insert a rule operator (between \"<\", \"<=\", \"==\", \"!=\", \">=\", \">\")",
                                           return_type=str,
                                           regex="^(<|<=|==|!=|>=|>)$")
        if _operator is None:
            return
        _rule_params["operator"] = _operator
        # Threshold
        _threshold = SimpleTUI.input_dialog("Rule threshold",
                                            question="Insert a rule threshold",
                                            return_type=float)
        if _threshold is None:
            return
        _rule_params["threshold"] = _threshold
        # Action
        _action = SimpleTUI.input_dialog("Rule action",
                                         question="Insert a rule action (must be defined in the platform manager)",
                                         return_type=str,
                                         regex="^[a-zA-Z0-9_-]+$")
        if _action is None:
            return
        _rule_params["action"] = _action
        # Create rule, update rules file and issue a refresh command to the RuleEngine
        self.rules.append(_rule_params)
        self._write_rules_to_file()
        # Send a message to the RuleEngine if it's running
        if self.is_monitor_running():
            self.re_cmd_queue.put({"command": "add_rule", "rule": _rule_params})

    def edit_rule(self):
        """
        Wizard for editing an existing rule
        """
        _rule_params = None
        while True:
            rule_index = SimpleTUI.list_dialog("Rules available",
                                               self.print_all_rules,
                                               question="Select the rule to edit")
            if rule_index is None:
                return
            _rule_params = self.rules[rule_index - 1]
            if _rule_params["name"] not in self.active_rules:
                break
            else:
                SimpleTUI.msg_dialog("Rule status",
                                     "You need to disable this rule before editing it!",
                                     SimpleTUI.DIALOG_ERROR)
        # Generic metric name (also referenced as "target")
        _target = SimpleTUI.input_dialog("Generic metric name",
                                         question="Insert a generic metric name (current: \"" + _rule_params["target"] + "\")",
                                         return_type=str,
                                         regex="^[a-zA-Z0-9_-]+$")
        if _target is None:
            return
        # Operator
        _operator = SimpleTUI.input_dialog("Rule operator",
                                           question="Insert a rule operator (current: \"" + _rule_params["operator"] + "\")",
                                           return_type=str,
                                           regex="^(<|<=|==|!=|>=|>)$")
        if _operator is None:
            return
        # Threshold
        _threshold = SimpleTUI.input_dialog("Rule threshold",
                                            question="Insert a rule threshold (current: \"" + str(_rule_params["threshold"]) + "\")",
                                            return_type=float)
        if _threshold is None:
            return

        # Action
        _action = SimpleTUI.input_dialog("Rule action",
                                         question="Insert a rule action (current: \"" + _rule_params["action"] + "\")",
                                         return_type=str,
                                         regex="^[a-zA-Z0-9_-]+$")
        if _action is None:
            return

        # Update rule, update rules file and issue a refresh command to the RuleEngine
        _rule_params["target"] = _target
        _rule_params["operator"] = _operator
        _rule_params["threshold"] = _threshold
        _rule_params["action"] = _action
        self._write_rules_to_file()
        # Send a message to the RuleEngine if it's running
        if self.is_monitor_running():
            self.re_cmd_queue.put({"command": "edit_rule", "rule": _rule_params})
        SimpleTUI.msg_dialog("Rule edited",
                             "This rule has been successfully edited!\nAll the changes will be applied to the RuleEngine starting from the next activity.",
                             SimpleTUI.DIALOG_SUCCESS)

    def delete_rule(self):
        """
        Wizard for deleting an existing rule
        """
        rule_index = SimpleTUI.list_dialog("Rules available",
                                           self.print_all_rules,
                                           question="Select the rule to delete")
        if rule_index is None:
            return
        rule = self.rules[rule_index - 1]
        self.rules.remove(rule)
        self._write_rules_to_file()
        if self.is_monitor_running():
            self.re_cmd_queue.put({"command": "remove_rule", "rule_name": rule["name"]})
        SimpleTUI.msg_dialog("Rule status",
                             "This rule has been deleted!\nAll the changes will be applied to the RuleEngine starting from the next activity.",
                             SimpleTUI.DIALOG_SUCCESS)

    # =============================================================================================== #
    #                                 RuleManager - Utility functions                                 #
    # =============================================================================================== #

    def _read_rules_from_file(self):
        """
        Read all the rules contained in rules/rules.dct
        """
        logging.debug("Reading rules...")
        try:
            with open("rules" + os.sep + "rules.dct") as file:
                _data = json.load(file)
            if("rules" in _data):
                self.rules = _data["rules"]
                logging.debug("All rules loaded")
            else:
                logging.error("Bad rules file format")
        except IOError as e:
            logging.error("An error has occourred while attempting to read rules: " + str(e))

    def _write_rules_to_file(self):
        """
        Write the current in-memory rules to a JSON file (stored in rules/rules.dct)
        """
        try:
            with open("rules" + os.sep + "rules.dct", "w") as file:
                file.write("%s\n" % json.dumps({"rules": self.rules}, sort_keys=False, indent=4))
        except IOError as e:
            SimpleTUI.exception_dialog(e)
            logging.error("There was an error while writing rules.dct: " + str(e))
