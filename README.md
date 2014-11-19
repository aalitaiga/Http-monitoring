Http-monitoring
===============

A simple console program to monitor the traffic on your local machine

Consume

              an actively written-to w3c-formatted HTTP access log
Every


              10s, display in the console the sections of the web site
              with the most hits (a section is defined as being what's
              before the second '/' in a URL. i.e. the section for "http://my.site.com/pages/create'
                is ""http://my.site.com/pages"), as well as
              interesting summary statistics on the traffic as a whole.
Make

              sure a user can keep the console app running and monitor
              traffic on their machine
Whenever


              total traffic for the past 2 minutes exceeds a certain
              number on average, add a message saying that “High traffic
              generated an alert - hits = {value}, triggered at {time}”
Whenever


              the total traffic drops again below that value on average
              for the past 2 minutes, add another message detailing when
              the alert recovered
Make

              sure all messages showing when alerting thresholds are

To do:

Alert by mail, phone?
Call the gc to limit the memory usage
Add some stats to predict when a threshold will be crossed
Don't only look at the graph of connection but have a look 
to the first derivative, send a warning when it's too high
Also monitor https traffic

