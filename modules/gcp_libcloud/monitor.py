"""
Google Cloud monitor implementation (using StackDriver API)
"""

import datetime
import logging
import time

from core.metamonitor import MetaMonitor
from google.cloud import monitoring_v3
from google.oauth2.credentials import Credentials
from libcloud.common.google import GoogleOAuth2Credential
from os import sep

__author__ = "Davide Monfrecola, Stefano Garione, Giorgio Gambino, Luca Banzato"
__copyright__ = "Copyright (C) 2019"
__credits__ = ["Andrea Lombardo", "Irene Lovotti"]
__license__ = "GPL v3"
__version__ = "0.10.0"
__maintainer__ = "Luca Banzato"
__email__ = "20005492@studenti.uniupo.it"
__status__ = "Prototype"


class GCPMonitor(MetaMonitor):

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
        # self._bind_generic_metric_to_getter(name="memory_free", function=self._get_memory_free_measures)
        #
        # No metric available for memory_used
        # self._bind_generic_metric_to_getter(name="memory_used", function=self._get_memory_used_measures)
        #
        logging.debug("[GCP MONITOR GETTERS]: " + str(self._metrics_getters))

    def connect(self):
        """
        Connect to GCP StackDriver and initialize its client object
        """
        credential_file = "~" + sep + ".google_libcloud_auth." + self.conf.gcp_project
        scopes = ["https://www.googleapis.com/auth/monitoring"  # View and write monitoring data for all of your Google projects
                  ]
        # Ask for or use an existing auth token
        oauth_client = GoogleOAuth2Credential(user_id=self.conf.gcp_access_key_id,
                                              key=self.conf.gcp_secret_access_key,
                                              credential_file=credential_file,
                                              scopes=scopes)
        # Create Google-specific Credentials object
        creds = Credentials(oauth_client.access_token)
        # Create the StackDriver client
        self.stackdriver_client = monitoring_v3.MetricServiceClient(credentials=creds)

    def _get_metric_values(self, instance_id, metric, granularity, limit):
        """
        StackDriver measurements getter. Conversion to generic metric name is performed here through _build_message.

        Args:
            instance_id (str): The id of the instance to fetch the measurements
            metric (str): The *specific* metric name to get the values
            granularity (int): The granularity of the measurements fetched, expressed in seconds
            limit (int): The maximum number of measurements returned

        Returns:
            dict: A structure containing all the measurements for a metric
        """
        logging.debug("Fetching metric \"" + metric + "\" with granularity=" + str(granularity) + " and limit=" + str(limit))
        # Get the project full path
        project_name = self.stackdriver_client.project_path(self.conf.gcp_project)
        # Define time interval for retrieving metrics
        interval = monitoring_v3.types.TimeInterval()
        # now is a UNIX timestamp (60 seconds are equal to 100 units)
        # The latest measurements are 5 minutes back in time, so we add a -500 ms in order to cover this delay
        now = time.time()
        interval.start_time.seconds = int(now - (((granularity / 0.6) * limit)) + (granularity / 0.6) * 2 - 500)
        interval.end_time.seconds = int(now)
        # Set the aggregation level
        aggregation = monitoring_v3.types.Aggregation()
        aggregation.alignment_period.seconds = granularity
        aggregation.per_series_aligner = (monitoring_v3.enums.Aggregation.Aligner.ALIGN_MEAN)

        _samples = []

        try:
            logging.debug("Instance ID: " + str(instance_id))
            results = self.stackdriver_client.list_time_series(project_name,
                                                               "metric.type = \"" + metric + "\" AND " +
                                                               "metric.label.instance_name = \"" + instance_id + "\"",  # FILTRO ()
                                                               interval,
                                                               monitoring_v3.enums.ListTimeSeriesRequest.TimeSeriesView.FULL,
                                                               aggregation)
            _random_measurements_values = []
            for result in results:
                for point in result.points:
                    _random_measurements_values.append(point)
            # Sort all the data (data can be unordered)
            _random_measurements_values.sort(key=lambda x: datetime.datetime.fromtimestamp(x.interval.start_time.seconds))
            # Extract the most recent limit-values
            _measurements_values = _random_measurements_values[-limit:]
            # Get the metric unit
            _metric_unit = "n/a"
            for page in self.stackdriver_client.list_metric_descriptors(project_name,
                                                                        filter_="metric.type = \"" + metric + "\"").pages:
                for element in page:
                    _metric_unit = element.unit
                    break
            # Add the measurements to the list that will be returned
            for _value in _measurements_values:
                _samples.append(self._build_message(timestamp=_value.interval.start_time.seconds,
                                                    value=_value.value.double_value,
                                                    unit=_metric_unit))
            logging.debug("MEASUREMENTS: " + str(_samples))
        except Exception as _exception:
            _samples.append(self._error_sample(_exception))
            raise _exception

        return _samples

    # Please visit https://cloud.google.com/monitoring/api/metrics_gcp
    # in order to get the specific metric name for a generic metric
    # (e.g. cpu_load -> compute.googleapis.com/instance/cpu/utilization)
    #
    # !NOTE!: all the metrics in the page are listed in the form "instance/cpu/utilization"
    # You need to add the prefix "compute.googleapis.com/" to each metric name
    # in order to get them working with EasyCloud
    #
    # e.g. "instance/cpu/utilization" -> "compute.googleapis.com/instance/cpu/utilization"

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
                                       metric="compute.googleapis.com/instance/cpu/utilization",
                                       granularity=granularity,
                                       limit=limit)
