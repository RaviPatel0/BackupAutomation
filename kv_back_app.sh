sft ssh $1 << EOF > out.txt
sudo su - splunk
splunk backup kvstore -archiveName backup-$3 -appName $4 -auth "admin:$2"
exit
exit
EOF 