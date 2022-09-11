####################################
#                                  #
#   Author : Krushi Vasani         #
#   Author : Ravi Nandasana        #
#                                  #
####################################

import argparse
from datetime import date
import http
import os
import sys
from unicodedata import name
import warnings
from getpass import getpass, getuser
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from jira.client import JIRA
from shared.preq import co2_login,check_vault_login
from shared.checks import check_disk_space, cm_app_specfic_backup, eb_tool_backup, indexer_searchability, kvstore_backup, kvstore_status, sh_app_specfic_backup, shcluster_status,query_yes_no

warnings.filterwarnings(action="ignore", category=ResourceWarning)
warnings.filterwarnings(action='ignore', message='Unverified HTTPS request')

parser = argparse.ArgumentParser()

parser.add_argument('-s', '--stack',
                    help='Stack name',
                    required=True)

parser.add_argument('-t', '--target',
                    help=' Target name (Example: sh1,c0m1,idm1,indexer,shc1',
                    required=True)

parser.add_argument('-j', '--jira',
                    help='Jira ticket (Example: TO-16301)',
                    required=True)

package=[]
AD_USER = getuser()
SHELL_PATH = os.environ['PATH']
HOME_PATH = os.environ['HOME']

choice = input("Take backup:\n1. Using EBTOOL\n2. App Specific\n3. KV Store\n4. Exit \n")

if choice == '2':
            package = input("Enter Package ID : ").split(',')
if choice == '3':
    if query_yes_no("\n\nDo you want to take full KV Store Backup ?", "yes"):
        kv_node = input("Enter KV Store Backup node (shc1,sh1,sh2, etc ...) :")
        backup_type = "full"
    else:
        package = input("Enter Package ID for app-specific KVStore Backup : ").split(',')
        kv_node = input("Enter KV Store Backup node (shc1,sh1,sh2, etc ...) : ")
        backup_type = "app"

print("Your username is " + AD_USER)


JIRA_SERVER = "https://splunk.atlassian.net"
args = parser.parse_args()

# Arguments
STACK = args.stack
BACKUP_NODES = args.target

# Strings
POST_DOMAIN = ".splunkcloud.com"
SPLUNKBASE_URL = "https://splunkbase.splunk.com/app/"
JIRA_ID = "KRUSHI"
CO2_ENV = ""
VAULT_TOKEN = ""
SHC_MEMBER = ""
ADMIN_VAULT_PASS = ""

# Dictionaries
co2_instances = {}
instance_dict={}

# Lists
BACKUP_NODESS =[]

if args.jira is not None:
    JIRA_ID = args.jira

VAULT_ADDR = "https://vault.splunkcloud.systems"
VAULT_PATH = "/v1/cloud-sec-lve-ephemeral/creds/"

AD_PASSWORD = getpass(prompt='Enter your AD_PASSWORD: ', stream=None)


OKTA_PASSWORD = getpass(
    prompt='OKTA_PASSWORD (If it is the same as AD_PASSWORD, just press Enter): ', stream=None)

if OKTA_PASSWORD == '':
    OKTA_PASSWORD = AD_PASSWORD
       
# read JIRA_TOKEN from ~/.jira/token file
JIRA_TOKEN = ""
try:
    with open('/Users/' + AD_USER + '/.jira/token', "r") as jira_token_read:
        JIRA_TOKEN = jira_token_read.read().strip()
except FileNotFoundError as fe:
    JIRA_TOKEN = getpass(prompt='Enter your JIRA_TOKEN: ', stream=None)
    if ".jira" not in os.listdir('/Users/' + AD_USER):
        os.mkdir('/Users/' + AD_USER + '/.jira/')
    with open('/Users/' + AD_USER + '/.jira/token', "w") as jira_token_write:
        jira_token_write.write(JIRA_TOKEN)

EMAIL_ID = (AD_USER + '@splunk.com')

if POST_DOMAIN == ".splunkcloud.com":
    CO2_ENV = "prod"
    CO2APIENDPOINT = "https://api.co2.lve.splunkcloud.systems"
    
try:
    setEnv = str(os.popen('cloudctl config use ' +
                    CO2_ENV + ' 2>&1').read())
except Exception as e:
    print(e)
    
print("CO2 Configuration:\n" + setEnv + "##########")


try:
    check_vault_login(VAULT_ADDR,OKTA_PASSWORD)
    co2_login(AD_PASSWORD)

except Exception as e:
    print(e)
    quit()

def get_token():
  f = open(str(Path.home())+"/.cloudctl/token_"+ CO2_ENV, "r")
  return f.read()

try:
    res = requests.get(CO2APIENDPOINT+"/v3/stacks/"+STACK+"/instances", headers={"authorization": "Bearer "+get_token().strip()})	
    co2_instances = res.json()	
except Exception as e:
    print(e)
    quit()

try:
    token_request = requests.post("https://splunkbase.splunk.com/api/account:login/",
                                  data=[('username', AD_USER + '@splunk.com'), ('password', AD_PASSWORD)])
except Exception as e:
    print(e)
    quit()

if token_request.status_code == 200:
    SPLUNKBASE_TOKEN = (BeautifulSoup(
        token_request.text, "html.parser")).feed.id.text
else:
    print("Failed to get Splunkbase Token... Check AD_PASSWORD")
    quit()


def patch_http_response_read(func):
    def inner(*args):
        try:
            return func(*args)
        except http.client.IncompleteRead as e:
            return e.partial

    return inner

http.client.HTTPResponse.read = patch_http_response_read(
    http.client.HTTPResponse.read)


try:
    results = co2_instances
    urls=[]
    if 'inputs_data_managers' in results:
        for idm in results["inputs_data_managers"]:
            for ids in idm["urls"]:
                idm_name = idm["name"]
                instance_dict[idm_name]=ids

    if 'cluster_master' in results:
        # for cm in results["cluster_master"]:
            for cms in range(1):
                cm_name =results["cluster_master"]["name"]
                cm_fqdn=results["cluster_master"]["urls"][-1]
                instance_dict[cm_name]= cm_fqdn

    if 'search_heads' in results:
        for sh in results["search_heads"]:
            for ids in sh["urls"]:
                if(sh["name"] == 'shc1'):
                    pass
                else:
                    sh_name = sh["name"]
                    instance_dict[sh_name]=ids

    if 'search_head_clusters' in results:
        for sh in results["search_head_clusters"]:
            for shcs in sh["instances"]:
                for ids in shcs["urls"]:
                    ids = ids.split('.')[0]
                    urls.append(ids)
                    shc_name = sh["name"]
                    instance_dict[shc_name]=urls
                    
    if 'indexers' in results:
        for idx in results["indexers"]:
            for ids in idx["urls"]:
                idxs = 'indexer'
                instance_dict[idxs]=ids

    # if 'indexers' in results:
    #     for idx in results["indexers"]:
    #         for ids in idx["urls"]:
    #             print(ids)

    if BACKUP_NODES is not None:
        for BACKUP_NODES in BACKUP_NODES.split(','):
            BACKUP_NODESS.append(BACKUP_NODES)
    print(instance_dict)

    if 'c0m1' in BACKUP_NODESS and 'indexer' in BACKUP_NODESS:
        print("\nYou chose c0m1 and indexer both target. If stack is Classic then choose only c0m1. If stack is NOAH then choose only indexer.")
        exit()
    if 'indexer' in BACKUP_NODESS:
        print("Please make sure that stack is Noah")
    if 'c0m1' in BACKUP_NODESS:
        print("Please make sure that stack is Classic")

    JIRA_CMT_STR = "h2. Took backup:\n"
    JIRA_KV_STR = ""
    get_pass="vault kv get cloud-sec/std/lve/stacks/"+STACK+"/admin | grep plaintext | awk {'print $2'}"
    PASS = os.popen(get_pass).read()
    PASS= PASS.split("\n")[0]
    JIRA_SCK_STR = "h2. Sanity Check:\n"
    
    sanity_pointer_shc = 0
    sanity_pointer_search = 0
    sanity_pointer_kv = 0
    
    while(choice!='4'):
        for i in instance_dict.keys():
            for j in BACKUP_NODESS:
                check_kv_status = "failed"
                kv_captain = "test"
                if j.startswith('shc') & (i==j):
                    flag = 0
                    for x in instance_dict[i]:
                        if flag == 0 and sanity_pointer_shc == 0:
                            # SHCluster Status
                            JIRA_SCK_STR=shcluster_status(JIRA_SCK_STR,x,PASS)                        
                            flag = 1
                            sanity_pointer_shc = 1

                        # KV Store Status
                        if choice == '3' and kv_node == "shc1" and sanity_pointer_kv == 0:
                            JIRA_SCK_STR,check_kv_status,kv_captain = kvstore_status(JIRA_SCK_STR,x,PASS,"yes")
                            JIRA_SCK_STR,check_kv_status,kv_captain = kvstore_status(JIRA_SCK_STR,kv_captain,PASS,"yes")
                            sanity_pointer_kv = 1
                        
                        # Indexer Searchability
                        if sanity_pointer_search == 0:
                            JIRA_SCK_STR=indexer_searchability(JIRA_SCK_STR,x,PASS,j)

                        # EB Tool Backup
                        if choice == '1':
                            disk_space=check_disk_space(x)
                            if int(disk_space) > 75:
                                JIRA_CMT_STR+="*on "+x+"*\n"
                                JIRA_CMT_STR+="*{color:red}Enough Disk space is not available on this node. Please take app-specific backup{color}*\n"
                                continue
                            JIRA_CMT_STR=eb_tool_backup(JIRA_CMT_STR,x)

                        # App Specific Backup
                        if choice == '2':
                            JIRA_CMT_STR=sh_app_specfic_backup(JIRA_CMT_STR,x,JIRA_ID,package)
                            
                        # KV Store Backup
                        if choice == '3' and check_kv_status == "ready" and x == kv_captain:
                            JIRA_KV_STR=kvstore_backup(JIRA_KV_STR,kv_captain,PASS,JIRA_ID,package,backup_type)  
                            print("Please Check KV Strore status before start Maintenance Window")

                elif(i==j):
                    node_fqdn = str(instance_dict[j]).split('.')[0]
                    if i != "indexer" and sanity_pointer_search == 0:
                        # Checking Indexer Searchability ... 
                        JIRA_SCK_STR=indexer_searchability(JIRA_SCK_STR,node_fqdn,PASS,j)
                        
                    # KV Store Status
                    if choice == '3' and kv_node != "shc1" and sanity_pointer_kv == 0:
                        node_id = (instance_dict[kv_node]).split(".")[0]
                        JIRA_SCK_STR,check_kv_status = kvstore_status(JIRA_SCK_STR,node_id,PASS,"no")
                        sanity_pointer_kv = 1
                        
                        
                    if choice == '1':
                        # Checking Disk Space 
                        if i != "indexer":
                            disk_space=check_disk_space(node_fqdn)
                            if int(disk_space) > 75:
                                JIRA_CMT_STR+="*on "+node_fqdn+"*\n"
                                JIRA_CMT_STR+="*{color:red}Enough Disk space is not available on this node. Please take app-specific backup{color}*\n"
                                continue

                        # Taking EBTool Backup
                        JIRA_CMT_STR=eb_tool_backup(JIRA_CMT_STR,node_fqdn)
                    if choice =='2':
                        # Taking App Specific Backup
                        if j.startswith('c0m1'):
                            JIRA_CMT_STR=cm_app_specfic_backup(JIRA_CMT_STR,node_fqdn,JIRA_ID,package)
                        else:
                            JIRA_CMT_STR=sh_app_specfic_backup(JIRA_CMT_STR,node_fqdn,JIRA_ID,package)
      
                    # KV Store Backup
                    if choice == '3' and check_kv_status == "ready" and (instance_dict[kv_node]).split(".")[0] == node_fqdn:
                        JIRA_KV_STR=kvstore_backup(JIRA_KV_STR,node_fqdn,PASS,JIRA_ID,package,backup_type)  
                        print("Please Check KV Strore status before start Maintenance Window")
                      
        sanity_pointer_search = 1
        
        choice = input("\n\nWant to continue with backup:\n1. Using EBTOOL\n2. App Specific\n3. KV Store\n4. Exit \n")
        if choice == '2':
            package = input("Enter Package ID : ").split(',')
        if choice == '3':
            if query_yes_no("\n\nDo you want to take full KV Store Backup ?", "yes"):
                backup_type = "full"
                kv_node = input("Enter KV Store Backup node (shc1,sh1,sh2, etc ...) :")
            else:
                package = input("Enter Package ID for app-specific KVStore Backup : ").split(',')
                kv_node = input("Enter KV Store Backup node (shc1,sh1,sh2, etc ...) : ")
                backup_type = "app"

    JIRA_CMT_STR+=JIRA_KV_STR
    print(JIRA_CMT_STR)
    print(JIRA_SCK_STR)
    if query_yes_no("\n\nDo you want to add JIRA comment?", "yes"):     
    
        if JIRA_ID == "KRUSHI":
            sys.stdout.write(
                "\nEnter the app install JIRA issue id (CO-123456):")
            JIRA_ID = input()

        options = {'server': JIRA_SERVER}
        jira = JIRA(options=options, basic_auth=(EMAIL_ID, JIRA_TOKEN))
        issue = jira.issue(JIRA_ID)
        remove_lable=['auto_precheck_general','auto_precheck_review','auto_precheck_failed','auto_precheck_complete','auto_precheck_in_progress']
        issue.fields.labels=[issue.fields.labels[i] for i in range(len(issue.fields.labels)) if issue.fields.labels[i] not in remove_lable]
        issue.fields.labels.append(u'auto_precheck_general')
        issue.update(fields={"labels": issue.fields.labels})
        jira.add_comment(issue, JIRA_CMT_STR)
        jira.add_comment(issue, JIRA_SCK_STR)
        print("Comment added successfully: " +
            JIRA_SERVER + "/browse/" + JIRA_ID)           

    print("\n")
    print("v1.0 @copyright Krushi Vasani & Ravi Nandasana")
    print("\n")
except Exception as e:
    print(e)
    quit()