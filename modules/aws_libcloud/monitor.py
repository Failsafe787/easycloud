"""
AWS monitor implementation (using Boto3 API)
"""

import boto3
import datetime
import logging
import pytz

from core.metamonitor import MetaMonitor
from tzlocal import get_localzone

__author__ = "Davide Monfrecola, Stefano Garione, Giorgio Gambino, Luca Banzato"
__copyright__ = "Copyright (C) 2019"
__credits__ = ["Andrea Lombardo", "Irene Lovotti"]
__license__ = "GPL v3"
__version__ = "0.10.0"
__maintainer__ = "Luca Banzato"
__email__ = "20005492@studenti.uniupo.it"
__status__ = "Prototype"


class AWSMonitor(MetaMonitor):

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
        self._bind_generic_metric_to_getter(name="cpu_load", function=self._get_cpu_measures)
        #
        # No metric available for memory_free
        # self._bind_generic_metric_to_getter(
        #    name="memory_free", function=self._get_memory_free_measures)
        #
        # No metric available for memory_used
        # self._bind_generic_metric_to_getter(
        #    name="memory_used", function=self._get_memory_used_measures)
        #
        logging.debug("[AWS MONITOR GETTERS]: " + str(self._metrics_getters))

    def connect(self):
        """
        Connect to AWS CloudWatch and initialize its client object
        """
        self.cloudwatch_client = boto3.client('cloudwatch',
                                              aws_access_key_id=self.conf.ec2_access_key_id,
                                              aws_secret_access_key=self.conf.ec2_secret_access_key,
                                              aws_session_token=self.conf.ec2_session_token,
                                              region_name=self.conf.ec2_default_region)

    def _get_metric_values(self, instance_id, metric, granularity, limit):
        """
        CloudWatch measurements getter. Conversion to generic metric name is performed here through _build_message.

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
        start_time_no_tz = local_tz.localize(start_time_local, is_dst=None)  # No daylight saving time
        end_time_no_tz = local_tz.localize(end_time_local, is_dst=None)  # No daylight saving time
        # Final times
        start_time_utc = start_time_no_tz.astimezone(pytz.utc)
        end_time_utc = end_time_no_tz.astimezone(pytz.utc)

        _samples = []

        try:
            logging.debug("Instance ID: " + str(instance_id))
            # logging.debug("FETCHING METRIC " + metric + ": " + str(instance_resources))
            _random_measurements_values = self.cloudwatch_client.get_metric_statistics(Namespace='AWS/EC2',
                                                                                       MetricName=metric,
                                                                                       Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                                                                                       StartTime=start_time_utc,
                                                                                       EndTime=end_time_utc,
                                                                                       Period=granularity,
                                                                                       Statistics=['Average'])["Datapoints"]
            # Sort all the data (data can be unordered)
            _random_measurements_values.sort(key=lambda x: x["Timestamp"])
            # Extract the most recent limit-values
            _measurements_values = _random_measurements_values[-limit:]
            # Add the measurements to the list that will be returned
            for _value in _measurements_values:
                _samples.append(self._build_message(timestamp=_value["Timestamp"],
                                                    value=_value["Average"],
                                                    unit=_value["Unit"]))
            logging.debug("MEASUREMENTS: " + str(_samples))
        except Exception as _exception:
            _samples.append(self._error_sample(_exception))
            raise _exception

        return _samples

    # Please visit https://docs.aws.amazon.com/en_us/AmazonCloudWatch/latest/monitoring/viewing_metrics_with_cloudwatch.html
    # in order to get the specific metric name for a generic metric (e.g. cpu_load -> CPUUtilization)

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
                                       metric="CPUUtilization",
                                       granularity=granularity,
                                       limit=limit)
