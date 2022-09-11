sft ssh $1 << EOF > out.txt
sudo su - splunk
splunk show kvstore-status -auth "admin:$2"
exit
exit
EOF 
