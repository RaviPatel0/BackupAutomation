sft ssh $1 << EOF 2> out.txt
sudo su - splunk
splunk search 'index="_internal" sourcetype=splunkd source="/opt/splunk/var/log/splunk/splunkd.log" earliest=-30 | fields splunk_server | stats count by splunk_server' -auth "admin:$2"
exit
exit
EOF 
