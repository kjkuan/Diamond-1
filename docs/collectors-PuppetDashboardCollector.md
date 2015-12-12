PuppetDashboardCollector
=====

Collect metrics from Puppet Dashboard

#### Dependencies

 * urllib2


#### Options - [Generic Options](Configuration)

<table><tr><th>Setting</th><th>Default</th><th>Description</th><th>Type</th></tr>
<tr><td>byte_unit</td><td>byte</td><td>Default numeric output(s)</td><td>str</td></tr>
<tr><td>enabled</td><td>False</td><td>Enable collecting these metrics</td><td>bool</td></tr>
<tr><td>host</td><td>localhost</td><td>Hostname to collect from</td><td>str</td></tr>
<tr><td>measure_collector_time</td><td>False</td><td>Collect the collector run time in ms</td><td>bool</td></tr>
<tr><td>metrics_blacklist</td><td>None</td><td>Regex to match metrics to block. Mutually exclusive with metrics_whitelist</td><td>NoneType</td></tr>
<tr><td>metrics_whitelist</td><td>None</td><td>Regex to match metrics to transmit. Mutually exclusive with metrics_blacklist</td><td>NoneType</td></tr>
<tr><td>path</td><td>puppetdashboard</td><td>Path to the dashboard</td><td>str</td></tr>
<tr><td>port</td><td>5678</td><td>Port number to collect from</td><td>int</td></tr>
</table>

#### Example Output

```
servers.hostname.puppetdashboard.changed 10
servers.hostname.puppetdashboard.pending 0
servers.hostname.puppetdashboard.unchanged 4
servers.hostname.puppetdashboard.unreported 0
servers.hostname.puppetdashboard.unresponsive 3
```

### This file was generated from the python source
### Please edit the source to make changes
