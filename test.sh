sft ssh $1 << EOF > out.txt
sudo su - splunk
splunk show shcluster-status -auth "admin:$2"
exit
exit
EOF 
