"""
Minimal Text User Interface implementation for
EasyCloud
"""

import os
import re
import traceback

from texttable import Texttable

__author__ = "Davide Monfrecola, Stefano Garione, Giorgio Gambino, Luca Banzato"
__copyright__ = "Copyright (C) 2019"
__credits__ = ["Andrea Lombardo", "Irene Lovotti"]
__license__ = "GPL v3"
__version__ = "0.10.0"
__maintainer__ = "Luca Banzato"
__email__ = "20005492@studenti.uniupo.it"
__status__ = "Prototype"


class SimpleTUI:

    def user_input(type, question=None, regex=None):
        """
        Prompt an input request to the user. Input will then be parsed
        as the type passed as argument to this method.
        If the input object is empty or in the wrong format (e.g. a
        string for a number), a new request will be prompted.

        Args:
            type (<type>): the type of data to be returned
            question (str, optional): the question the user has to answer
            regex (str, optional): check if the provided answer is in a specific format

        Returns:
            <type>: user input of type <type>
        """
        if(question is not None):
            print(question)

        while(True):
            try:
                _raw_input = input("> ")
                if _raw_input in ["exit", "quit", "stop"]:
                    return None
                if len(_raw_input) == 0:
                    SimpleTUI.warning("No answer provided, please retype your choice!")
                elif regex is not None and not re.search(regex, _raw_input):
                    SimpleTUI.error("Invalid input, please retype your choice!")
                elif type is None:
                    return _raw_input
                else:
                    return type(_raw_input)
            except Exception:
                SimpleTUI.error("Invalid input, please retype your choice!")

    def user_yn(question=None, warning=False):
        """
        Prompt a yes/no request to the user

        Args:
            question (str, optional): the question to ask the user for an item
            warning (bool, optional): highlight the message

        Returns:
            bool: user answer (True if yes, False if no)
        """
        yes = set(['yes', 'y'])
        no = set(['no', 'n'])

        if(question is not None):
            if warning:
                SimpleTUI.warning(question + " (Yes/No)")
            else:
                SimpleTUI.info(question + " (Yes/No)")
        else:
            SimpleTUI.info("(Yes/No)")

        while(True):
            _user_input = input("> ")
            if _user_input.isalpha():
                if _user_input in yes:
                    return True
                elif _user_input in no:
                    return False
                else:
                    SimpleTUI.error("Invalid input, please retype your choice!")
            else:
                SimpleTUI.error("Invalid input, please retype your choice!")

    def clear_console():
        """
        Clear the console issuing the follow commands to the interpreter:
        * "cls" on Microsoft(R) Windows environment
        * "clear" on Unix-like systems
        """
        os.system("cls" if os.name == "nt" else "clear")

    def set_console_title(title):
        """
        Set the console title

        Args:
            title (str): Set the current console title
        """
        print("\x1b]2;" + title + "\x07")

    def resize_console(rows, columns):
        """
        Resize the current terminal emulator.
        Note: this may not work with all the terminal emulators.

        Args:
            rows (int): new number of rows of the terminal
            columns (int): new number of columns of the terminal
        """
        if os.name == "nt":
            # Untested
            os.system("mode con: cols=" + str(columns) + " lines=" + str(rows))
        else:
            # Terminal escape sequence for resizing the current window
            # Working under macOS / GNU/Linux, only if supported by the terminal emulator
            # Xfce4 terminal: Yes, Deepin Terminal: No
            print("\x1b[8;" + str(rows) + ";" + str(columns) + "t")

    def pause():
        """
        Pause the execution of a python script until the user doesn't press
        a key
        """
        input("Press a key to continue...")

    def print_table(header, body):
        """
        Print a table using Texttable

        Args:
            header (list of str): Table header (one element per column)
            body (list of list of str): Table body (list of rows, which are
                                        lists of strings))
        """
        table = Texttable(150)  # Width
        table.set_deco(0)  # No borders
        table.set_cols_dtype(['t'] * len(header))  # Data type (all strings)
        table.set_cols_align(["l"] * len(header))  # Left alignment
        table.add_rows([header] + body)
        print(table.draw())

    def print_menu(header, menu_items, subheader_items=None, custom_question=None):
        """
        Print a menu

        Args:
            header (str): the header of the menu
            menu_items (list of str): menu items
            subheader_items (list of str, optional): text to be displayed between
                                                     the header and menu items
            custom_question (str, optional): a custom question to replace the
                                             standard one

        Returns:
            int: a menu index selected by the user
        """
        SimpleTUI.clear_console()
        menu = "\n" + str(header) + "\n\n"
        if (subheader_items is not None and len(subheader_items) > 0):
            for subheader_item in subheader_items:
                menu += str(subheader_item) + "\n"
            menu += "\n"
        if custom_question is None:
            menu += "\nWhat would you like to do?\n"
        else:
            menu += "\n" + custom_question + "\n"
        menu += "--------------------------\n"
        i = 1
        for item in menu_items:
            menu += str(i) + ") " + str(item) + "\n"
            i = i + 1
        print(menu)
        value = None
        while True:
            value = SimpleTUI.user_input(int, "Please make a choice: ")
            if value is not None and value >= 1 and value <= len(menu_items):
                break
            else:
                SimpleTUI.error("Invalid choice!")
        SimpleTUI.clear_console()
        return value

    def input_dialog(header, question=None, return_type=None, regex=None, pause_on_exit=False, ask_for_quit=True, cannot_quit=False):
        """
        Display an input dialog

        Args:
            header (str): the header of this dialog
            question (str, optional): the question to ask the user for an item
            return_type (<type>, optional): the type of data to be returned
            regex (str, optional): a regular expression the input must follow
            pause_on_exit (bool, optional): ask for pressing a key before closing
                                            this dialog (default = True)
            ask_for_quit (bool, optional): ask for user confirmation if an exit
                                           command is issued (default = True)
            cannot_quit (bool, optional): block any attempt to close this dialog
                                          (default = False)

        Returns:
            <type>: user input of type <type>
        """
        return_value = None
        SimpleTUI.clear_console()
        print("\n--- " + header + " ---\n")
        while(True):
            input_data = SimpleTUI.user_input(return_type, question + ": ", regex)
            # User wants to exit
            if input_data is None:
                if cannot_quit:
                    SimpleTUI.error("Cannot close this section. Please, provide a valid input!")
                elif not ask_for_quit or (ask_for_quit and SimpleTUI.user_yn("Are you sure you want to quit?")):
                    break
            # Normal value request (e.g. insert instance name)
            else:
                return_value = input_data
                break
        return return_value

    def yn_dialog(header, question, warning=False):
        """
        Display a Yes/No dialog

        Args:
            header (str): the header of this dialog
            question (str): the question to ask the user

        Returns:
            bool: user answer (True if yes, False if no)
        """
        SimpleTUI.clear_console()
        print("\n--- " + header + " ---\n")
        result = SimpleTUI.user_yn(question, warning=warning)
        SimpleTUI.clear_console()
        return result

    def list_dialog(header, list_printer, question=None, pause_on_exit=False, ask_for_quit=True):
        """
        Print a list dialog

        Args:
            header (str): the header of this dialog
            question (str, optional): the question to ask the user for an item
            list_printer (function): a function which prints a table and returns
                                     the number of items printed
            pause_on_exit (bool, optional): ask for pressing a key before closing
                                            this dialog only if no question is passed
                                            (default = False)
            ask_for_quit (bool, optional): ask for user confirmation if an exit
                                           command is issued (default = True)

        Returns:
            int: The index of the item selected (starting from 1)

        Raises:
            ValueError: if list_printer is not a function
        """
        if not callable(list_printer):
            raise ValueError("list_printer must be a function!")
        return_value = None
        items_number = 0
        SimpleTUI.clear_console()
        print("\n--- " + header + " ---\n")
        try:
            items_number = list_printer()
        except Exception as e:
            SimpleTUI.exception_dialog(e, pause_on_exit=False, clear_on_exit=False)
        print("")
        # Ask for user input only if it is required and there're elements
        if items_number > 0 and question is not None:
            while(True):
                input_data = SimpleTUI.user_input(int, question + ": ")
                # User wants to exit
                if input_data is None:
                    if not ask_for_quit or (ask_for_quit and SimpleTUI.user_yn("Are you sure you want to quit?")):
                        break
                # Check if this is an ID selector
                elif input_data >= 1 and input_data <= items_number:
                    return_value = input_data
                    break
                else:
                    SimpleTUI.error("Unavailable choice!")
        # Pause if specified or no elements were provided by the list
        if pause_on_exit or question is None or (items_number == 0 and question is not None):
            SimpleTUI.pause()
        SimpleTUI.clear_console()
        return return_value

    def msg_dialog(header, message, msg_type, pause_on_exit=True, clear_on_exit=True):
        """
        Display a message

        Args:
            header (str): the header of this dialog
            message (str): the message to display
            msg_type (str): a message type between "DIALOG_INFO", "DIALOG_SUCCESS",
                            "DIALOG_WARNING", "DIALOG_ERROR"
            pause_on_exit (bool, optional): ask for pressing a key before closing
                                            this dialog (default = True)
            clear_on_exit (bool, optional): clear the terminal on exit (default = True)

        Raises:
            ValueError: if msg_type is not one of the group listed above
        """
        SimpleTUI.clear_console()
        print("\n--- " + header + " ---\n")
        if msg_type == 0:
            SimpleTUI.info(message)
        elif msg_type == 1:
            SimpleTUI.success("\N{HEAVY CHECK MARK} " + message)
        elif msg_type == 2:
            SimpleTUI.warning("\N{EXCLAMATION MARK} " + message)
        elif msg_type == 3:
            SimpleTUI.error("\N{CROSS MARK} " + message)
        else:
            raise ValueError("Invalid msg_type!")
        if(pause_on_exit):
            print("")  # Leave an empty space
            SimpleTUI.pause()
        if(clear_on_exit):
            SimpleTUI.clear_console()

    def exception_dialog(exception, pause_on_exit=True, clear_on_exit=True):
        """
        Display an error dialog

        Args:
            exception (Exception): an exception to be printed
                                   alongside the error message
            pause_on_exit (bool, optional): ask for pressing a key before closing
                                            this dialog (default = True)
            clear_on_exit (bool, optional): clear the terminal on exit (default = True)
        """
        trace = traceback.format_exc()
        SimpleTUI.msg_dialog("Error", "A network or program error has occourred!\n" +
                             "\nERROR:\n" + str(exception) + "\n\n" +
                             "- If the error is related to a server or network problem, please try again\n" +
                             "  in a few minutes and check the platform status page/forum/mailing list\n" +
                             "  to understand if the service is under mainteinance or encountering problems.\n" +
                             "- If there was an authentication error, please check the correctness of the credentials.\n" +
                             "- If this problem persists or there was an internal program error, please open a new support\n" +
                             "  ticket on the EasyCloud Git page, reporting the whole message (error and traceback),\n" +
                             "  alongside all the steps performed before, in order to help us identifiying and reproducing\n" +
                             "  the issue.\n\n" +
                             "TRACEBACK:\n" + str(trace),
                             SimpleTUI.DIALOG_ERROR, pause_on_exit=pause_on_exit, clear_on_exit=clear_on_exit)

    # Nominal values for dialog type (used in msg_dialog)
    DIALOG_INFO = 0
    DIALOG_SUCCESS = 1
    DIALOG_WARNING = 2
    DIALOG_ERROR = 3

    def info(message):
        """
        Print an information message

        Args:
            message (str): a message
        """
        print("\033[1m" + message + "\033[0m")  # Bold

    def success(message):
        """
        Print a success message

        Args:
            message (str): a message
        """
        print("\033[1;32m" + message + "\033[0m")  # Green Bold

    def warning(message):
        """
        Print a warning message

        Args:
            message (str): a message
        """
        print("\033[1;33m" + message + "\033[0m")  # Yellow Bold

    def error(message):
        """
        Print an error message

        Args:
            message (str): a message
        """
        print("\033[1;31m" + message + "\033[0m")  # Red Bold

    def active(string):
        """
        Return a colored text (Green)

        Args:
            string (str): a string to format

        Returns:
            str: a formatted string
        """
        return "\033[1;32m" + string + "\033[0m"

    def inactive(string):
        """
        Return a colored text (White)

        Args:
            string (str): a string to format

        Returns:
            str: a formatted string
        """
        return "\033[1m" + string + "\033[0m"
