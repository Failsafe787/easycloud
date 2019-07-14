"""
Generic monitor, methods decorated with @abstractmethod must be
implemented by a specialized monitor. Currently these methods are:

    connect: connect to the monitoring service and save the client in a variable
             used only by methods of the specific monitor
    _get_metric_values: returns a list of standardized messages (created with
                        method _build_message, defined in this abstract class)

Metrics getters must be implemented in the specialized monitor and binded with the
generic metric name using _bind_generic_metric_to_getter.
"""

import collections
import datetime
import json
import logging
import time

from abc import ABC, abstractmethod
from os import sep

__author__ = "Davide Monfrecola, Stefano Garione, Giorgio Gambino, Luca Banzato"
__copyright__ = "Copyright (C) 2019"
__credits__ = ["Andrea Lombardo", "Irene Lovotti"]
__license__ = "GPL v3"
__version__ = "0.10.0"
__maintainer__ = "Luca Banzato"
__email__ = "20005492@studenti.uniupo.it"
__status__ = "Prototype"


class MetaMonitor(ABC):

    def __init__(self, conf, commands_queue, measurements_queue):
        """
        Init method (object initialization)

        Args:
            conf (MetaConfManager): a configuration manager holding all the settings
                                    for the RuleEngine
            commands_queue (Queue): message queue for communicating with the main
                                    thread and receiving commands regarding the metrics
                                    to observe
            measurements_queue (Queue): message queue for sending measurements to
                                        the platform RuleEngine
        """
        self.conf = conf
        self.commands_queue = commands_queue
        self.measurements_queue = measurements_queue

        # Association between generic metric name and a getter for that metric
        self._metrics_getters = collections.defaultdict(dict)
        self._monitored_instances = []  # List of monitored instances ids
        self._read_metrics_from_file()  # Read metrics from rules/metrics.dct
        self._monitored_metrics = self._set_all_metrics_active()

        # Set monitor enabled
        self._stop = False

        # Connect to the monitoring service
        self.connect()

    @abstractmethod
    def connect(self):
        pass

    def run(self):
        """
        Main monitor loop. Creates messages for RuleEngine in the form
        { "instance_id":string,
          "measurements": [{
              "metric": <metric1_name>,
              "values": [
                   {
                       "timestamp": datetime | None,
                       "value": float | None,
                       "unit": string | None
                   },
                   ...
              ]},
              {
              "metric": <metric2_name>,
              "values": [
                  ...
              ]}
            ]}
        }
        """

        logging.debug("Monitor thread started")

        # Main monitor loop
        while not self._stop:

            # Check commands

            logging.debug("[" + self.__class__.__name__ + "] Checking commands...")
            while not self.commands_queue.empty():
                command = self.commands_queue.get()
                logging.debug("[" + self.__class__.__name__ + "] New command received: " + str(command))
                self._process_command(command)

            # Check instances
            logging.debug("[" + self.__class__.__name__ + "] Checking instances...")
            logging.debug(self._monitored_instances)
            for _instance in self._monitored_instances:
                _metrics_samples = []
                logging.debug("[" + self.__class__.__name__ + "] Check instance {0}".format(_instance))
                for _requested_metric in self._monitored_metrics:
                    _metrics_samples.append(self._get_samples(instance_id=_instance, metric_name=_requested_metric,
                                                              limit=self.conf.window_size, granularity=self.conf.granularity))
                logging.debug("[" + self.__class__.__name__ + "] Sending message: " + str({"instance_id": _instance, "measurements": _metrics_samples}))
                self.measurements_queue.put({"instance_id": _instance, "measurements": _metrics_samples})

            # Put this monitor to sleep (time defined in config file and
            # expressed in seconds)
            logging.debug("[" + self.__class__.__name__ + "] Sleeping for " + str(self.conf.monitor_fetch_period) + " seconds...")
            time.sleep(self.conf.monitor_fetch_period)

    def stop(self):
        """
        Stop this monitor
        """
        self._stop = True

    def _process_command(self, message):
        """
        Process a command sent by another thread. Command must be in the form
        {
            "command":string (currently add|remove)
            "instance_id":string (the instance id)
        }

        Args:
            message (str): The message containing the command to process
        """
        if("command" in message and "instance_id" in message):
            if(message["command"] == "add"):
                self._add_monitored_instance(message["instance_id"])
            elif(message["command"] == "remove"):
                self._remove_monitored_instance(message["instance_id"])
            else:
                logging.warning("[" + self.__class__.__name__ +
                                "] Command not implemented: " + str(message["command"]))
        else:
            logging.error("[" + self.__class__.__name__ +
                          "] Bad command received: " + str(message))

    def _add_monitored_instance(self, instance_id):
        """
        Args:
            instance_id (str): The instance id to add to the monitored instances list
        """
        if(instance_id not in self._monitored_instances):
            self._monitored_instances.append(instance_id)
            logging.debug("[" + self.__class__.__name__ + "] New monitored instance added: " + instance_id)
        else:
            logging.warning("[" + self.__class__.__name__ + "] instance " +
                            instance_id + " is already in the monitored instances list")

    def _remove_monitored_instance(self, instance_id):
        """
        Remove a instance id inside the monitored instances list

        Args:
            instance_id (str): The instance id (intended as instance id) to remove from the
                               monitored instances list
        """
        if(instance_id in self._monitored_instances):
            self._monitored_instances.remove(instance_id)
            logging.debug("[" + self.__class__.__name__ + "] Monitored instance removed: " + instance_id)
        else:
            logging.warning("[" + self.__class__.__name__ + "] Attempted to remove instance " +
                            instance_id + " while it's not in the monitored instances list")

    def _get_samples(self, instance_id, metric_name, limit, granularity):
        """
        Get a number of samples given a instance_id (usually a VM id) and
        a standard metric name.
        A dictionary in the form { <metric_name> : None } is returned if
        the getter function for the provided metric is not implemented by
        the specific monitor

        Args:
            instance_id (str): The instance id (intended as instance id)
            metric_name (str): The *generic* metric name
            limit (int): The maximum number of measurements returned
            granularity (int): The granularity of the measurements fetched, expressed in seconds

        Returns:
            dict: A structure containing all the measurements (max=limit) for a certain metric
        """
        _metric_getter = self._get_metric_getter(generic_metric=metric_name)
        if(_metric_getter is not None):
            _metric_samples = _metric_getter(
                instance_id=instance_id, granularity=granularity, limit=limit)
            logging.debug(
                "Adding " + str(_metric_samples) + " (instance " + instance_id + ", metric " + metric_name + ")")
            return {"metric": metric_name, "values": _metric_samples}
        else:
            return {"metric": metric_name, "values": None}

    def _bind_generic_metric_to_getter(self, name, function):
        """
        Method for registering a metric getter with a generic metric name

        Args:
            name (str): The *generic* name of the metric
            function (function): The fuction that returns the metric measurements
                                 from the platform monitor
        """
        _function = function
        self._metrics_getters[name] = _function

    def _get_metric_getter(self, generic_metric):
        """
        Given the *generic* metric name, return the metric getter function for
        the platform

        Args:
            generic_metric (str): Description

        Returns:
            function: The metric getter function specific for the current platform,
                      None if no getter is assigned to the generic metric
        """
        _value = self._metrics_getters[generic_metric]
        logging.info("METRIC GETTER VALUE for " + generic_metric + ": " + str(_value))
        if(callable(_value)):  # check if the returned value is a function
            return _value
        else:
            return None

    @abstractmethod
    def _get_metric_values(self, instance, metric, granularity, limit):
        pass

    def _build_message(self, timestamp, value, unit):
        """
        Generic message builder, must be used to create messages to be inserted
        in the list returned by the implementation of _get_metric_values

        Args:
            timestamp (str or datetime): Timestamp of the measurement
            value (float): Value of the measurement
            unit (str): The metric measurements unit

        Returns:
            dict: A measurement struct
        """
        return {
            "timestamp": timestamp,
            "value": value,
            "unit": unit
        }

    def _error_sample(self, error):
        """
        Return an error message if something went wrong during a measurement fetch

        Args:
            error (str): the error description

        Returns:
            dict: A measurement struct containing error details
        """
        return {
            "timestamp": datetime.datetime.now(),
            "error": str(type(error)) + " - " + str(error)
        }

    def _read_metrics_from_file(self):
        """
        Read all the *generic* metrics definitions contained in rules/metrics.dct
        """
        logging.debug("Reading metrics...")
        try:
            with open("rules" + sep + "metrics.dct") as file:
                _data = json.load(file)
            if("metrics" in _data):
                self.metrics = _data["metrics"]
                logging.debug("All metrics loaded")
            else:
                logging.error("Bad metrics file format")
        except IOError as e:
            logging.error("An error has occourred while attempting to read metrics definition: " + str(e))

    def _set_all_metrics_active(self):
        """
        Set all the loaded *generic* metrics active

        Returns:
            str[]: A list of active *generic* metrics
        """
        monitored_metrics = []
        if self.metrics is None:
            logging.error("No metrics loaded! There was an error while reading the metrics from source.")
        else:
            for metric in self.metrics:
                if "name" in metric:
                    monitored_metrics.append(metric["name"])
                else:
                    logging.error("Bad metric definition: " + str(metric) + ". Skipped!")
        return monitored_metrics
