"""
EasyCloud Amazon Web Services Manager
"""

# For a list of valid filters to use with the ex_filter parameter of certain methods,
# please visit https://docs.aws.amazon.com/en_us/AWSEC2/latest/APIReference/API_Operations.html

import time

from core.actionbinder import bind_action
from core.metamanager import MetaManager
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider
from modules.aws_libcloud.actions import AWSAgentActions
from modules.aws_libcloud.confmanager import AWSConfManager
from modules.aws_libcloud.monitor import AWSMonitor
from tui.simpletui import SimpleTUI

__author__ = "Davide Monfrecola, Stefano Garione, Giorgio Gambino, Luca Banzato"
__copyright__ = "Copyright (C) 2019"
__credits__ = ["Andrea Lombardo", "Irene Lovotti"]
__license__ = "GPL v3"
__version__ = "0.10.0"
__maintainer__ = "Luca Banzato"
__email__ = "20005492@studenti.uniupo.it"
__status__ = "Prototype"


class AWS(MetaManager):

    def __init__(self):
        super().__init__()
        self.platform_name = "Amazon Web Services"
        self.conf = AWSConfManager()
        self.cloned_instances = []
        # self.snapshots = None
        self.connect()

    # =============================================================================================== #
    #                                Platform-specific client creation                                #
    # =============================================================================================== #

    def connect(self):
        """
        Connection to Amazon Web Services
        """
        cls = get_driver(Provider.EC2)
        self.ec2_client = cls(self.conf.ec2_access_key_id,
                              self.conf.ec2_secret_access_key,
                              token=self.conf.ec2_session_token,
                              region=self.conf.ec2_default_region)

    # =============================================================================================== #
    #                                  Platform-specific list printers                                #
    # =============================================================================================== #

    # Nothing here

    # =============================================================================================== #
    #                                         List builders                                           #
    # =============================================================================================== #

    def _platform_list_all_images(self):
        """
        Print all available images
        Format: "ID", "Name", Image ID", "State"
        """
        if self.conf.freetier_only:
            # Use free-tier images
            self.images = self.ec2_client.list_images(ex_image_ids=self.conf.freetier_images_ids)
        else:
            # Use image filters
            self.images = self.ec2_client.list_images(
                ex_filters={"name": self.conf.images_filters})
        i = 1
        table_body = []
        for image in self.images:
            table_body.append([i, image.name, image.id, image.extra["state"]])
            i = i + 1
        return table_body

    def _platform_list_all_availability_zones(self):
        """
        Print all available images
        Format: "ID", "Name", Zone State", "Region Name"
        """
        self.avail_zones = self.ec2_client.list_locations()
        i = 1
        table_body = []
        for avail_zone in self.avail_zones:
            table_body.append([i, avail_zone.availability_zone.name,
                               avail_zone.availability_zone.zone_state, avail_zone.availability_zone.region_name])
            i = i + 1
        return table_body

    def _platform_list_all_instance_types(self):
        """
        Print all instance types
        Format: "ID", "Instance Type ID", "vCPUs", "Ram (GB)", "Disk (GB)"
        """
        self.instance_types = self.ec2_client.list_sizes()
        if self.conf.freetier_only:
            filtered_instance_types = []
            for instance_type in self.instance_types:
                if instance_type.id in self.conf.freetier_instance_types:
                    filtered_instance_types.append(instance_type)
                self.instance_types = filtered_instance_types
        i = 1
        table_body = []
        for instance_type in self.instance_types:
            table_body.append([i, instance_type.id, instance_type.extra["vcpu"],
                               instance_type.ram / 1024,
                               str(instance_type.disk) + " (" + instance_type.extra["storage"] + ")"])
            i = i + 1
        return table_body

    def _platform_list_all_security_groups(self):
        """
        Print all security groups
        Format: "ID", "SG name", "SG description"
        """
        # Here a list of str is returned (the docs say list of EC2SecurityGroup)
        self.security_groups = self.ec2_client.ex_list_security_groups()
        i = 1
        table_body = []
        for security_group in self.security_groups:
            table_body.append([i, security_group, "n/a"])
            i = i + 1
        return table_body

    def _platform_list_all_networks(self):
        """
        Print id and other useful informations of all networks available
        Format: "ID", "Network name", "Description"
        """
        self.networks = self.ec2_client.ex_list_networks()
        i = 1
        table_body = []
        for network in self.networks:
            table_body.append([i, network.name, network.id])
            i = i + 1
        return table_body

    def _platform_list_all_key_pairs(self):
        """
        Print all key pairs
        Format: "ID", "Key name", "Key fingerprint"
        """
        self.key_pairs = self.ec2_client.list_key_pairs()
        i = 1
        table_body = []
        for key_pair in self.key_pairs:
            table_body.append([i, key_pair.name, key_pair.fingerprint])
            i = i + 1
        return table_body

    def _platform_list_all_instances(self):
        """
        Print instance id, image id, IP address and state for each active instance
        Format: "ID", "Instance Name", "Instance ID", "IP address", "Status", "Key Name", "Avail. Zone"
        """
        self.instances = self.ec2_client.list_nodes()
        i = 1
        table_body = []
        for instance in self.instances:
            if len(instance.public_ips) > 0 and None not in instance.public_ips:
                table_body.append([i, instance.name, instance.id, ", ".join(instance.public_ips), instance.state, instance.extra["key_name"], instance.extra["availability"]])
            else:
                table_body.append([i, instance.name, instance.id, "-", instance.state, instance.extra["key_name"], instance.extra["availability"]])
            i = i + 1
        return table_body

    def _platform_list_all_volumes(self):
        """
        Print volumes alongside informations regarding attachments
        Format: "Volume ID", "Creation", "Size (GB)", "Attached To", "Status"
        """
        self.volumes = self.ec2_client.list_volumes()
        i = 1
        table_body = []
        for volume in self.volumes:
            created_at = volume.extra["create_time"].strftime("%b %d %Y, %H:%M:%S") + " UTC"
            if volume.extra["instance_id"] is not None:
                node = self.ec2_client.list_nodes(ex_node_ids=[volume.extra["instance_id"]])[0]
                table_body.append([i, volume.name, volume.id, created_at, volume.size,
                                   node.name + " (" + volume.extra["device"] + ")", volume.state, volume.extra["zone"]])
            else:
                table_body.append([i, volume.name, volume.id, created_at, volume.size,
                                   "- (-)", volume.state, volume.extra["zone"]])
            i = i + 1
        return table_body

    def _platform_list_all_floating_ips(self):
        """
        Print ip and other useful information of all floating ip available
        Format: ""ID", "Public Ip", "Floating IP ID", "Associated Instance"
        """
        self.floating_ips = self.ec2_client.ex_describe_all_addresses()
        i = 1
        table_body = []
        for floating_ip in self.floating_ips:
            if(floating_ip.instance_id is not None):
                node = self.ec2_client.list_nodes(ex_node_ids=[floating_ip.instance_id])[0]
                if(node is not None):
                    table_body.append([i, floating_ip.ip, floating_ip.extra["allocation_id"], node.name, "n/a"])
                else:
                    table_body.append([i, floating_ip.ip, floating_ip.extra["allocation_id"], "Load Balancer", "n/a"])
            else:
                table_body.append([i, floating_ip.ip, floating_ip.extra["allocation_id"], "-", "n/a"])
            i = i + 1
        return table_body

    # =============================================================================================== #
    #                                Platform-specific list builders                                  #
    # =============================================================================================== #

    # Nothing here

    # =============================================================================================== #
    #                                       Actions and Menus                                         #
    # =============================================================================================== #

    def _platform_get_region(self):
        """
        Get current region name

        Returns:
            str: the name of the current region
        """
        return self.conf.ec2_default_region

    def _platform_create_new_instance(self, instance_name, image, instance_type, monitor_cmd_queue=None):
        """
        Create a new instance using the Amazon Web Services API
        Some specific steps are performed here:
            - Ask for security group
            - Ask for key pair
            - Instance creation summary

        Args:
            instance_name (str): The name of the instance
            image (<image_type>): The image to be used as a base system
            instance_type (<instance_type>): The VM flavor
            monitor_cmd_queue: the monitor commands Quue
        """
        # 5. Security Group
        security_group_index = SimpleTUI.list_dialog("Security Groups available",
                                                     self.print_all_security_groups,
                                                     question="Select security group")
        if security_group_index is None:
            return
        security_group = self.security_groups[security_group_index - 1]
        # 6. Key Pair
        key_pair_index = SimpleTUI.list_dialog("Key Pairs available",
                                               self.print_all_key_pairs,
                                               question="Select key pair")
        if key_pair_index is None:
            return
        key_pair = self.key_pairs[key_pair_index - 1]

        # Creation summary
        print("\n--- Creating a new instance with the following properties:")
        print("- %-20s %-30s" % ("Name", instance_name))
        print("- %-20s %-30s" % ("Image", image.name))
        print("- %-20s %-30s" % ("Instance Type", instance_type.name))
        print("- %-20s %-30s" % ("Key Pair", key_pair.name))
        print("- %-20s %-30s" % ("Security Group", security_group))

        # ask for confirm
        print("")
        if(SimpleTUI.user_yn("Are you sure?")):
            instance = self.ec2_client.create_node(name=instance_name,
                                                   image=image,
                                                   size=instance_type,
                                                   ex_keyname=key_pair.name,
                                                   ex_security_groups=[security_group],
                                                   ex_monitoring=True,
                                                   ex_mincount=1,
                                                   ex_maxcount=1)
            if instance is None:
                return False
            if monitor_cmd_queue is not None and self.is_monitor_running():
                monitor_cmd_queue.put({"command": "add", "instance_id": instance.id})
            return True

    def _platform_instance_action(self, instance, action):
        """
        Handle an instance action with Amazon Web Services API
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
        for instance in self.ec2_client.list_nodes():
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
        if volume.extra["instance_id"] is None:
            return False
        return True

    def _platform_detach_volume(self, volume):
        """
        Detach a volume using the Amazon Web Services API

        Args:
            volume (<volume>): The volume to detach

        Returns:
            bool: True if the volume is successfully detached, False otherwise
        """
        result = self.ec2_client.detach_volume(volume)
        if result:
            while True:
                # No direct way to refresh a Volume status, so we look if
                # it is still attached to its previous instance
                node = self.ec2_client.list_nodes(ex_node_ids=[volume.extra["instance_id"]])[0]
                node_volumes = self.ec2_client.list_volumes(node=node)
                is_present = False
                for node_volume in node_volumes:
                    if node_volume.id == volume.id:
                        is_present = True
                        break
                if not is_present:
                    break
                time.sleep(3)
        return result

    def _platform_delete_volume(self, volume):
        """
        Delete a volume using the Amazon Web Services API

        Args:
            volume (<volume>): The volume to delete

        Returns:
            bool: True if the volume is successfully deleted, False otherwise
        """
        return self.ec2_client.destroy_volume(volume)

    def _platform_attach_volume(self, volume, instance):
        """
        Attach a volume using the Amazon Web Services API
        Some specific steps are performed here:
            - Exposure point (e.g. /dev/sdb)

        Args:
            volume (<volume>): The volume to attach
            instance (<instance>): The instance where the volume is to be attached

        Returns:
            bool: True if the volume is attached successfully, False otherwise
        """
        # Ask for exposure point (the GNU/Linux device where this volume will
        # be available)
        exposure_point = SimpleTUI.input_dialog("Exposure point",
                                                question="Specify where the device is exposed, e.g. ‘/dev/sdb’",
                                                return_type=str,
                                                regex="^(/[^/ ]*)+/?$")
        if exposure_point is None:
            return
        return self.ec2_client.attach_volume(instance, volume, exposure_point)

    def _platform_create_volume(self, volume_name, volume_size):
        """
        Create a new volume using the Amazon Web Services API
        Some specific steps are performed here:
            - Volume type (standard or io1)
            - IOPS (only if io1 is selected)
            - Zone selection (required)

        Args:
            volume_name (str): Volume name
            volume_size (int): Volume size in GB

        Returns:
            bool: True if the volume is successfully created, False otherwise
        """
        # Volume type
        volume_type = SimpleTUI.input_dialog("Volume type",
                                             question="Specify the volume type (standard, io1)",
                                             return_type=str,
                                             regex="^(standard|io1)$")
        if volume_type is None:
            return
        # IOPS
        iops = None
        if volume_type == "io1":
            iops = SimpleTUI.input_dialog("IOPS limit",
                                          question="Specify the number of IOPS (I/O operations per second) the volume has to support",
                                          return_type=int)
            if iops is None:
                return
        # Zone selection
        zone_index = SimpleTUI.list_dialog("Zones available",
                                           self.print_all_availability_zones,
                                           question="Select a zone where the volume will be created")
        if zone_index is None:
            return
        zone = self.avail_zones[zone_index - 1]
        # Volume creation
        return self.ec2_client.create_volume(name=volume_name, size=volume_size, location=zone,
                                             ex_volume_type=volume_type, ex_iops=iops)

    def _platform_is_ip_assigned(self, floating_ip):
        """
        Check if a floating IP is assigned to an instance

        Args:
            floating_ip (<floating_ip>): The floating IP to check

        Returns:
            bool: True if the floating IP is assigned, False otherwise
        """
        if(floating_ip.instance_id is not None):
            return True
        return False

    def _platform_detach_floating_ip(self, floating_ip):
        """
        Detach a floating IP using the Amazon Web Services API

        Args:
            floating_ip (<floating_ip>): The floating IP to detach

        Returns:
            bool: True if the floating IP is successfully detached, False otherwise
        """
        result = self.ec2_client.ex_disassociate_address(floating_ip, domain="vpc")
        if(result):
            while True:
                # No direct way to refresh a Floating IP, so we look if
                # it is still attached to its previous instance
                node = self.ec2_client.list_nodes(ex_node_ids=[floating_ip.instance_id])[0]
                node_floating_ips = self.ec2_client.ex_describe_addresses_for_node(node)
                if floating_ip.ip not in node_floating_ips:
                    break
                time.sleep(3)
        return result

    def _platform_release_floating_ip(self, floating_ip):
        """
        Release a floating IP using the Amazon Web Services API

        Args:
            floating_ip (<floating_ip>): The floating IP to release

        Returns:
            bool: True if the floating IP is successfully released, False otherwise
        """
        return self.ec2_client.ex_release_address(floating_ip, domain="vpc")

    def _platform_associate_floating_ip(self, floating_ip, instance):
        """
        Associate a floating IP to an instance using the Amazon Web Services API

        Args:
            floating_ip (<floating_ip>): The floating IP to attach
            instance (<instance>): The instance where the floating IP is to be assigned

        Returns:
            bool: True if the floating IP is successfully associated, False otherwise
        """
        return self.ec2_client.ex_associate_address_with_node(instance, floating_ip)

    def _platform_reserve_floating_ip(self):
        """
        Reserve a floating IP using the Amazon Web Services API
        """
        return self.ec2_client.ex_allocate_address()

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
        self.instances = self.ec2_client.list_nodes()
        for instance in self.instances:
            commands_queue.put({"command": "add", "instance_id": instance.id})
        return AWSMonitor(conf=self.conf,
                          commands_queue=commands_queue,
                          measurements_queue=measurements_queue)

    # =============================================================================================== #
    #                               Platform-specific Actions and Menus                               #
    # =============================================================================================== #

    def _get_security_groups_from_instance(self, instance):
        """
        Return the security groups list assigned to an instance

        Args:
            instance (Node): an AWS instance object

        Returns:
            str[]: List of names of security groups associated with the instance
        """
        security_groups = []
        if "groups" in instance.extra:
            for security_group in instance.extra["groups"]:
                security_groups.append(security_group["group_name"])
        return security_groups

    def _get_instance_type_from_instance(self, instance):
        """
        Return the instance type object

        Args:
            instance (Node): an AWS instance object

        Returns:
            NodeSize: an instance type object, None if it can't be determined
        """
        for instance_type in self.ec2_client.list_sizes():
            if instance_type.id == instance.extra["instance_type"]:
                return instance_type
        return None

    def _platform_extra_menu(self):
        """
        Print the extra Functions Menu (specific for each platform)
        """
        while(True):
            menu_header = self.platform_name + " Extra Commands"
            menu_subheader = ["Region: \033[1;94m" +
                              self._platform_get_region() + "\033[0m"]
            menu_items = ["Back to the Main Menu"]
            choice = SimpleTUI.print_menu(menu_header, menu_items, menu_subheader)
            # if choice == 1 and self._is_barebone():  # Blazar menu
            if choice == 1:
                break
            else:
                SimpleTUI.msg_dialog("Error", "Unimplemented functionality", SimpleTUI.DIALOG_ERROR)

    # =============================================================================================== #
    #                                         Override methods                                        #
    # =============================================================================================== #

    override_main_menu = []
    override_ips_menu = []
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
        # if menu == "main" and choice in self.override_main_menu:
        #     if choice == 6 and self._is_barebone():  # Volumes on barebone are not supported
        #         return True
        #     elif choice in [8, 9] and not self._is_barebone():  # Monitor is not available on KVM
        #         return True
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
        # if menu == "main":
        #    if choice == 6:  # Volumes on barebone
        #        return 0
        #    SimpleTUI.error("Unavailable choice!")
        #    SimpleTUI.pause()
        #    SimpleTUI.clear_console()
        pass

    # =============================================================================================== #
    #                                  RuleEngine Actions Definition                                  #
    # =============================================================================================== #

    # All the actions are defined in the actions.py file in the module directory
    # Note: the platform name passed on the decorator must be equal to this class name

    @bind_action("AWS", "clone")
    def clone_instance(self, instance_id):
        """
        Clone instance
        """
        AWSAgentActions.clone_instance(self, instance_id)

    @bind_action("AWS", "alarm")
    def alarm(self, resource_id):
        """
        Trigger an alarm
        """
        AWSAgentActions.alarm(self, resource_id)
