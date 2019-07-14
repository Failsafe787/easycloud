"""
A basic rule engine. It should be replaced with a serious
RE, like durable_rules or others. In the previous release of
CloudTUI (written in Python 2.7), Monfrecola and Gambino
used Mitre's Intellect. Unfortunately, it is not available
for Python 3.
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
import operator
import threading

from queue import Empty


class RuleEngine(threading.Thread):

    def __init__(self, conf, commands_queue, measurements_queue, agent_queue):
        """
        Init method

        Args:
            conf (MetaConfManager): a configuration manager holding all the settings
                                    for the RuleEngine
            commands_queue (Queue): message queue for communicating with the main
                                    thread and receiving commands regarding the rules
            measurements_queue (Queue): message queue for receiving measurements from
                                        the platform monitor
            agent_queue (Queue): message queue used for sending commands to the platform
                                Agent
        """
        self.conf = conf
        self.commands_queue = commands_queue
        self.measurements_queue = measurements_queue
        self.agent_queue = agent_queue
        self.active_rules = []
        # Each instance is stored in this format: {"instance_id": <id>,
        # "rules":["p1","p2",...]}
        self._stop = False

    def run(self):
        """
        RuleEngine Thread Main loop
        """
        # Wait for the init message
        logging.debug("[" + self.__class__.__name__ + "] Waiting for init message...")
        while not self._stop:
            message = None
            # Try message extraction
            while not self._stop:
                try:
                    message = self.commands_queue.get(block=True, timeout=3)
                    self.commands_queue.task_done()
                    break
                except Empty:
                    logging.debug("[" + self.__class__.__name__ + "] No init message received...")
            # Process the message (or ignore it if it's not an init one)
            if message is not None:
                if "command" in message and message["command"] == "init" and "rules" in message:
                    self._process_command(message)
                    logging.debug("[" + self.__class__.__name__ + "] Init message received!")
                    break
        # Normal thread execution
        while not self._stop:
            try:
                # Check any commands received between a message and another
                # (commands have priority)
                while not self.commands_queue.empty():
                    command = self.commands_queue.get()
                    logging.debug("[" + self.__class__.__name__ + "] Message received! " + str(command))
                    self._process_command(command)
                logging.debug("[" + self.__class__.__name__ + "] Checking for new messages...")
                # Fetch a message from the monitor queue (or block the flow
                # until a message is received)
                message = self.measurements_queue.get(timeout=3)
                # Check if an action must be performed
                self._process_message(message)
                logging.debug("Finished reasoning!")
            except Empty:
                logging.debug("[" + self.__class__.__name__ + "] No new messages...")
                pass

    def stop(self):
        """
        Stop the RuleEngine thread
        """
        self._stop = True

    def _process_command(self, message):
        """
        Process a command sent by another thread. Command must be in the form
        {
            "instance_id": string (the instance id)
            "command": string (between "enable_rule", "disable_rule", "add_rule",
                       "remove_rule", "edit_rule")
        }

        Args:
            message (dict): A JSON-Formatted command
        """
        if("command" in message):
            # Init message (load all the rules)
            if message["command"] == "init" and "rules" in message:
                self.rules = message["rules"]
            # Enable a rule
            elif message["command"] == "enable_rule" and "rule_name" in message:
                self._enable_rule(message["rule_name"])
            # Disable a rule
            elif message["command"] == "disable_rule" and "rule_name" in message:
                self._disable_rule(message["rule_name"])
            # Add a rule definition to the rules list
            elif message["command"] == "add_rule" and "rule" in message:
                self._add_rule(message["rule"])
            # Remove a rule definition from the rules list
            elif message["command"] == "remove_rule" and "rule_name" in message:
                self._remove_rule(message["rule_name"])
            # Update a rule definition
            elif message["command"] == "edit_rule" and "rule" in message:
                self._edit_rule(message["rule"])
            # Report an unsupported command
            else:
                logging.warning("[" + self.__class__.__name__ +
                                "] Command not implemented: " + str(message["command"]))
        # Report a bad message
        else:
            logging.error("[" + self.__class__.__name__ +
                          "] Bad command received: " + str(message))

    def _enable_rule(self, rule_name):
        """
        Enable a rule for all the available instances

        Args:
            rule_name (str): the rule name to enable
        """
        if rule_name not in self.active_rules:
            self.active_rules.append(rule_name)
            logging.debug("[" + self.__class__.__name__ + "] Rule Enabled: " + rule_name)
        else:
            logging.warning("[" + self.__class__.__name__ + "] Attempted to add rule " +
                            rule_name + " to the active rules list while already present!")

    def _disable_rule(self, rule_name):
        """
        Disable a rule for all the available instances

        Args:
            rule_name (str): the rule name to disable
        """
        if rule_name in self.active_rules:
            self.active_rules.remove(rule_name)
            logging.debug("[" + self.__class__.__name__ + "] Rule Disabled: " + rule_name)
        else:
            logging.warning("[" + self.__class__.__name__ + "] Attempted to remove rule " +
                            rule_name + " to the active rules list while not present!")

    def _add_rule(self, rule):
        """
        Add a rule definition to the list of rules

        Args:
            rule (dict): the rule definition
        """
        if rule not in self.rules:
            self.rules.append(rule)
            logging.debug("[" + self.__class__.__name__ + "] Rule Created: " + str(rule))
        else:
            logging.warning("[" + self.__class__.__name__ + "] Attempted to add rule " +
                            rule["name"] + " to the rules while a copy of it is already present!")

    def _remove_rule(self, rule_name):
        """
        Remove a rule definition from the list of rules

        Args:
            rule_name (str): the rule name to delete
        """
        found = False
        for rule in self.rules:
            if rule["name"] == rule_name:
                self.rules.remove(rule)
                logging.debug("[" + self.__class__.__name__ + "] Rule Removed: " + rule_name)
                found = True
                break
        if not found:
            logging.warning("[" + self.__class__.__name__ + "] Attempted to remove rule " +
                            rule_name + ", but no rule with that name has been found in the rules list!")

    def _edit_rule(self, edited_rule):
        """
        Replace an existing rule definition with the new one

        Args:
            edited_rule (str): the new rule body
        """
        found = False
        for rule in self.rules:
            if rule["name"] == edited_rule["name"]:
                rule = edited_rule
                logging.debug("[" + self.__class__.__name__ + "] Rule Edited: " + str(rule))
                found = True
                break
        if not found:
            logging.warning("[" + self.__class__.__name__ + "] Attempted to edit rule " +
                            edited_rule["name"] + ", but no rule with that name has been found in the rules list!")

    def _process_message(self, message):
        """
        Process a message received from the Monitor

        Args:
            message (dict): a JSON-Formatted message
        """
        logging.debug("[" + self.__class__.__name__ + "] Processing the message: " + str(message))
        if("instance_id" in message and "measurements" in message):
            logging.debug("[" + self.__class__.__name__ + "] Performing magic stuff...")
            self._reason(instance_id=message["instance_id"], rules_names=self.active_rules,
                         measurements=message["measurements"])
        else:
            logging.error("[" + self.__class__.__name__ +
                          "] Bad message received: " + str(message))

    def _get_rule_definition(self, rule_name):
        for rule_definition in self.rules:
            if rule_definition["name"] == rule_name:
                return rule_definition
        return None

    def _reason(self, instance_id, rules_names, measurements):
        """
        Reason about enabled rules and last measurements and
        take an action if necessary

        Args:
            instance_id (str): The instance id to reason about
            assigned_rules (str[]): A list of enabled rules names in the form
                                    [{'metric': '<metric1_name>', 'values': []},
                                    ...,
                                    {'metric': '<metric2_name>', 'values': []}]
            measurements (dict): A JSON-Formatted struct
        """
        logging.debug("MEASUREMENTS TO BE PROCESSED: " + str(measurements))
        for _rule_name in rules_names:
            rule = self._get_rule_definition(_rule_name)
            try:
                _metric_measurements = None
                for metric_measurement in measurements:
                    if metric_measurement["metric"] == rule["target"]:
                        _metric_measurements = metric_measurement["values"]
                        break
                # Monitor reported that has no getter for the metric required
                # by this rule (in form {"metric":None})
                if(_metric_measurements is None):
                    logging.error(
                        "[" + self.__class__.__name__ + "] The monitor reported that has no getter implemented for this metric: " + rule["target"])
                # Less measurements than expected for a metric
                elif(len(_metric_measurements) < self.conf.window_size):
                    logging.error("[" + self.__class__.__name__ + "] The monitor reported less measurements (" + str(len(
                        _metric_measurements)) + ") than the specified window_size value (" + str(self.conf.window_size) + ").")
                else:  # Operator and expected number of measurements are available
                    self._apply_rule(instance_id=instance_id, rule_name=_rule_name,
                                     metric_measurements=_metric_measurements)
            # Monitor has not provided measurements for a certain metric
            # (something went wrong...)
            except KeyError:
                logging.error("[" + self.__class__.__name__ + "] No measurements regarding metric " +
                              rule["target"] + " have been found")

    def _apply_rule(self, instance_id, rule_name, metric_measurements):
        """
        Apply a rule and send a message to the Agent if required

        Args:
            instance_id (str): The instance id to reason about
            rule_name (str): The rule name
            metric_measurements (dict): A JSON-Formatted struct
        """
        # number of measurements with errors (in form {"timestamp":"<tt>",
        # "error":"<error_message>"})
        _errors = 0
        _satisfied = 0  # number of times this rule has been satisfied

        try:  # Rule initialization
            _rule = self._get_rule_definition(rule_name)  # Get rule definition (a dictionary)
            # Convert operator symbol in function (e.g. ">" -> operator.gt)
            _operation = self._get_operator(operator_symbol=_rule["operator"])
            if(_operation is None):  # Invalid operator
                logging.error("[" + self.__class__.__name__ + "] Invalid operator defined for rule " +
                              _rule["name"] + ": " + _rule["operator"])
            else:
                for _measurement in metric_measurements:  # Check each measurement
                    # Bad measurement (very rare, should not happen due to
                    # temporal series)
                    if("error" in _measurement):
                        logging.error(
                            "[" + self.__class__.__name__ + "] One of the measurements isn't valid: " + _measurement["error"])
                        _errors += 1
                    else:  # Fine measurement, perform rule satisfaction
                        if(_operation(_measurement["value"], _rule["threshold"])):
                            _satisfied += 1
                logging.debug(str(_satisfied) + " measurements are satisfying the " + rule_name + " rule, with a minimum_positive of " + str(self.conf.minimum_positive))
                if(_satisfied >= self.conf.minimum_positive):  # Should I apply the rule?
                    logging.debug("[" + self.__class__.__name__ + "] ACTION!!!!! " + str(_rule["action"]))
                    self._send_action(instance_id=instance_id,
                                      action=_rule["action"])
                    if(_errors > 0):
                        logging.warning("[" + self.__class__.__name__ + "] An action regarding a decision based on measurements with errors was performed!")
        except KeyError:  # rule_name is the name of a rule not defined in the rules list
            logging.error("[" + self.__class__.__name__ + "] No rule named " +
                          rule_name + " has been found in the rules list")

    """
    Convert an operator symbol to a function
    """

    def _get_operator(self, operator_symbol):
        """https://docs.python.org/3/library/operator.html

        Args:
            operator_symbol (str): an operator symbol between
                                   "<", "<=", "==", "!=", ">=", ">"

        Returns:
            function: a function performing the comparison represented by
                      the input symbol, None if an invalid symbol was passed
        """
        _symbol_function_map = {
            "<": operator.lt,
            "<=": operator.le,
            "==": operator.eq,
            "!=": operator.ne,
            ">=": operator.ge,
            ">": operator.gt
        }
        if operator_symbol in _symbol_function_map:
            return _symbol_function_map[operator_symbol]
        else:
            return None

    def _send_action(self, instance_id, action):
        """
        Send a command to the MetaAgent if a rule condition has been met

        Args:
            instance_id (str): The instance id to apply the action
            action (str): The action name
        """
        self.agent_queue.put({"instance_id": instance_id, "action": action})
