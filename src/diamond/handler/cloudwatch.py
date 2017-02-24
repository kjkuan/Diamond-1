# coding=utf-8
"""
Output the collected values to AWS CloudWatch

Automatically adds the InstanceId Dimension

#### Dependencies

 * [boto](http://boto.readthedocs.org/en/latest/index.html)

#### Configuration

Enable this handler

 * handlers = diamond.handler.cloudwatch.cloudwatchHandler

Example Config:

[[cloudwatchHandler]]
region = us-east-1
no_instance_id = False

# See http://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html
[[[dimensions]]]
environment = production
group = api
role = worker

[[[LoadAvg01]]]
collector = loadavg
metric = 01
namespace = MachineLoad
name = Avg01
unit = None


[[[LoadAvg05]]]
collector = loadavg
metric = 05
namespace = MachineLoad
name = Avg05
unit = None

"""

import sys
import datetime

from diamond.handler.Handler import Handler
from diamond.utils.config import str_to_bool
from configobj import Section

try:
    import boto
    import boto.ec2.cloudwatch
    import boto.utils
except ImportError:
    boto = None


class cloudwatchHandler(Handler):
    """
      Implements the abstract Handler class
      Sending data to a AWS CloudWatch
    """

    def __init__(self, config=None):
        """
          Create a new instance of cloudwatchHandler class
        """

        # Initialize Handler
        Handler.__init__(self, config)

        if not boto:
            self.log.error(
                "CloudWatch: Boto is not installed, please install boto.")
            return

        # Initialize Data
        self.connection = None

        # Initialize Options
        self.region = self.config['region']

        self.dimensions = self.config.get('dimensions', {})
        if self.dimensions.__class__ is not Section:
            self.log.error("dimensions must be a sub-section!")
            return

        instances = boto.utils.get_instance_metadata()
        if 'instance-id' not in instances:
            self.log.error('CloudWatch: Failed to load instance metadata')
            return
        self.instance_id = instances['instance-id']

        # For backward compatibility: set the InstanceId dimension if not no_instance_id
        if not str_to_bool(self.config.get('no_instance_id', False)):
            self.log.debug("Setting InstanceId: " + self.instance_id)
            self.dimensions.update(InstanceId=self.instance_id)

        self.valid_config = ('region', 'collector', 'metric', 'namespace',
                             'name', 'unit', 'dimensions')
        self.rules = []
        for key_name, section in self.config.items():

            if section.__class__ is Section:

                # skips the global [dimensions] section.
                if section.name == 'dimensions':
                    continue

                keys = section.keys()
                rules = {}
                for key in keys:
                    if key not in self.valid_config:
                        self.log.warning("invalid key %s in section %s",
                                         key, section.name)
                    else:
                        rules[key] = section[key]

                        if key == 'dimensions':
                            if rules[key].__class__ is not Section:
                                self.log.error("dimensions must be a sub-section!")
                                return

                # initialize per-rule [dimensions], which "inherits" from the global [dimensions].
                dim = self.dimensions.copy()
                dim.update(rules.get('dimensions', {}))
                rules['dimensions'] = dim

                rules['collector'] = str(rules['collector'])
                rules['metric'] = str(rules['metric'])
                rules['namespace'] = str(rules.get('namespace', ''))
                rules['name'] = str(rules.get('name', section.name))
                rules['unit'] = str(rules.get('unit', 'None'))

                self.rules.append(rules)

        # Create CloudWatch Connection
        self._bind()

    def get_default_config_help(self):
        """
        Returns the help text for the configuration options for this handler
        """
        config = super(cloudwatchHandler, self).get_default_config_help()

        config.update({
            'region': '',
            'metric': '',
            'namespace': '',
            'name': '',
            'unit': '',
            'collector': '',
        })

        return config

    def get_default_config(self):
        """
        Return the default config for the handler
        """
        config = super(cloudwatchHandler, self).get_default_config()

        config.update({
            'region': 'us-east-1',
            'collector': 'loadavg',
            'metric': '01',
            'namespace': 'MachineLoad',
            'name': 'Avg01',
            'unit': 'None',
        })

        return config

    def _bind(self):
        """
           Create CloudWatch Connection
        """

        self.log.debug(
            "CloudWatch: Attempting to connect to CloudWatch at Region: %s",
            self.region)
        try:
            self.connection = boto.ec2.cloudwatch.connect_to_region(
                self.region)
            self.log.debug(
                "CloudWatch: Succesfully Connected to CloudWatch at Region: %s",
                self.region)
        except boto.exception.EC2ResponseError:
            self.log.error('CloudWatch: CloudWatch Exception Handler: ')

    def __del__(self):
        """
          Destroy instance of the cloudWatchHandler class
        """
        try:
            self.connection = None
        except AttributeError:
            pass

    def process(self, metric):
        """
          Process a metric and send it to CloudWatch
        """
        if not boto:
            return

        collector = str(metric.getCollectorPath())
        metricname = str(metric.getMetricPath())
        timestamp = datetime.datetime.utcfromtimestamp(metric.timestamp)

        # Send the data as ......

        for rule in self.rules:
            data = (
                rule['namespace'], rule['name'],
                metric.value, timestamp,
                rule['unit'], rule['dimensions']
            )
            self.log.debug(
                "Comparing Collector: [%s] with (%s) "
                "and Metric: [%s] with (%s)",
                rule['collector'], collector, rule['metric'], metricname
            )
            if rule['collector'] == collector and rule['metric'] == metricname:
                self.log.debug(
                    "CloudWatch: Attempting to publish to %s, metric: %s "
                    "with value (%s) unit: (%s) @%s and dimensions: %s" % data
                )
                try:
                    self.connection.put_metric_data(*data)
                    self.log.debug(
                        "CloudWatch: Successfully published to %s, metric: %s"
                        "with value (%s), unit: (%s) @%s and dimensions: %s" % data
                    )
                except AttributeError, e:
                    self.log.error(
                        "CloudWatch: Failed publishing - %s ", str(e))
                except Exception:  # Rough connection re-try logic.
                    self.log.error(
                        "CloudWatch: Failed publishing - %s ",
                        str(sys.exc_info()[0]))
                    self._bind()
