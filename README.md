# BackupAutomation
**CREST TechOps Backup &amp; Sanity Check automation**


**Run Backup scrpit as below**


**1. Clone repo**

    git clone https://github.com/RaviPatel0/BackupAutomation.git

**2. Go to the BackupAutomation directory**


**3. Give execution permission to test.sh and test1.sh files**

    chmod +x test.sh
    chmod +x test1.sh
    
**4. Run python script**

    python3 backup.py -s <STACK-NAME> -t <TARGETS (Example: sh1,c0m1,idm1,indexer,shc1) > -j <JIRA ID>

  
**5 Example**
  
    python3 backup.py -s fb -t shc1,c0m1 -j TO-123456


**NOTE**

You can choose either c0m1 or indexer.

    If stack is Classic then choose only c0m1.

    If stack is NOAH then choose only indexer.


