"""
EasyCloud Google Cloud Platform Manager
"""

import datetime
import pytz
import re
import time

from core.actionbinder import bind_action
from core.metamanager import MetaManager
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider
from modules.gcp_libcloud.actions import GCPAgentActions
from modules.gcp_libcloud.confmanager import GCPConfManager
from modules.gcp_libcloud.monitor import GCPMonitor
from tui.simpletui import SimpleTUI

__author__ = "Davide Monfrecola, Stefano Garione, Giorgio Gambino, Luca Banzato"
__copyright__ = "Copyright (C) 2019"
__credits__ = ["Andrea Lombardo", "Irene Lovotti"]
__license__ = "GPL v3"
__version__ = "0.10.0"
__maintainer__ = "Luca Banzato"
__email__ = "20005492@studenti.uniupo.it"
__status__ = "Prototype"


class GCP(MetaManager):

    def __init__(self):
        super().__init__()
        self.platform_name = "Google Cloud Platform"
        self.conf = GCPConfManager()
        self.cloned_instances = []
        # self.snapshots = None
        self.connect()

    # =============================================================================================== #
    #                                Platform-specific client creation                                #
    # =============================================================================================== #

    def connect(self):
        """
        Connection to the endpoint specified in the configuration file
        """
        # Define the authorization scopes the user needs to approve before using Google Cloud with EasyCloud
        # A list of Authorization scopes can be found at https://developers.google.com/identity/protocols/googlescopes
        scopes = ["https://www.googleapis.com/auth/compute",  # View and manage Google Compute Engine resources
                  "https://www.googleapis.com/auth/devstorage.full_control",  # Manage your data and permissions in Google Cloud Storage
                  "https://www.googleapis.com/auth/monitoring"  # View and write monitoring data for all of your Google projects
                  ]
        # Trying connection to endpoint
        cls = get_driver(Provider.GCE)
        self.gcp_client = cls(self.conf.gcp_access_key_id, self.conf.gcp_secret_access_key, scopes=scopes,
                              project=self.conf.gcp_project, datacenter=self.conf.gcp_datacenter)

    # =============================================================================================== #
    #                                  Platform-specific list printers                                #
    # =============================================================================================== #

    def print_all_nics(self):
        """
        Print instance id, image id, IP address and state for each active instance
        ! NOTE: before using this method, please set an instance using self.instance = <instance> !

        Returns:
            int: the number of items printed
        """
        table_header = ["ID", "NIC Name"]
        table_body = self._list_all_nics()
        SimpleTUI.print_table(table_header, table_body)
        if len(self.instances) == 0:
            SimpleTUI.info("There are no NICs available for this instance")
        return len(self.instances)

    def print_global_instances(self):
        """
        Print instance id, image id, IP address and state for each active instance in each region
        """
        table_header = ["ID", "Instance Name", "Instance ID",
                        "IP address", "Status", "Key Name", "Avail. Zone"]
        table_body = self._list_global_instances()
        SimpleTUI.print_table(table_header, table_body)
        if len(self.global_instances) == 0:
            SimpleTUI.info("There are no running or pending instances")
        return len(self.global_instances)

    def print_global_volumes(self):
        """
        Print all the available volumes for each region and some informations
        """
        table_header = ["ID", "Volume Name", "Volume ID",
                        "Creation", "Size (GB)", "Attached To", "Status", "Avail. Zone"]
        table_body = self._list_global_volumes()
        SimpleTUI.print_table(table_header, table_body)
        if len(self.global_volumes) == 0:
            SimpleTUI.info("There are no volumes available")
        return len(self.global_volumes)

    def print_global_floating_ips(self):
        """
        Print ip and other useful information of all floating ip available in each region
        """
        table_header = ["ID", "Public Ip",
                        "Floating IP ID", "Associated Instance", "Region"]
        table_body = self._list_global_floating_ips()
        SimpleTUI.print_table(table_header, table_body)
        if len(self.global_floating_ips) == 0:
            SimpleTUI.info("There are no floating IPs available")
        return len(self.global_floating_ips)

    # =============================================================================================== #
    #                                         List builders                                           #
    # =============================================================================================== #

    def _platform_list_all_images(self):
        """
        Print all available images
        Format: "ID", "Name", Image ID", "State"
        """
        self.images = self.gcp_client.list_images()
        i = 1
        table_body = []
        for image in self.images:
            table_body.append([i, image.name, image.id, image.extra["status"]])
            i = i + 1
        return table_body

    def _platform_list_all_availability_zones(self):
        """
        # Not used #
        Print all available images
        Format: "ID", "Name", Zone State", "Region Name"
        """
        self.avail_zones = self.gcp_client.ex_list_zones()
        i = 1
        table_body = []
        for avail_zone in self.avail_zones:
            table_body.append([i, avail_zone.name, avail_zone.status, avail_zone.country])
            i = i + 1
        return table_body

    def _platform_list_all_instance_types(self):
        """
        Print all instance types
        Format: "ID", "Instance Type ID", "vCPUs", "Ram (GB)", "Disk (GB)"
        """
        self.instance_types = self.gcp_client.list_sizes()
        if self.conf.alwaysfree_only:
            filtered_instance_types = []
            for instance_type in self.instance_types:
                if instance_type.name in self.conf.alwaysfree_instance_types:
                    filtered_instance_types.append(instance_type)
                self.instance_types = filtered_instance_types
        i = 1
        table_body = []
        for instance_type in self.instance_types:
            table_body.append([i, instance_type.name, instance_type.extra["guestCpus"],
                               instance_type.ram, instance_type.disk])
            i = i + 1
        return table_body

    def _platform_list_all_security_groups(self):
        """
        Print all security groups
        Format: "ID", "SG name", "SG description"
        """
        # Security groups not available on GCP
        # Please look for the firewalls
        pass

    def _platform_list_all_networks(self):
        """
        # Not used #
        Print id and other useful informations of all networks available
        Format: "ID", "Network name", "Description"
        """
        self.networks = self.gcp_client.ex_list_networks()
        i = 1
        table_body = []
        for network in self.networks:
            table_body.append([i, network.name, network.id])
            i = i + 1
        return table_body

    def _platform_list_all_firewalls(self):
        """
        Print informations about all the available firewalls
        Format: "ID", "Firewall name"
        """
        self.firewalls = self.gcp_client.ex_list_firewalls()
        i = 1
        table_body = []
        for firewall in self.firewalls:
            table_body.append([i, firewall.name])
            i = i + 1
        return table_body

    def _platform_list_all_key_pairs(self):
        """
        # Key pairs not available on GCP #

        Print all key pairs
        Format: "ID", "Key name", "Key fingerprint"
        """
        pass

    def _platform_list_all_instances(self):
        """
        Print instance id, image id, IP address and state for each active instance
        Format: "ID", "Instance Name", "Instance ID", "IP address", "Status", "Key Name", "Avail. Zone"
        """
        self.instances = self.gcp_client.list_nodes()
        i = 1
        table_body = []
        for instance in self.instances:
            if len(instance.public_ips) > 0 and None not in instance.public_ips:
                table_body.append([i, instance.name, instance.id, ", ".join(instance.public_ips), instance.state, "n/a", instance.extra["zone"].name])
            else:
                table_body.append([i, instance.name, instance.id, "-", instance.state, "n/a", instance.extra["zone"].name])
            i = i + 1
        return table_body

    def _platform_list_all_volumes(self):
        """
        Print volumes alongside informations regarding attachments
        Format: "Volume ID", "Creation", "Size (GB)", "Attached To", "Status", "Avail. Zone"
        """
        self.volumes = self.gcp_client.list_volumes()
        i = 1
        table_body = []
        for volume in self.volumes:
            created_at_timestamp = volume.extra["creationTimestamp"]
            # Fix for Python 3.x (< 3.7), strptime doesn't recognize the colons of timezone, so they must be removed
            # See https://stackoverflow.com/questions/54268458/datetime-strptime-issue-with-a-timezone-offset-with-colons
            timestamp_tz_fix = re.sub(r'([-+]\d{2}):(\d{2})(?:(\d{2}))?$', r'\1\2\3', created_at_timestamp)
            created_at_datetime = datetime.datetime.strptime(timestamp_tz_fix, "%Y-%m-%dT%H:%M:%S.%f%z")
            created_at = created_at_datetime.astimezone(pytz.utc).strftime("%b %d %Y, %H:%M:%S") + " UTC"
            instance = self._get_instance_from_volume(volume)
            if instance is not None:
                table_body.append([i, volume.name, volume.id, created_at, volume.size,
                                   instance.name, volume.extra["status"], volume.extra["zone"].name])
            else:
                table_body.append([i, volume.name, volume.id, created_at, volume.size,
                                   "-", volume.extra["status"], volume.extra["zone"].name])
            i = i + 1
        return table_body

    def _platform_list_all_floating_ips(self):
        """
        Print ip and other useful information of all floating ip available
        Format: "ID", "Public Ip", "Floating IP ID", "Associated Instance", "Region"
        """
        self.floating_ips = self.gcp_client.ex_list_addresses()
        i = 1
        table_body = []
        for floating_ip in self.floating_ips:
            instance = self._get_instance_from_floating_ip(floating_ip)
            if instance is not None:
                table_body.append([i, floating_ip.address, floating_ip.id, instance.name, floating_ip.region.name])
            else:
                table_body.append([i, floating_ip.address, floating_ip.id, "-", floating_ip.region.name])
            i = i + 1
        return table_body

    # =============================================================================================== #
    #                                Platform-specific list builders                                  #
    # =============================================================================================== #

    def _list_all_nics(self):
        """
        Print id and other useful informations of all network interfaces
        available for a certain instance
        Format: "ID", "Network name", "IP Address"
        """
        i = 1
        table_body = []
        for network_interface in self.current_instance.extra["networkInterfaces"]:
            table_body.append([i, network_interface["name"], network_interface["networkIP"]])
            i = i + 1
        return table_body

    def _list_all_assigned_ips(self):
        self.instances = self.gcp_client.list_nodes()
        self.assigned_ips = []
        i = 1
        table_body = []
        for instance in self.instances:
            if len(instance.public_ips) > 0 and None not in instance.public_ips:
                self.assigned_ips.append(instance.public_ips[0])
                table_body.append([i, instance.public_ips[0], instance.name])
            i = i + 1
        return table_body

    def _list_global_instances(self):
        """
        Print instance id, image id, IP address and state for all the instances in all the zones
        Format: "ID", "Instance Name", "Instance ID", "IP address", "Status", "Key Name", "Avail. Zone"
        """
        self.global_instances = []
        zones = self.gcp_client.ex_list_zones()
        for zone in zones:
            self.global_instances += self.gcp_client.list_nodes(ex_zone=zone)
        i = 1
        table_body = []
        for instance in self.global_instances:
            if len(instance.public_ips) > 0 and None not in instance.public_ips:
                table_body.append([i, instance.name, instance.id, ", ".join(instance.public_ips), instance.state, "n/a", instance.extra["zone"].name])
            else:
                table_body.append([i, instance.name, instance.id, "-", instance.state, "n/a", instance.extra["zone"].name])
            i = i + 1
        return table_body

    def _list_global_volumes(self):
        """
        Print volumes alongside informations regarding attachments for all the volumes in all the zones
        Format: "Volume ID", "Creation", "Size (GB)", "Attached To", "Status", "Avail. Zone"
        """
        self.global_volumes = []
        zones = self.gcp_client.ex_list_zones()
        for zone in zones:
            self.global_volumes += self.gcp_client.list_volumes(ex_zone=zone)
        i = 1
        table_body = []
        for volume in self.global_volumes:
            created_at_timestamp = volume.extra["creationTimestamp"]
            # Fix for Python 3.x (< 3.7), strptime doesn't recognize the colons of timezone, so they must be removed
            # See https://stackoverflow.com/questions/54268458/datetime-strptime-issue-with-a-timezone-offset-with-colons
            timestamp_tz_fix = re.sub(r'([-+]\d{2}):(\d{2})(?:(\d{2}))?$', r'\1\2\3', created_at_timestamp)
            created_at_datetime = datetime.datetime.strptime(timestamp_tz_fix, "%Y-%m-%dT%H:%M:%S.%f%z")
            created_at = created_at_datetime.astimezone(pytz.utc).strftime("%b %d %Y, %H:%M:%S") + " UTC"
            instance = self._get_instance_from_volume(volume)
            if instance is not None:
                table_body.append([i, volume.name, volume.id, created_at, volume.size,
                                   instance.name, volume.extra["status"], volume.extra["zone"].name])
            else:
                table_body.append([i, volume.name, volume.id, created_at, volume.size,
                                   "-", volume.extra["status"], volume.extra["zone"].name])
            i = i + 1
        return table_body

    def _list_global_floating_ips(self):
        """
        Print ip and other useful information of all floating ip available
        Format: "ID", "Public Ip", "Floating IP ID", "Associated Instance", "Region"
        """
        self.global_floating_ips = self.gcp_client.ex_list_addresses(region="all")
        i = 1
        table_body = []
        for floating_ip in self.global_floating_ips:
            instance = self._get_instance_from_floating_ip(floating_ip)
            if instance is not None:
                table_body.append([i, floating_ip.address, floating_ip.id, instance.name, floating_ip.region.name])
            else:
                table_body.append([i, floating_ip.address, floating_ip.id, "-", floating_ip.region.name])
            i = i + 1
        return table_body

    # =============================================================================================== #
    #                                       Actions and Menus                                         #
    # =============================================================================================== #

    def _platform_get_region(self):
        """
        Get current region name

        Returns:
            str: the name of the current region
        """
        return self.conf.gcp_datacenter

    def _platform_create_new_instance(self, instance_name, image, instance_type, monitor_cmd_queue=None):
        """
        Create a new instance using the Google Cloud Platform API

        Args:
            instance_name (str): The name of the instance
            image (<image_type>): The image to be used as a base system
            instance_type (<instance_type>): The VM flavor
            monitor_cmd_queue: the monitor commands Quue
        """

        # Creation summary
        print("\n--- Creating a new instance with the following properties:")
        print("- %-20s %-30s" % ("Name", instance_name))
        print("- %-20s %-30s" % ("Image", image.name))
        print("- %-20s %-30s" % ("Instance Type", instance_type.name))

        # ask for confirm
        print("")
        if(SimpleTUI.user_yn("Are you sure?")):
            instance = self.gcp_client.create_node(name=instance_name,
                                                   size=instance_type,
                                                   image=image)
            if instance is None:
                return False
            if monitor_cmd_queue is not None and self.is_monitor_running():
                monitor_cmd_queue.put({"command": "add", "instance_id": instance.id})
            return True

    def _platform_instance_action(self, instance, action):
        """
        Handle an instance action with Google Cloud Platform API
        """
        if action == "reboot":
            return instance.reboot()
        elif action == "delete":
            return instance.destroy()

    def _platform_get_instance_info(self):
        """
        Return a list of instances info
        """
        info = []
        for instance in self.gcp_client.get_only_instances():
            info.append({"id": instance.id, "name": instance.name})
        return info

    def _platform_is_volume_attached(self, volume):
        """
        Check if a volume is attached to an instance

        Args:
            volume (<volume>): The volume to check

        Returns:
            bool: True if the volume is successfully attached, False otherwise
        """
        for instance in self.gcp_client.list_nodes():
            disks = instance.extra["disks"]
            if len(disks) > 0:
                for disk in disks:
                    if volume.name == disk["deviceName"]:
                        return True
        return False

    def _platform_detach_volume(self, volume):
        """
        Detach a volume using the Google Cloud Platform API
        Some specific steps are performed here:
            - Check if the selected volume is a boot disk

        Args:
            volume (<volume>): The volume to detach

        Returns:
            bool: True if the volume is successfully detached, False otherwise
        """
        # Search for the instance the volume is attached to
        instance = self._get_instance_from_volume(volume)
        if instance is None:
            return False
        if not self._is_volume_removable(volume):
            SimpleTUI.msg_dialog("Detaching status",
                                 "This volume is mounted as boot disk and cannot be detached until the VM is stopped!",
                                 SimpleTUI.DIALOG_ERROR)
            return
        result = self.gcp_client.detach_volume(volume, instance)
        if result:
            while True:
                # No direct way to refresh a Volume status, so we look if
                # it is still attached to its previous instance
                updated_volume = self.gcp_client.ex_get_volume(volume.name)
                if not self._platform_is_volume_attached(updated_volume):
                    break
                time.sleep(3)
        return result

    def _platform_delete_volume(self, volume):
        """
        Delete a volume using the Google Cloud Platform API
        Some specific steps are performed here:
            - Check if the selected volume is a boot disk

        Args:
            volume (<volume>): The volume to delete

        Returns:
            bool: True if the volume is successfully deleted, False otherwise
        """
        if not self._is_volume_removable(volume):
            SimpleTUI.msg_dialog("Volume deletion",
                                 "This volume is mounted as boot disk and cannot be detached until the VM is stopped!",
                                 SimpleTUI.DIALOG_ERROR)
            return
        return self.gcp_client.destroy_volume(volume)

    def _platform_attach_volume(self, volume, instance):
        """
        Attach a volume using the Google Cloud Platform API
        Some specific steps are performed here:
            - Device name (the name assigned to this device visible through the VM OS)
            - Mount mode (read only or read write)
            - Disk interface (SCSI or NVME)

        Args:
            volume (<volume>): The volume to attach
            instance (<instance>): The instance where the volume is to be attached

        Returns:
            bool: True if the volume is attached successfully, False otherwise
        """
        # Ask for mount ro/rw
        ro_rw = SimpleTUI.input_dialog("Mount mode",
                                       question="Specify a mount mode (READ_WRITE, READ_ONLY)",
                                       return_type=str,
                                       regex="^(READ_WRITE|READ_ONLY)$")
        if ro_rw is None:
            return
        # Ask for disk interface
        interface = SimpleTUI.input_dialog("Disk interface",
                                           question="Specify disk interface (SCSI, NVME)",
                                           return_type=str,
                                           regex="^(SCSI|NVME)$")
        return self.gcp_client.attach_volume(node=instance, volume=volume, device=volume.name,
                                             ex_boot=False, ex_auto_delete=False, ex_interface=interface)

    def _platform_create_volume(self, volume_name, volume_size):
        """
        Create a new volume using the Google Cloud Platform API
        Some specific steps are performed here:
            - Volume type (pd-standard or pd-ssd)

        Args:
            volume_name (str): Volume name
            volume_size (int): Volume size in GB

        Returns:
            bool: True if the volume is successfully created, False otherwise
        """
        # Volume type
        volume_type = SimpleTUI.input_dialog("Volume type",
                                             question="Specify the volume type (pd-standard, pd-ssd)",
                                             return_type=str,
                                             regex="^(pd-standard|pd-ssd)$")
        if volume_type is None:
            return
        # Volume creation
        return self.gcp_client.create_volume(size=volume_size, name=volume_name,
                                             ex_disk_type=volume_type)

    def _platform_is_ip_assigned(self, floating_ip):
        """
        # Not supported on GCP #
        Check if a floating IP is assigned to an instance

        Args:
            floating_ip (GCEAddress): The floating IP to check

        Returns:
            bool: True if the floating IP is assigned, False otherwise
        """
        return False

    def _platform_detach_floating_ip(self, floating_ip):
        # Not supported on GCP #
        """
        Detach a floating IP using the Google Cloud Platform API

        Args:
            floating_ip (GCEAddress): The floating IP to detach

        Returns:
            bool: True if the floating IP is successfully detached, False otherwise
        """
        pass

    def _platform_release_floating_ip(self, floating_ip):
        """
        Release a floating IP using the Google Cloud Platform API

        Args:
            floating_ip (GCEAddress): The floating IP to release

        Returns:
            bool: True if the floating IP is successfully released, False otherwise
        """
        return self.gcp_client.ex_destroy_address(floating_ip)

    def _platform_associate_floating_ip(self, floating_ip, instance):
        """
        Associate a floating IP to an instance using the Google Cloud Platform API
        Some specific steps are performed here:
            - NIC (Network interface controller) selection
            - Access config name

        Args:
            floating_ip (GCEAddress): The floating IP to attach
            instance (Node): The instance where the floating IP is to be assigned

        Returns:
            bool: True if the floating IP is successfully associated, False otherwise
        """
        # Set an instance, as required by print_all_nics()
        self.current_instance = instance
        nic_index = SimpleTUI.list_dialog("NICs available",
                                          self.print_all_nics,
                                          question="Select the VM NIC to assign this IP")
        if nic_index is None:
            return
        nic = instance.extra["networkInterfaces"][nic_index - 1]  # serve nome per rimuovere
        # Check if there's already an active Access Configuration and ask the user for confirm
        remove_old_access_config = False
        if self._nic_has_access_config(nic):
            choice = SimpleTUI.yn_dialog("Access Configuration Overwrite",
                                         "Warning: there's already an access configuration associated to this NIC.\n" +
                                         "Do you really want to continue (the current access configuration will be overwritten)?",
                                         warning=True)
            if not choice:
                return
            remove_old_access_config = True
        # Access Configuration name
        access_config_name = SimpleTUI.input_dialog("Access configuration",
                                                    question="Specify an access configuration name",
                                                    return_type=str,
                                                    regex="^[a-zA-Z0-9-]+$")
        if access_config_name is None:
            return
        # Remove the old access configuration if it's already existing
        if remove_old_access_config:
            SimpleTUI.msg_dialog("Access Configuration Overwrite", "Removing old access configuration...",
                                 SimpleTUI.DIALOG_INFO, pause_on_exit=False, clear_on_exit=False)
            if not self._delete_access_config(instance, nic):
                SimpleTUI.msg_dialog("Access Configuration Overwrite",
                                     "There was an error while removing the current access configuration!",
                                     SimpleTUI.DIALOG_ERROR)
                return
        # Associate the Access Configuration to the NIC
        if self.gcp_client.ex_add_access_config(node=instance, name=access_config_name,
                                                nic=nic, nat_ip=floating_ip.address,
                                                config_type="ONE_TO_ONE_NAT"):
            return True
        return False

    def _platform_reserve_floating_ip(self):
        """
        Reserve a floating IP using the Google Cloud Platform API
        """
        address_name = SimpleTUI.input_dialog("Floating IP Name",
                                              question="Specify a name for the new Floating IP",
                                              return_type=str,
                                              regex="^[a-zA-Z0-9-]+$")
        if address_name is None:
            return
        if self.gcp_client.ex_create_address(name=address_name):
            return True
        return False

    def _platform_get_monitor(self, commands_queue, measurements_queue):
        """
        Create the Google Cloud Platform Monitor using StackDriver APIs

        Args:
            commands_queue (Queue): message queue for communicating with the main
                                    thread and receiving commands regarding the metrics
                                    to observe
            measurements_queue (Queue): message queue for sending measurements to
                                        the platform RuleEngine

        Returns:
            MetaMonitor: the platform-specific monitor
        """
        self.instances = self.gcp_client.list_nodes()
        for instance in self.instances:
            commands_queue.put({"command": "add", "instance_id": instance.name})
        return GCPMonitor(conf=self.conf,
                          commands_queue=commands_queue,
                          measurements_queue=measurements_queue)

    # =============================================================================================== #
    #                               Platform-specific Actions and Menus                               #
    # =============================================================================================== #

    def _nic_has_access_config(self, nic):
        """
        Check if an access configuration is assigned to a NIC

        Args:
            nic (NetworkInterface): The NIC to check

        Returns:
            bool: True if an access_configuration is already assigned
                  to this NIC, False otherwise
        """
        if len(nic["accessConfigs"]) > 0:
            return True
        return False

    def _is_volume_removable(self, volume):
        """
        Check if the volume can be detached from an instance or deleted

        Args:
            volume (StorageVolume): The volume to check
        """
        for instance in self.gcp_client.list_nodes(ex_zone=volume.extra["zone"]):
            disks = instance.extra["disks"]
            if len(disks) > 0:
                for disk in disks:
                    if volume.name == disk["deviceName"] and disk["boot"] and instance.state != "stopped":
                        return False
        return True

    def _delete_access_config(self, instance, nic):
        """
        Delete an access config associated to a network interface of a VM

        Args:
            instance (Node): The instanceto which the access config is
                             associated
            access_config_name (str): The access configuration name
            nic (str): The network interface controller name
        """
        return self.gcp_client.ex_delete_access_config(node=instance,
                                                       name=nic["accessConfigs"][0]["name"],
                                                       nic=nic["name"])

    def _get_instance_from_volume(self, volume):
        """
        Return the instance to which the volume is attached

        Args:
            volume (StorageVolume): the volume attached to an instance

        Returns:
            Node: an instance, or None if no instances are found
        """
        for instance in self.gcp_client.list_nodes(ex_zone=volume.extra["zone"]):
            disks = instance.extra["disks"]
            if len(disks) > 0:
                for disk in disks:
                    if volume.name == disk["deviceName"]:
                        return instance
        return None

    def _get_instance_from_floating_ip(self, floating_ip):
        """
        Return the instance to which the floating IP is attached

        Args:
            floating_ip (GCEAddress): the floating IP attached to an instance

        Returns:
            Node: an instance, or None if no instances are found
        """
        for instance in self.gcp_client.list_nodes(ex_zone="all"):
            if len(instance.public_ips) > 0 and None not in instance.public_ips:
                if instance.public_ips[0] == floating_ip.address:
                    return instance
        return None

    def _is_instance_floating_ip_static(self, instance):
        """
        Check if the floating IP is promoted to static

        Args:
            floating_ip (Node): The instance to check

        Returns:
            bool: True if the attached floating IP is static, false otherwise
        """
        if len(instance.public_ips) == 0 or None in instance.public_ips:
            return False
        self.floating_ips = self.gcp_client.ex_list_addresses()
        for floating_ip in self.floating_ips:
            if instance.public_ips[0] == floating_ip.address:
                return True
        return False

    def promote_ephimeral_ip(self):
        """
        Promote an Ephimeral IP to a Static one
        For more infos about Ephimeral/Static IPs on GCP, please visit
        https://cloud.google.com/compute/docs/ip-addresses/
        """
        # Select an instance
        floating_ip = None
        while(True):
            instance_index = SimpleTUI.list_dialog("Instances available",
                                                   self.print_all_instances,
                                                   question="Select the instance which floating IP has to be promoted to \"static\"")
            if instance_index is None:
                return
            instance = self.instances[instance_index - 1]
            # Check if the instance has an IP assigned (e.g. no IP is assigned while stopped)
            if len(instance.public_ips) == 0 or None in instance.public_ips:
                SimpleTUI.msg_dialog("Promotion status", "This instance has no available floating IPs to promote!",
                                     SimpleTUI.DIALOG_ERROR)
            # Check if the instance has already a static IP assigned
            elif self._is_instance_floating_ip_static(instance):
                SimpleTUI.msg_dialog("Promotion status", "This instance floating IP is already promoted to \"static\"!",
                                     SimpleTUI.DIALOG_ERROR)
            # Continue the ephimeral to static conversion
            else:
                floating_ip = instance.public_ips[0]
                break
        # Specify address name
        address_name = SimpleTUI.input_dialog("Static Floating IP Name",
                                              question="Specify a name for the new Static Floating IP",
                                              return_type=str,
                                              regex="^[a-zA-Z0-9-]+$")
        if address_name is None:
            return
        if self._promote_ephimeral_ip_to_static(floating_ip, address_name):
            SimpleTUI.msg_dialog("Static Floating IP Promotion", "Floating IP promoted!", SimpleTUI.DIALOG_SUCCESS)
        else:
            SimpleTUI.msg_dialog("Static Floating IP Promotion", "There was an error while promoting this Floating IP!", SimpleTUI.DIALOG_ERROR)

    def _promote_ephimeral_ip_to_static(self, floating_ip, address_name):
        """
        Create a new static ip starting from an ephimeral one

        Args:
            floating_ip (str): the IP to promote
            address_name (str): the symbolic name to assign to the new static IP

        Returns:
            bool: True if the creation is a success, False otherwise
        """
        return self.gcp_client.ex_create_address(name=address_name, address=floating_ip)

    def _platform_extra_menu(self):
        """
        Print the extra Functions Menu (specific for each platform)
        """
        while(True):
            menu_header = self.platform_name + " Extra Commands"
            menu_subheader = ["Region: \033[1;94m" +
                              self._platform_get_region() + "\033[0m"]
            menu_items = ["Promote ephimeral IP to static",
                          "Demote a static IP",
                          "List instances for all the regions",
                          "List volumes for all the regions",
                          "List floating ips for all the regions",
                          "Back to the Main Menu"]
            choice = SimpleTUI.print_menu(menu_header, menu_items, menu_subheader)
            if choice == 1:  # Promote IP
                self.promote_ephimeral_ip()
            elif choice == 2:  # Demote IP
                answer = SimpleTUI.yn_dialog("Demotion status",
                                             "You can demote a static IP easily deleting it through \"Manage floating IPs\" > \"Release a reserved Floating IP\".\n" +
                                             "NOTE: the static IP won't be removed from the associated instance until the latter is stopped/rebooted/deleted.\n" +
                                             "For more infos about Ephimeral/Static IPs on GCP, please visit https://cloud.google.com/compute/docs/ip-addresses/.\n" +
                                             "Would you like to start the \"Release a reserved Floating IP\" wizard now?", SimpleTUI.DIALOG_INFO)
                if answer:
                    self.release_floating_ip()
            elif choice == 3:  # List all the instances (Global)
                SimpleTUI.list_dialog("Instances available (Global view)",
                                      list_printer=self.print_global_instances)
            elif choice == 4:  # List all the volumes (Global)
                SimpleTUI.list_dialog("Volumes available (Global view)",
                                      list_printer=self.print_global_volumes)
            elif choice == 5:  # List all the floating ips (Global)
                SimpleTUI.list_dialog("Floating IPs available (Global view)",
                                      list_printer=self.print_global_floating_ips)
            elif choice == 6:
                break
            else:
                SimpleTUI.msg_dialog("Error", "Unimplemented functionality", SimpleTUI.DIALOG_ERROR)

    # =============================================================================================== #
    #                                         Override methods                                        #
    # =============================================================================================== #

    override_main_menu = []
    override_ips_menu = [5]
    override_volumes_menu = []

    def _platform_is_overridden(self, menu, choice):
        """
        Check if a menu voice is overridden by this platform

        Args:
            menu (str): a menu identifier
            choice (int): a menu entry index

        Returns:
            bool: the override status (True/False)
        """
        if menu == "floating_ips" and choice in self.override_ips_menu:
            if choice == 5:  # Volumes on barebone are not supported
                return True
        return False

    def _platform_override_menu(self, menu, choice):
        """
        Override a menu voice

        Args:
            menu (str): a menu identifier
            choice (int): a menu entry index

        Returns:
            int: 0 for normal, 1 for going back to the main menu of EasyCloud,
                 2 for closing the whole application
        """
        if menu == "floating_ips":
            if choice == 5:  # Detach floating ip
                SimpleTUI.msg_dialog("Detach Floating IP", "Detaching an IP address from an instance is not supported on GCP: \n" +
                                     "an instance must always have an IP associated while running.\n" +
                                     "However, you can assign another address to the desired instance to\n" +
                                     "replace the current one.",
                                     SimpleTUI.DIALOG_INFO)
                return 0
            SimpleTUI.error("Unavailable choice!")
            SimpleTUI.pause()
            SimpleTUI.clear_console()
        pass

    # =============================================================================================== #
    #                                  RuleEngine Actions Definition                                  #
    # =============================================================================================== #

    # All the actions are defined in the actions.py file in the module directory
    # Note: the platform name passed on the decorator must be equal to this class name

    @bind_action("GCP", "clone")
    def clone_instance(self, instance_id):
        """
        Clone instance
        """
        GCPAgentActions.clone_instance(self, instance_id)

    @bind_action("GCPCloud", "alarm")
    def alarm(self, resource_id):
        """
        Trigger an alarm
        """
        GCPAgentActions.alarm(self, resource_id)
