"""
EasyCloud Chameleon Cloud Manager
"""

import datetime
import time

from core.actionbinder import bind_action
from core.metamanager import MetaManager
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider
from modules.chameleon_libcloud.actions import ChameleonCloudAgentActions
from modules.chameleon_libcloud.confmanager import ChameleonCloudConfManager
from modules.chameleon_libcloud.monitor import ChameleonCloudMonitor
from tui.simpletui import SimpleTUI

__author__ = "Davide Monfrecola, Stefano Garione, Giorgio Gambino, Luca Banzato"
__copyright__ = "Copyright (C) 2019"
__credits__ = ["Andrea Lombardo", "Irene Lovotti"]
__license__ = "GPL v3"
__version__ = "0.10.0"
__maintainer__ = "Luca Banzato"
__email__ = "20005492@studenti.uniupo.it"
__status__ = "Prototype"


class ChameleonCloud(MetaManager):

    def __init__(self):
        super().__init__()
        self.platform_name = "Chameleon Cloud"
        self.conf = ChameleonCloudConfManager()
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
        cls = get_driver(Provider.OPENSTACK)
        self.os_client = cls(self.conf.os_username, self.conf.os_password,
                             ex_tenant_name=self.conf.os_project_name,
                             ex_force_auth_url=self.conf.os_auth_url,
                             ex_force_service_region=self.conf.os_region,
                             ex_force_auth_version='3.x_password')  # Updated 03/05/19

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
        self.images = self.os_client.list_images()
        i = 1
        table_body = []
        for image in self.images:
            table_body.append([i, image.name, image.id, image.extra["status"]])
            i = i + 1
        return table_body

    def _platform_list_all_availability_zones(self):
        """
        Print all available images
        Format: "ID", "Name", Zone State", "Region Name"
        """
        # Unimplemented, not required
        pass

    def _platform_list_all_instance_types(self):
        """
        Print all instance types
        Format: "ID", "Instance Type ID", "vCPUs", "Ram (GB)", "Disk (GB)"
        """
        self.instance_types = self.os_client.list_sizes()
        i = 1
        table_body = []
        for instance_type in self.instance_types:
            # vCPUs number is not provided in any way, so a n/a is reported instead
            table_body.append([i, instance_type.name, "n/a", instance_type.ram / 1024, instance_type.disk])
            i = i + 1
        return table_body

    def _platform_list_all_security_groups(self):
        """
        Print all security groups
        Format: "ID", "SG name", "SG description"
        """
        self.security_groups = self.os_client.ex_list_security_groups()
        i = 1
        table_body = []
        for security_group in self.security_groups:
            table_body.append([i, security_group.name, security_group.description])
            i = i + 1
        return table_body

    def _platform_list_all_networks(self):
        """
        Print id and other useful informations of all networks available
        Format: "ID", "Network name", "Description"
        """
        self.networks = self.os_client.ex_list_networks()
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
        self.key_pairs = self.os_client.list_key_pairs()
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
        self.instances = self.os_client.list_nodes()
        i = 1
        table_body = []
        for instance in self.instances:
            if len(instance.public_ips) > 0 and None not in instance.public_ips:
                table_body.append([i, instance.name, instance.id, ", ".join(instance.public_ips), instance.state, instance.extra["key_name"], instance.extra["availability_zone"]])
            else:
                table_body.append([i, instance.name, instance.id, "-", instance.state, instance.extra["key_name"], instance.extra["availability_zone"]])
            i = i + 1
        return table_body

    def _platform_list_all_volumes(self):
        """
        Print volumes alongside informations regarding attachments
        Format: "Volume ID", "Creation", "Size (GB)", "Attached To", "Status"
        """
        self.volumes = self.os_client.list_volumes()
        i = 1
        table_body = []
        for volume in self.volumes:
            created_at = datetime.datetime.strptime(volume.extra["created_at"], "%Y-%m-%dT%H:%M:%S.%f").strftime("%b %d %Y, %H:%M:%S") + " UTC"
            if "attachments" in volume.extra and len(volume.extra["attachments"]) > 0:
                node = self.os_client.ex_get_node_details(volume.extra["attachments"][0]["serverId"])
                table_body.append([i, volume.name, volume.id, created_at, volume.size,
                                   node.name + " (" + volume.extra["attachments"][0]["device"] + ")", volume.state, volume.extra["location"]])
            else:
                table_body.append([i, volume.name, volume.id, created_at, volume.size,
                                   "- (-)", volume.state, volume.extra["location"]])
            i = i + 1
        return table_body

    def _platform_list_all_floating_ips(self):
        """
        Print ip and other useful information of all floating ip available
        Format: ""ID", "Public Ip", "Floating IP ID", "Associated Instance"
        """
        self.floating_ips = self.os_client.ex_list_floating_ips()
        i = 1
        table_body = []
        for floating_ip in self.floating_ips:
            if(floating_ip.node_id is not None):
                node = self.os_client.ex_get_node_details(floating_ip.node_id)
                if(node is not None):
                    table_body.append([i, floating_ip.ip_address, floating_ip.id, node.name, "n/a"])
                else:
                    table_body.append([i, floating_ip.ip_address, floating_ip.id, "Load Balancer", "n/a"])
            else:
                table_body.append([i, floating_ip.ip_address, floating_ip.id, "-", "n/a"])
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
        return self.conf.os_region

    def _platform_create_new_instance(self, instance_name, image, instance_type, monitor_cmd_queue=None):
        """
        Create a new instance using the OpenStack API
        Some specific steps are performed here:
            - Ask for security group
            - Ask for key pair
            - Instance creation summary

        Args:
            instance_name (str): The name of the instance
            image (<image_type>): The image to be used as a base system
            instance_type (<instance_type>): The VM flavor
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
        # 7. Reservation id required if using CHI@TACC or CHI@UC (Optional)
        # For details about the fields, please visit
        # https://developer.openstack.org/api-ref/compute/?expanded=create-server-detail
        scheduler_hints = {}
        if (self._is_barebone()):
            reservation_id = SimpleTUI.input_dialog("Blazar reservations",
                                                    question="Insert reservation UUID",
                                                    return_type=str,
                                                    regex="[0-9a-fA-F]{8}\\-[0-9a-fA-F]{4}\\-[0-9a-fA-F]{4}\\-[0-9a-fA-F]{4}\\-[0-9a-fA-F]{12}")
            scheduler_hints["reservation"] = reservation_id

        # Creation summary
        print("\n--- Creating a new instance with the following properties:")
        print("- %-20s %-30s" % ("Name", instance_name))
        print("- %-20s %-30s" % ("Image", image.name))
        print("- %-20s %-30s" % ("Instance Type", instance_type.name))
        print("- %-20s %-30s" % ("Key Pair", key_pair.name))
        print("- %-20s %-30s" % ("Security Group", security_group.name))
        if (self._is_barebone()):
            print("- %-20s %-30s" % ("Reservation", reservation_id))

        # ask for confirm
        print("")
        if(SimpleTUI.user_yn("Are you sure?")):
            instance = self.os_client.create_node(name=instance_name,
                                                  image=image,
                                                  size=instance_type,
                                                  ex_keyname=key_pair.name,
                                                  ex_security_groups=[security_group],
                                                  ex_scheduler_hints=scheduler_hints)
            if instance is None:
                return False
            if monitor_cmd_queue is not None and self.is_monitor_running():
                monitor_cmd_queue.put({"command": "add", "instance_id": instance.id})
            return True

    def _platform_instance_action(self, instance, action):
        """
        Handle an instance action with Openstack API
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
        for instance in self.os_client.list_nodes():
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
        if(len(volume.extra["attachments"]) == 0):
            return False
        elif(volume.extra["attachments"][0]["serverId"] is None):
            return False
        return True

    def _platform_detach_volume(self, volume):
        """
        Detach a volume using the OpenStack API

        Args:
            volume (<volume>): The volume to detach

        Returns:
            bool: True if the volume is successfully detached, False otherwise
        """
        result = self.os_client.detach_volume(volume)
        if(result):
            while True:
                updated_volume = self.os_client.ex_get_volume(volume.id)
                if not self._platform_is_volume_attached(updated_volume):
                    break
                time.sleep(3)
        return result

    def _platform_delete_volume(self, volume):
        """
        Delete a volume using the OpenStack API

        Args:
            volume (<volume>): The volume to delete

        Returns:
            bool: True if the volume is successfully deleted, False otherwise
        """
        return self.os_client.destroy_volume(volume)

    def _platform_attach_volume(self, volume, instance):
        """
        Attach a volume using the OpenStack API
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
        return self.os_client.attach_volume(instance, volume, exposure_point)

    def _platform_create_volume(self, volume_name, volume_size):
        """
        Create a new volume using the OpenStack API

        Args:
            volume_name (str): Volume name
            volume_size (int): Volume size in GB

        Returns:
            bool: True if the volume is successfully created, False otherwise
        """
        return self.os_client.create_volume(name=volume_name, size=volume_size)

    def _platform_is_ip_assigned(self, floating_ip):
        """
        Check if a floating IP is assigned to an instance

        Args:
            floating_ip (<floating_ip>): The floating IP to check

        Returns:
            bool: True if the floating IP is assigned, False otherwise
        """
        if(floating_ip.node_id is not None):
            return True
        return False

    def _platform_detach_floating_ip(self, floating_ip):
        """
        Detach a floating IP using the OpenStack API

        Args:
            floating_ip (<floating_ip>): The floating IP to detach

        Returns:
            bool: True if the floating IP is successfully detached, False otherwise
        """
        node = self.os_client.ex_get_node_details(floating_ip.node_id)
        result = self.os_client.ex_detach_floating_ip_from_node(node, floating_ip)
        if(result):
            while True:
                updated_floating_ip = self.os_client.ex_get_floating_ip(floating_ip.ip_address)
                if not self._platform_is_ip_assigned(updated_floating_ip):
                    break
                time.sleep(3)
        return result

    def _platform_release_floating_ip(self, floating_ip):
        """
        Release a floating IP using the OpenStack API

        Args:
            floating_ip (<floating_ip>): The floating IP to release

        Returns:
            bool: True if the floating IP is successfully released, False otherwise
        """
        return self.os_client.ex_delete_floating_ip(floating_ip)

    def _platform_associate_floating_ip(self, floating_ip, instance):
        """
        Associate a floating IP to an instance using the OpenStack API

        Args:
            floating_ip (<floating_ip>): The floating IP to attach
            instance (<instance>): The instance where the floating IP is to be assigned

        Returns:
            bool: True if the floating IP is successfully associated, False otherwise
        """
        return self.os_client.ex_attach_floating_ip_to_node(instance, floating_ip)

    def _platform_reserve_floating_ip(self):
        """
        Reserve a floating IP using the OpenStack API
        """
        # public - CHI@TACC and CHI@UC
        # ext-net - OpenStack@TACC
        return self.os_client.ex_create_floating_ip(ip_pool="public" if self._is_barebone() else "ext-net")

    # =============================================================================================== #
    #                               Platform-specific Actions and Menus                               #
    # =============================================================================================== #

    def _is_barebone(self):
        """
        Detect if the selected region is using barebone instances or KVM
        """
        if self.conf.os_region in ["CHI@TACC", "CHI@UC"]:
            return True
        return False

    def _platform_extra_menu(self):
        """
        Print the extra Functions Menu (specific for each platform)
        """
        while(True):
            menu_header = self.platform_name + " Extra Commands"
            menu_subheader = ["Region: \033[1;94m" +
                              self._platform_get_region() + "\033[0m"]
            menu_items = ["Handle reservations (Not available in this release)" if self._is_barebone()
                          else "Handle reservations (Not available on KVM)",
                          "Back to the Main Menu"]
            choice = SimpleTUI.print_menu(menu_header, menu_items, menu_subheader)
            # if choice == 1 and self._is_barebone():  # Blazar menu
            if choice == 1:
                if self._is_barebone():
                    SimpleTUI.msg_dialog("Error", "Unimplemented functionality", SimpleTUI.DIALOG_ERROR)
                else:
                    SimpleTUI.msg_dialog("Reservations Manager", "Reservation manager is not available on OpenStack@TACC.\n" +
                                         "Please use one of the following regions:\n\n" +
                                         "- CHI@TACC (https://chi.tacc.chameleoncloud.org)\n" +
                                         "- CHI@UC (https://chi.uc.chameleoncloud.org)", SimpleTUI.DIALOG_INFO)
            # self.manage_reservations()
            elif choice == 2:  # Back to the main menu
                break
            else:
                SimpleTUI.msg_dialog("Error", "Unimplemented functionality", SimpleTUI.DIALOG_ERROR)

    # =============================================================================================== #
    #                                         Override methods                                        #
    # =============================================================================================== #

    override_main_menu = [6, 8, 9]
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
        if menu == "main" and choice in self.override_main_menu:
            if choice == 6 and self._is_barebone():  # Volumes on barebone are not supported
                return True
            elif choice in [8, 9] and not self._is_barebone():  # Monitor is not available on KVM
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
        if menu == "main":
            if choice == 6:  # Volumes on barebone
                SimpleTUI.msg_dialog("Volumes Handler", "CHI@TACC and CHI@UC don't support volumes.\n" +
                                     "Please use KVM (https://openstack.tacc.chameleoncloud.org)", SimpleTUI.DIALOG_INFO)
                return 0
            elif choice in [8, 9]:  # Monitor on KVM
                SimpleTUI.msg_dialog("Monitoring", "Monitoring and Rule Management features are not available on OpenStack@TACC.\n" +
                                     "Please use one of the following regions:\n\n" +
                                     "- CHI@TACC (https://chi.tacc.chameleoncloud.org)\n" +
                                     "- CHI@UC (https://chi.uc.chameleoncloud.org)", SimpleTUI.DIALOG_INFO)
                return 0
            SimpleTUI.error("Unavailable choice!")
            SimpleTUI.pause()
            SimpleTUI.clear_console()

    # =============================================================================================== #
    #                                         Monitor creation                                        #
    # =============================================================================================== #

    def _platform_get_monitor(self, commands_queue, measurements_queue):
        """
        Create the Chameleon Cloud Resources Monitor using Gnocchi APIs

        Args:
            commands_queue (Queue): message queue for communicating with the main
                                    thread and receiving commands regarding the metrics
                                    to observe
            measurements_queue (Queue): message queue for sending measurements to
                                        the platform RuleEngine

        Returns:
            MetaMonitor: the platform-specific monitor
        """
        self.instances = self.os_client.list_nodes()
        for instance in self.instances:
            print("Adding instance to monitor init: " + str({"command": "add", "instance_id": instance.id}))
            commands_queue.put({"command": "add", "instance_id": instance.id})
        return ChameleonCloudMonitor(conf=self.conf,
                                     commands_queue=commands_queue,
                                     measurements_queue=measurements_queue)

    # =============================================================================================== #
    #                                  RuleEngine Actions Definition                                  #
    # =============================================================================================== #

    # All the actions are defined in the actions.py file in the module directory
    # Note: the platform name passed on the decorator must be equal to this class name

    @bind_action("ChameleonCloud", "clone")
    def clone_instance(self, instance_id):
        """
        Clone instance
        """
        ChameleonCloudAgentActions.clone_instance(self, instance_id)

    @bind_action("ChameleonCloud", "alarm")
    def alarm(self, instance_id):
        """
        Trigger an alarm
        """
        ChameleonCloudAgentActions.alarm(self, instance_id)
