"""
Chameleon Cloud monitor implementation (using Gnocchi API)
"""

import datetime
import logging
import pytz

from core.metamonitor import MetaMonitor
from gnocchiclient.v1 import client
from keystoneauth1 import loading
from tzlocal import get_localzone

__author__ = "Davide Monfrecola, Stefano Garione, Giorgio Gambino, Luca Banzato"
__copyright__ = "Copyright (C) 2019"
__credits__ = ["Andrea Lombardo", "Irene Lovotti"]
__license__ = "GPL v3"
__version__ = "0.10.0"
__maintainer__ = "Luca Banzato"
__email__ = "20005492@studenti.uniupo.it"
__status__ = "Prototype"


class ChameleonCloudMonitor(MetaMonitor):

    def __init__(self, conf, commands_queue, measurements_queue):
        """
        Init method

        Args:
            conf (MetaConfManager): a configuration manager holding all the settings
                                    for the Monitor
            commands_queue (Queue): message queue for communicating with the main
                                    thread and receiving commands regarding the metrics
                                    to observe
            measurements_queue (Queue): message queue for sending measurements to
                                        the platform RuleEngine
        """
        super().__init__(conf, commands_queue, measurements_queue)
        self._bind_generic_metric_to_getter(
            name="cpu_load", function=self._get_cpu_measures)
        self._bind_generic_metric_to_getter(
            name="memory_free", function=self._get_memory_free_measures)
        self._bind_generic_metric_to_getter(
            name="memory_used", function=self._get_memory_used_measures)
        logging.debug("[CHAMELEON CLOUD MONITOR GETTERS]: " + str(self._metrics_getters))

    def connect(self):
        """
        Connect to Gnocchi and initialize its client object
        """
        _loader = loading.get_plugin_loader('password')
        _auth = _loader.load_from_options(auth_url=self.conf.os_auth_url,
                                          username=self.conf.os_username,
                                          password=self.conf.os_password,
                                          project_id=self.conf.os_project_id,
                                          user_domain_name="default")
        self.gnocchi_client = client.Client(adapter_options={
                                            "region_name": self.conf.os_region}, session_options={"auth": _auth})

    def _get_metric_values(self, instance_id, metric, granularity, limit):
        """
        Gnocchi measurements getter. Conversion to generic metric name is performed here through _build_message.

        Args:
            instance_id (str): The id of the instance to fetch the measurements
            metric (str): The *specific* metric name to get the values
            granularity (int): The granularity of the measurements fetched, expressed in seconds
            limit (int): The maximum number of measurements returned

        Returns:
            dict: A structure containing all the measurements for a metric
        """
        logging.debug("Fetching metric \"" + metric + "\" with granularity=" + str(granularity) + " and limit=" + str(limit))
        # Define time interval for retrieving metrics
        start_time_local = datetime.datetime.now() - datetime.timedelta(seconds=(granularity * limit) + granularity * 2)
        end_time_local = datetime.datetime.now()
        local_tz = get_localzone()  # Detect current timezone
        # Convert local time to UTC
        start_time_no_tz = local_tz.localize(
            start_time_local, is_dst=None)  # No daylight saving time
        end_time_no_tz = local_tz.localize(
            end_time_local, is_dst=None)  # No daylight saving time
        # Final times
        start_time_utc = start_time_no_tz.astimezone(pytz.utc)
        end_time_utc = end_time_no_tz.astimezone(pytz.utc)

        _samples = []

        try:
            instance_resources = self.gnocchi_client.resource.get("generic", instance_id)
            logging.debug("Instance ID: " + str(instance_id))
            # logging.debug("FETCHING METRIC " + metric + ": " + str(instance_resources))
            _random_measurements_values = self.gnocchi_client.metric.get_measures(
                instance_resources["metrics"][metric], start=start_time_utc, end=end_time_utc, granularity=granularity)
            # Sort all the data (sometimes data can be unrodered)
            _random_measurements_values.sort(key=lambda x: x[0])
            # Extract the most recent limit-values
            _measurements_values = _random_measurements_values[-limit:]
            _metric_unit = self.gnocchi_client.metric.get(
                instance_resources["metrics"][metric])["unit"]
            # Add the measurements to the list that will be returned
            for _value in _measurements_values:
                _samples.append(self._build_message(timestamp=_value[0],
                                                    value=_value[2],
                                                    unit=_metric_unit))
            logging.debug("MEASUREMENTS: " + str(_samples))
        except Exception as _exception:
            _samples.append(self._error_sample(_exception))
            logging.error("There was an error while fetching measurements:\n" +
                          str(type(_exception)) + " -  " + str(_exception) +
                          ". Please note that this is normal if you recently created a new instance.")

        return _samples

    # For the complete metrics list available for each instance, please use the
    # res_viewer.py script available in the module main directory, after
    # filling all the required authentication parameters

    def _get_cpu_measures(self, instance_id, granularity, limit):
        """
        CPU Load getter

        Args:
            instance_id (str): The id of the instance to fetch the measurements
            granularity (int): The granularity of the measurements fetched, expressed in seconds
            limit (int): The maximum number of measurements returned

        Returns:
            dict: A structure containing all the measurements regarding CPU Load
        """
        return self._get_metric_values(instance_id=instance_id,
                                       metric="load@load",
                                       granularity=granularity,
                                       limit=limit)

    def _get_memory_free_measures(self, instance_id, granularity, limit):
        """
        Memory free getter

        Args:
            instance_id (str): The id of the instance to fetch the measurements
            granularity (int): The granularity of the measurements fetched, expressed in seconds
            limit (int): The maximum number of measurements returned

        Returns:
            dict: A structure containing all the measurements regarding Memory Free
        """
        return self._get_metric_values(instance_id=instance_id,
                                       metric="memory@memory.free",
                                       granularity=granularity,
                                       limit=limit)

    def _get_memory_used_measures(self, instance_id, granularity, limit):
        """
        Memory used getter

        Args:
            instance_id (str): The id of the instance to fetch the measurements
            granularity (int): The granularity of the measurements fetched, expressed in seconds
            limit (int): The maximum number of measurements returned

        Returns:
            dict: A structure containing all the measurements regarding Memory Used
        """
        return self._get_metric_values(instance_id=instance_id,
                                       metric="memory@memory.used",
                                       granularity=granularity,
                                       limit=limit)
