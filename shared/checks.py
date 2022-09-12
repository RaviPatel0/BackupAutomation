import subprocess
import os
import re
import sys
import time

def query_yes_no(question, default="no"):
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)
    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write(
                "Please respond with 'yes' or 'no' (or 'y' or 'n').\n")
            

def shcluster_status(JIRA_SCK_STR,x,PASS):
    # SHCluster Status
    print("Checking SHCluster Status ... ")
    subprocess.call(['sh', './shc_status.sh',x,PASS])
    JIRA_SCK_STR+="*SHCluster Status :*\n"
    JIRA_SCK_STR+="{code:java}\n"
    JIRA_SCK_STR+="splunk@"+x+":~$ splunk show shcluster-status\n"
    with open('out.txt', 'r') as f:
        for line in f:
            JIRA_SCK_STR+=line
    JIRA_SCK_STR+="{code}\n"
    
    return JIRA_SCK_STR
    
    
def kvstore_status(JIRA_SCK_STR,x,PASS,is_shc):
    print("Checking KVStore Status on "+x+"... ")
    subprocess.call(['sh', './kv_status.sh',x,PASS])
    JIRA_SCK_STR+="*KVStore Status :*\n"
    JIRA_SCK_STR+="{code:java}\n"
    JIRA_SCK_STR+="splunk@"+x+":~$ splunk show kvstore-status\n"
    with open('out.txt', 'r') as f:
        for line in f:
            JIRA_SCK_STR+=line
    JIRA_SCK_STR+="{code}\n"
    
    # Verify KV Store Status
    print("Verifing KVStore Status "+x+" ... ")
    check_kv_status = os.popen("cat out.txt | egrep 'ready|Ready' | wc -l").read()
    check_kv_status = check_kv_status.split("\n")[0].strip()
    if check_kv_status == "2":
        check_kv_status = "ready"
    else:
        check_kv_status = "failed"
        
    # Identify KV Store Captain
    if check_kv_status == "ready" and is_shc == "yes":
        print("Identifing KV Store Captain "+x+" ... ")
        kv_captain = os.popen("cat out.txt | grep -B 10 'KV store captain' | grep 'hostAndPort'").read()
        kv_captain = kv_captain.split()[2].split(":")[0]
        JIRA_SCK_STR+= "\n*{color:#14892c}KVStore Status is Ready.{color}*\n"
        kv_captain=kv_captain.split(".")[0]
        print("KVStore Captain ",kv_captain)
    elif check_kv_status == "ready" and is_shc == "no":
        JIRA_SCK_STR+= "\n*{color:#14892c}KVStore Status is Ready.{color}*\n"
        return JIRA_SCK_STR,check_kv_status
    else:
        JIRA_SCK_STR+= "\n*{color:#d04437}KVStore Status is failed. Please take backup after fix KVStore Status*{color}*\n"
        print("KVStore Status is failed. Please take backup after fix KVStore Status")
        check_kv_status="failed"
        kv_captain="error"
        return JIRA_SCK_STR,check_kv_status,kv_captain
    
    return JIRA_SCK_STR,check_kv_status,kv_captain


def indexer_searchability(JIRA_SCK_STR,x,PASS,j):
    print("Checking Indexer Searchability ... ")
    subprocess.call(['sh', './lookup.sh',x,PASS])
    check_err="ERROR:"
    JIRA_SCK_STR+="*Lookup Error Check on :"+x+" ("+j+")*\n"
    lookup_flag = 0
    temp = ""
    with open('out.txt', 'r') as f:
        for line in f:
            if re.search(check_err, line):
                lookup_flag = 1
                temp+=line
    if lookup_flag == 1:  
        JIRA_SCK_STR+="*{color:#d04437}Below lookup errors are present{color}*\n\n"
        JIRA_SCK_STR+="{code:java}\n"+temp+"{code}"
    else:
        JIRA_SCK_STR+="{color:#14892c} No lookup error present {color} \n\n"
        
    return JIRA_SCK_STR

def check_disk_space(x):
    print("Checking Disk Space ... ")
    cmd =  "sft ssh "+ x + " --command 'sudo su  - splunk -c \"df -h | grep \'/opt/splunk\' \"'"
    op= os.popen(cmd).read()
    disk_space=(op.split()[-2]).split("%")[0]

    return disk_space


def eb_tool_backup(JIRA_CMT_STR,x,j):
    print("Taking EBTool Backup ... ")
    JIRA_CMT_STR+="*on "+x+" ("+j+")*\n"
    JIRA_CMT_STR+="{code:java}\n"
    cmd =  "sft ssh " + x + " --command 'sudo su  - splunk -c \"PYTHONPATH="" LD_LIBRARY_PATH="" >/dev/null; local-backup-splunketc backup;\"'"
    op= os.popen(cmd).read()
    JIRA_CMT_STR+="splunk@"+x+":~$  local-backup-splunketc backup\n"


    with open('tempf.txt', 'w') as f:
        print(op, file=f)
        
    with open("tempf.txt","r") as file_one:

        patrn = "Tab-completion"
        patrn1="closed"
        patrn2="Required space constraint not met"
        for line in file_one:
            if re.search(patrn, line):
                pass
            elif re.search(patrn1, line):
                pass
            elif re.search(patrn2, line):
                JIRA_CMT_STR+="Required space constraint not met"
            else:
                JIRA_CMT_STR+=line
    JIRA_CMT_STR+="splunk@"+x+":~$ \n"
    JIRA_CMT_STR+="{code}\n"
    
    return JIRA_CMT_STR



def sh_app_specfic_backup(JIRA_CMT_STR,x,JIRA_ID,package,j):
    print("Taking App Specific Backup ... ")
    JIRA_CMT_STR+="*on "+x+" ("+j+")*\n"
    op=""
    JIRA_CMT_STR+="{code:java}\n"
    for k in package:
        cmd = "sft ssh " + x + " --command 'sudo su  - splunk -c \"date;cd /opt/splunk/;mkdir /opt/splunk/tmp/"+JIRA_ID+"/;cd;cd /opt/splunk/etc/apps/;cp -pR "+str(k).strip()+"/ /opt/splunk/tmp/"+JIRA_ID+"/;ls -la /opt/splunk/tmp/"+JIRA_ID+"/\"'"  
        op= os.popen(cmd).read()
        JIRA_CMT_STR+="splunk@"+x+":~/etc/apps$  cp -pR "+str(k)+"/ /opt/splunk/tmp/"+JIRA_ID+"/\n"

        with open('tempf.txt', 'w') as f:
            print(op, file=f)
        with open("tempf.txt","r") as file_one:
            patrn1="No such file or directory"
            for line in file_one:
                if re.search(patrn1, line):
                    JIRA_CMT_STR+="\n------>    Package not found - ("+str(k)+")    <------\n\n"
                    break             
    with open('tempf.txt', 'w') as f:
        print(op, file=f)
        
    JIRA_CMT_STR+="splunk@"+x+":~/etc/apps$  ls -la /opt/splunk/tmp/"+JIRA_ID+"/\n"   
    with open("tempf.txt","r") as file_one:
        patrn = "Tab-completion"
        patrn4 = "closed"
        patrn1="No such file or directory"
        patrn3="mkdir: cannot create directory"
        patrn5="UTC"
        for line in file_one:
            if re.search(patrn, line):
                pass
            elif re.search(patrn3, line):
                pass
            elif re.search(patrn4, line):
                pass
            elif re.search(patrn5, line):
                DATE = line
            elif re.search(patrn1, line):
                pass
            else:
                JIRA_CMT_STR+=line
    
    JIRA_CMT_STR+="splunk@"+x+":~/etc/apps$ date\n"
    JIRA_CMT_STR+=DATE
    JIRA_CMT_STR+="splunk@"+x+":~/etc/apps$ \n"
    JIRA_CMT_STR+="{code}\n"
        
    return JIRA_CMT_STR

def cm_app_specfic_backup(JIRA_CMT_STR,node_fqdn,JIRA_ID,package,j):
    print("Taking App Specific Backup ... ")
    JIRA_CMT_STR+="*on "+node_fqdn+" ("+j+")*\n"
    JIRA_CMT_STR+="{code:java}\n"
    op=""
    for k in package:   
        cmd = "sft ssh " + node_fqdn + " --command 'sudo su  - splunk -c \"date;cd /opt/splunk/;mkdir /opt/splunk/tmp/"+JIRA_ID+"/;cd;cd /opt/splunk/etc/master-apps/;cp -pR "+str(k).strip()+"/ /opt/splunk/tmp/"+JIRA_ID+"/;ls -la /opt/splunk/tmp/"+JIRA_ID+"/\"'"  
        op= os.popen(cmd).read()
        JIRA_CMT_STR+="splunk@"+node_fqdn+":~/etc/master-apps$  cp -pR "+str(k)+"/ /opt/splunk/tmp/"+JIRA_ID+"/\n"

        with open('tempf.txt', 'w') as f:
            print(op, file=f)

        with open("tempf.txt","r") as file_one:
            patrn1="No such file or directory"
            for line in file_one:
                if re.search(patrn1, line):
                    JIRA_CMT_STR+="\n------>    Package not found - ("+str(k)+")    <------\n\n"
                    break             
    with open('tempf.txt', 'w') as f:
        print(op, file=f)
        
    JIRA_CMT_STR+="splunk@"+node_fqdn+":~/etc/master-apps$  ls -la /opt/splunk/tmp/"+JIRA_ID+"/\n"
    with open("tempf.txt","r") as file_one:
        patrn = "Tab-completion"
        patrn4 = "closed"
        patrn1="No such file or directory"
        patrn3="mkdir: cannot create directory"
        patrn5="UTC"
        for line in file_one:
            if re.search(patrn, line):
                pass
            elif re.search(patrn3, line):
                pass
            elif re.search(patrn4, line):
                pass
            elif re.search(patrn5, line):
                DATE = line
            elif re.search(patrn1, line):
                pass
            else:
                JIRA_CMT_STR+=line
                    
    JIRA_CMT_STR+="splunk@"+node_fqdn+":~/etc/master-apps$ date\n"
    JIRA_CMT_STR+=DATE
    JIRA_CMT_STR+="splunk@"+node_fqdn+":~/etc/master-apps$ \n"
    JIRA_CMT_STR+="{code}\n"

    return JIRA_CMT_STR
   
def kvstore_backup(JIRA_KV_STR,node,PASS,JIRA_ID,package,backup_type):
    print("Taking KVStore Backup ... ")
    back = package
    if backup_type == "full":
        subprocess.call(['sh', './kv_back.sh',node,PASS,JIRA_ID])
        JIRA_KV_STR+="h2. *KVStore Backup*\n"
        JIRA_KV_STR+="*on "+node+"*\n"
        JIRA_KV_STR+="{code:java}\n"
        JIRA_KV_STR+="splunk@"+node+":~$ splunk backup kvstore -archiveName backup-"+JIRA_ID+"\n"
        JIRA_KV_STR+="splunk@"+node+":~$ \n"
        JIRA_KV_STR+="{code}\n"
        JIRA_KV_STR=kv_jira_commnet(JIRA_KV_STR,node,JIRA_ID,JIRA_ID)

    if backup_type == "app":
        JIRA_KV_STR+="h2. *KVStore Backup*\n"
        JIRA_KV_STR+="*on "+node+"*\n"
        JIRA_KV_STR+="{code:java}\n"
        for i in package:
            package=str(package).strip()
            subprocess.call(['sh', './kv_back_app.sh',node,PASS,i])
            print("Backup is in progress wait for 60 secounds ...")
            time.sleep(60)    
            move_next = False            
            JIRA_KV_STR+="splunk@"+node+":~$ splunk backup kvstore -archiveName backup-"+i+" -appName "+i+"\n"
            if query_yes_no("\n\nCheck KV Store status is ready on not ?", "yes"):
                pass
            else:
                while not move_next:
                    print("Again sleep for 60 secounds Backup is in progress ...")
                    time.sleep(60)   
                    move_next=query_yes_no("\n\nCheck KV Store status is ready on not ?", "no") 
                    time.sleep(60)
        JIRA_KV_STR+="splunk@"+node+":~$ \n"
        JIRA_KV_STR+="{code}\n"
        JIRA_KV_STR=kv_jira_commnet(JIRA_KV_STR,node,JIRA_ID,back)

    return JIRA_KV_STR


def kv_jira_commnet(JIRA_KV_STR,node,JIRA_ID,package_name):
    JIRA_KV_STR+="{code:java}\n"
    if package_name == JIRA_ID:
        cmd = "sft ssh " + node + " --command 'sudo su  - splunk -c \"date;cd /opt/splunk/;mkdir /opt/splunk/tmp/"+JIRA_ID+";cd;cd /opt/splunk/var/lib/splunk/kvstorebackup/;cp -pR backup-"+package_name+".tar.gz /opt/splunk/tmp/"+JIRA_ID+"/;ls -la /opt/splunk/tmp/"+JIRA_ID+"/\"'"  
        op= os.popen(cmd).read()
        JIRA_KV_STR+="splunk@"+node+":~/var/lib/splunk/kvstorebackup$  cp -pR backup-"+package_name+".tar.gz /opt/splunk/tmp/"+JIRA_ID+"/\n"
        JIRA_KV_STR+="splunk@"+node+":~/var/lib/splunk/kvstorebackup$  ls -la /opt/splunk/tmp/"+JIRA_ID+"/\n"
    else:
        for i in range(len(package_name)):
            cmd = "sft ssh " + node + " --command 'sudo su  - splunk -c \"date;cd /opt/splunk/;mkdir /opt/splunk/tmp/"+JIRA_ID+";cd;cd /opt/splunk/var/lib/splunk/kvstorebackup/;cp -pR backup-"+str(package_name[i])+".tar.gz /opt/splunk/tmp/"+JIRA_ID+"/;ls -la /opt/splunk/tmp/"+JIRA_ID+"/\"'"
            op= os.popen(cmd).read()
            JIRA_KV_STR+="splunk@"+node+":~/var/lib/splunk/kvstorebackup$  cp -pR backup-"+str(package_name[i])+".tar.gz /opt/splunk/tmp/"+JIRA_ID+"/\n"

            with open('tempf.txt', 'w') as f:
                print(op, file=f)

            with open("tempf.txt","r") as file_one:
                patrn1="No such file or directory"
                for line in file_one:
                    if re.search(patrn1, line):
                        JIRA_KV_STR+="\n------>    Package not found - ("+str(package_name[i])+")    <------\n\n"
                        break     
                    
    with open('tempf.txt', 'w') as f:
        print(op, file=f)
    JIRA_KV_STR+="splunk@"+node+":~/var/lib/splunk/kvstorebackup$  ls -la /opt/splunk/tmp/"+JIRA_ID+"/\n" 
    
    with open("tempf.txt","r") as file_one:

        patrn = "Tab-completion"
        patrn4 = "closed"
        patrn1="No such file or directory"
        patrn3="mkdir: cannot create directory"
        patrn5="UTC"
        for line in file_one:
            if re.search(patrn, line):
                pass
            elif re.search(patrn3, line):
                pass
            elif re.search(patrn4, line):
                pass
            elif re.search(patrn5, line):
                DATE = line
            elif re.search(patrn1, line):
                pass
            else:
                JIRA_KV_STR+=line
    JIRA_KV_STR+="splunk@"+node+":~/var/lib/splunk/kvstorebackup$ date\n"
    JIRA_KV_STR+=DATE
    JIRA_KV_STR+="splunk@"+node+":~/var/lib/splunk/kvstorebackup$ \n"
    JIRA_KV_STR+="{code}\n"
    
    return JIRA_KV_STR