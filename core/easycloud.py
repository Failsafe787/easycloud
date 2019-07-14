"""
EasyCloud main script
"""

import logging
import modules
import subprocess
import sys

from core.module import Module
from os import environ, sep
from pkgutil import iter_modules
from tui.simpletui import SimpleTUI


__author__ = "Davide Monfrecola, Stefano Garione, Giorgio Gambino, Luca Banzato"
__copyright__ = "Copyright (C) 2019"
__credits__ = ["Andrea Lombardo", "Irene Lovotti"]
__license__ = "GPL v3"
__version__ = "0.10.0"
__maintainer__ = "Luca Banzato"
__email__ = "20005492@studenti.uniupo.it"
__status__ = "Prototype"


class EasyCloud:

    loaded_modules = []
    loaded_instances = []

    def start(self, no_libs_check=False):
        """
        Main application loop
        """
        # Resize the console window
        SimpleTUI.resize_console(30, 120)
        # Load all the modules
        self.load_all_modules(no_libs_check=no_libs_check)
        # Loop
        exit = False
        while(not exit):
            SimpleTUI.set_console_title("EasyCloud")
            platform = self.menu()
            manager = self.get_instance(platform.manager_class)
            try:
                close = False
                while(not close):
                    action = manager.menu()
                    # if action == 0:  # Ignore this value
                    #     pass
                    if action == 1:  # Close current manager menu
                        close = True
                    elif action == 2:  # Close this application
                        close = True
                        exit = True
            except Exception as e:
                SimpleTUI.exception_dialog(e)
        self.close(0)

    def menu(self):
        """
        Prints the modules menu
        """
        global kill

        while True:
            # Header creation
            menu_header = "******************** EasyCloud ********************"
            # Subheader creation
            disclaimer = "\033[34;1mThis is a proof-of-concept build, not suitable\nfor production use.\033[0m\n"
            debug_status = None
            hffr_status = None
            if "LIBCLOUD_DEBUG" in environ:
                debug_status = "\033[93mLibcloud Debug Mode ON\033[0m"
            else:
                debug_status = "\033[90mLibcloud Debug Mode OFF\033[0m"
            if "LIBCLOUD_DEBUG_PRETTY_PRINT_RESPONSE" in environ and environ["LIBCLOUD_DEBUG_PRETTY_PRINT_RESPONSE"] == "1":
                hffr_status = "\033[93mLibcloud Human friendly formatted response ON\033[0m"
            else:
                hffr_status = "\033[90mLibcloud Human friendly formatted response OFF\033[0m"
            menu_subheader = [disclaimer, debug_status, hffr_status]
            # Menu items creation
            menu_items = []
            for module in self.loaded_modules:
                menu_items.append(module.platform_name)
            menu_items.append("Close application")
            # Menu print
            choice = SimpleTUI.print_menu(menu_header, menu_items,
                                          subheader_items=menu_subheader,
                                          custom_question="Select a platform")
            try:
                if(choice >= 1 and choice <= len(self.loaded_modules)):
                    return self.loaded_modules[choice - 1]  # Load a module
                elif(choice == len(self.loaded_modules) + 1):  # Close application
                    self.close(0)
                else:
                    SimpleTUI.msg_dialog("Error", "Unimplemented functionality", SimpleTUI.DIALOG_ERROR)
            except Exception as e:
                SimpleTUI.exception_dialog(e)

    def close(self, code):
        """
        Close the application

        Args:
            code (int): an exit code (0 for normal termination)
        """
        SimpleTUI.clear_console()
        exit(code)

    def get_instance(self, manager_class):
        """
        Returns an existing instance of the manager_class provided in input
        if previously instantiated or creates a new instance.

        Args:
            manager_class (<manager_class>): class of the module manager

        Returns:
            <manager_class_instance>: an instance of <manager_class>
        """
        for _instance in self.loaded_instances:
            if isinstance(_instance, manager_class):
                return _instance
        try:
            _new_instance = manager_class()
            self.loaded_instances.append(_new_instance)
            return _new_instance
        except Exception as e:
            SimpleTUI.exception_dialog(e)
            return None

    def load_all_modules(self, no_libs_check):
        """
        Loads all the Modules from the modules folder
        """
        _all_modules = list(iter_modules(modules.__path__))
        for _module in _all_modules:
            module_object = Module(_module[1])
            try:
                if no_libs_check or self.check_dependencies(module_object):
                    module_object.load_manager_class()
                    self.loaded_modules.append(module_object)
            except ImportError as e:
                SimpleTUI.msg_dialog("Missing packages", "There was an error while importing a package for the\n" +
                                     module_object.platform_name + " module: \n\n" + str(e) + "\n\n" +
                                     "This module won't be loaded.", SimpleTUI.DIALOG_ERROR)

    def check_dependencies(self, module):
        """
        Check if all the dependencies (pip packages) are satisfied for
        a certain module, and can install them if the user approves

        Args:
            module (Module): a module object (no manager class must be loaded
                             through load_manager_class method of this object)

        Returns:
            bool: the result of the check
        """
        required_packages = getattr(module, "dependencies")
        installed_packages = subprocess.check_output(['pip3', 'list', '--format=json'], stderr=subprocess.STDOUT).decode()
        missing_packages_names = []  # package names displayed to the user
        missing_packages_commands = []  # packages names/urls passed to pip3
        for required_package in required_packages:
            # Format: pip-package-name:package-url|package-git (the latter is optional)
            #
            # Symbolic: pip package name (the one you see with "pip3 list")
            # Package URL (optional): package url from where pip3 will download the library
            # Package Git (optional): package git url in the form git+git://github.com/my_user/my_project.git(@branch)
            #
            # e.g. libcloud:apache-libcloud
            required_package_data = required_package.split(":", 1)
            if required_package_data[0] not in installed_packages:
                missing_packages_names.append(required_package_data[0])
                if len(required_package_data) == 2:
                    missing_packages_commands.append(required_package_data[1])
                else:
                    missing_packages_commands.append(required_package_data[0])
        if len(missing_packages_names) > 0:
            packages_list = ""
            for missing_package_name in missing_packages_names:
                packages_list += "- " + missing_package_name + "\n"
            choice = SimpleTUI.yn_dialog("Missing packages", "The following packages are required by the " + module.platform_name + " module:\n" +
                                         "\n" + packages_list + "\nIf these packages are not installed, this module won't be loaded.\n" +
                                         "Do you want to install them through pip?", warning=True)
            if choice:
                SimpleTUI.msg_dialog("Library installer", "Installing the required libraries, this can take a bit...",
                                     SimpleTUI.DIALOG_INFO, pause_on_exit=False, clear_on_exit=False)
                if self.install_libraries(missing_packages_commands):
                    SimpleTUI.msg_dialog("Library installer", "All the packages for " + module.platform_name + "\n" +
                                         "were successfully installed!\n\n" + packages_list, SimpleTUI.DIALOG_SUCCESS)
                    return True
                else:
                    SimpleTUI.msg_dialog("Library installer", "There was an error while installing the missing packages\n" +
                                         "for " + module.platform_name + ".\n"
                                         "Please check logs" + sep + "installer.log in the main directory for details.", SimpleTUI.DIALOG_ERROR)
                    return False
            return False
        return True

    def install_libraries(self, pip_libs):
        """
        Install the provided libraries using pip3 and save a log
        file inside logs directory

        Args:
            pip_libs (str[]): a list of names of pip packages

        Returns:
            bool: the installation result
        """
        subproc = subprocess.Popen([sys.executable, "-m", "pip", "install", "--user"] + pip_libs, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        try:
            logfile = open("logs" + sep + "libs_installer.log", "a+")  # open log in append mode
            for line in subproc.stdout:
                # write the subprocess stdout to the log file
                logfile.write(line.decode(sys.stdout.encoding))
            logfile.close()
        except IOError as e:
            logging.error("IO Error while trying to write data on logs" + sep + "libs_installer.log: " + str(e))
        subproc.wait()
        if subproc.returncode:  # raise an exception if the installation encountered a problem
            return False
        return True
