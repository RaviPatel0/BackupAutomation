jira = str(input("Enter Jira ID T0-12345 : "))
sh = str(input("Enter SH instance ID sh-i-07a2912f4cf12684 : "))
c0m1 = str(input("Enter c0m1 instance ID c0m1-i-a5229212c8f12684 : "))

apps = int(str(input("Enter number of apps : ")))

apps_data_sh = "";
apps_data_c0m1 = " ";

for i in range(apps):
	package = str(input("Enter package name : "))
	apps_data_sh = apps_data_sh + "tar -czf /opt/splunk/tmp/"+ jira + "/" + package + ".tgz etc/apps/" + package + "/; "
	
	check_indexer = str(input("App is installed on indexer (Y/n) : "))

	if(check_indexer == 'y' or check_indexer == 'Y'):
		apps_data_c0m1 = apps_data_c0m1 + "tar -czf /opt/splunk/tmp/"+ jira + "/" + package + ".tgz etc/master-apps/" + package + "/; "
   
print("\n")
print("-------Backup Code--------")
print("\n")
print("-------SH1--------")
print("sft ssh " + sh + " --command 'sudo -u splunk sh -c \"cd /opt/splunk/; mkdir /opt/splunk/tmp/" + jira + 
	"; " + apps_data_sh + "cd /opt/splunk/tmp/" + jira + "; pwd ; ls -la; hostname -f ; date\"'")

if apps_data_c0m1 != " ":
	print("\n")
	print("-------c0m1--------")
	print("sft ssh " + c0m1 + " --command 'sudo -u splunk sh -c \"cd /opt/splunk/; mkdir /opt/splunk/tmp/" + jira + 
	"; " + apps_data_c0m1 + "cd /opt/splunk/tmp/" + jira + "; pwd ; ls -la; hostname -f ; date\"'")
	

print("\n")
print("v1.0 @copyright Ravi Nandasana")