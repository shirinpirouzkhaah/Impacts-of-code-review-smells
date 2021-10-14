 
"""
@author: Shirin
"""  
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            import json 
import json 
import numpy as np
import math
import pandas as pd
from pandas import DataFrame
from scipy.stats import norm 
from pandas.io.json import json_normalize
import matplotlib.pyplot as plt
import re
import datetime
#--------------------------------------reading data ----------------------------------
#issue tracking data
jiradata = pd.read_json("QtCre20170313-20201022.json", lines=True) 


#issue tracking data is nested jason. trying to read nested jasons 
jiradataColumn = []
for index,row in jiradata.iterrows():
    jiradataColumn.append(pd.json_normalize(row['data']))
    
J = jiradataColumn
index = 0
while index < len(J):
    print(index, len(J))
    Instance_Jira_data = J[index]
    Date = Instance_Jira_data.iloc[0]["fields.created"]
    Date = re.split('(\d+)', Date)
    print(Instance_Jira_data.iloc[0]["id"], Instance_Jira_data.iloc[0]["fields.created"])
    if 2017 > int(Date[1]) or int(Date[1]) > 2020:
        J = J[:index] + J[index+1 :]
        index = index - 1
        print("yes1", index)
    elif int(Date[1]) == 2020 and int(Date[3]) > 5:
        J = J[:index] + J[index+1 :]
        index = index - 1
        print("yes2",index)
    elif int(Date[1]) == 2020 and int(Date[3]) == 4 and int(Date[5]) > 20:
       J = J[:index] + J[index+1 :]
       index = index - 1
       print("yes3", index)
    index+=1

jiradataColumn = J
#QT review data                   
df = pd.read_json("qt_2017-01-01.json", lines=True)

inspect = df 
creator = []
for index, row in inspect.iterrows(): 
    Ddict = row["search_fields"]["project_name"]
    if(Ddict == "qt-creator/qt-creator"):
        creator.append(row)
reviewdata= pd.concat(creator, axis=1).T

#review data is nested jason. trying to read nested jasons 
reviewdataColumn = []
for index,row in reviewdata.iterrows():
    reviewdataColumn.append(pd.json_normalize(row['data']))
reviewsearchField = []
for index,row in reviewdata.iterrows():
    reviewsearchField.append(pd.json_normalize(row['search_fields']))
#getting two main columns of review data in the form of DATA FRAME
patchsets = []
comments = [] 
for index in range (len(reviewdataColumn )):
    dataDF = reviewdataColumn[index]
    if (dataDF.iloc[0]['status'] != 'NEW' and dataDF.iloc[0]['status'] != 'ABANDONED' ):
        for index3,row in dataDF.iterrows():
            patchsets.append(pd.json_normalize(row['patchSets']))
            comments.append(pd.json_normalize(row['comments']))
    
# Projects possible Bots
Eclipse_Bots = {"EGit Bot","JGit Bot","Platform Bot","CI Bot","OSEE Bot","BaSyx Bot","Eclipse Genie", "Trace Compass Bot","JDT Bot","Equinox Bot","CDT Bot","M2E Bot","PDE Bot","Orbit Bot","CBI Bot","EASE Bot","QVT-OML Bot", "Jubula Bot","Linux Tools Bot","Xtext Bot","Sirius Bot","DLTK Bot","StatET Bot","Nebula Bot","SWTBot Bot","EMFStore Bot"}    
Wireshark_Bots = {"Petri Dish Buildbot", "Wireshark code review", "human rights"}
LiberOffice_Bots = {"Jenkins", "Jenkins CollaboraOffice", "Pootle bot, LibreOﬃciant", "Weblate", "Gerrit Code Review", "JP", "libreoffice lhm"}
QT_Bots = { "Qt Sanity Bot","Qt CI Bot","Qt Cherry-pick Bot","Qt Submodule Update Bot","Qbs CI Bot","Qt LanceBot","Qt CMake Build Bot","Qt Wayland Headless Tests Bot","Qt Continuous Integration System","Qt Cleanup Bot", "Qt Doc Bot","Qt Forward Merge Bot", "The Qt Project", "Qt3dStudioBot","Qt CI Test Bot","Continuous Integration (KDAB)"}

#--------------------------------------Functions---------------------------------------
#this function gets jira data and returns index of reopened issues in the data
data = jiradataColumn
def ReopenIssues(data):
    Reopened_issues_indices = []
    for index in range (len(data)):
        instance_issue = data[index]
        changelogHistories = instance_issue.iloc[0]['changelog.histories']
        for indx in range (len(changelogHistories)):
            nested_changelogHistories = changelogHistories[indx]
            List_of_items = nested_changelogHistories.get("items")
            for indxx in range (len(List_of_items)):
                field = List_of_items[indxx]
                if(field.get("field") == "status"):
                    if(field.get("fromString") == "Closed" and field.get("toString") == "Open" ):
                        Reopened_issues_indices.append(index)
    return Reopened_issues_indices 

#this function gets jira data and index of reopened issues and returns their related commit number
def ReopenedCommits(data,ReopenedIssues):
    Reopened_issues_reviewCommits = [] 
    for index in range (len(ReopenedIssues)):
        instance_issue_index = ReopenedIssues[index]
        instance_issue = data[instance_issue_index]
        changelogHistories = instance_issue.iloc[0]['changelog.histories']
        for indx in range (len(changelogHistories)):
            nested_changelogHistories = changelogHistories[indx]
            List_of_items = nested_changelogHistories.get("items")
            for indxx in range (len(List_of_items)):
                field = List_of_items[indxx]
                if(field.get("field") == "Commits"):
                    Reopened_issues_reviewCommits.append(field.get("toString"))
    return Reopened_issues_reviewCommits

def linkage(data, patchsets):
    Commit_Number_standard_lenghth = 40
    Commit_number_of_issues = []
    for index in range (len(data)):
        instance_issue = data[index]
        changelogHistories = instance_issue.iloc[0]['changelog.histories']
        for indx in range (len(changelogHistories)):
            nested_changelogHistories = changelogHistories[indx]
            List_of_items = nested_changelogHistories.get("items")
            for indxx in range (len(List_of_items)):
                field = List_of_items[indxx]
                if(field.get("field") == "Commits"):
                    Commit_number_of_issues.append(field.get("toString")) 
    Commit_number_of_reviews = []
    for index in range (len(patchsets)):
        instance_patch = patchsets[index]
        for indx in range (len(instance_patch)):
            if (instance_patch.iloc[indx]['kind'] == "REWORK"):
                commit_number = instance_patch.iloc[indx]["parents"]
                Commit_number_of_reviews.append(commit_number)
    Issue_Commits = []
    for index in range(len(Commit_number_of_issues)):
        commit_number_string = Commit_number_of_issues[index]
        Issues_Commits_list = commit_number_string.split(" ")
        for indx in range(len(Issues_Commits_list)):
            if (len(Issues_Commits_list[indx]) == Commit_Number_standard_lenghth):
                Issue_Commits.append(Issues_Commits_list[indx])

    Review_Commits = []
    for index in range(len(Commit_number_of_reviews)):
        commit_number_string = Commit_number_of_reviews[index]
        for indx in range(len(commit_number_string)):
                Review_Commits.append(commit_number_string[indx])
    return Issue_Commits, Review_Commits
#this function gets review data, commits, and returns 3 array  patches that have at least one negative vote
# and bypassed negative reviewer patches
def bypassNegative_rev(comments):
    listWithreject = []
    listWithrejectIndex = []
    smellyList = []
    smellyListIndex = []
    rejection = False                   
    for index in range (len(comments)):
        instance_comment = comments[index]
        for indx in range (len(instance_comment)):
            # -1 and -2 are negative votes that reviewers give 
            if (instance_comment.iloc[indx]["message"].find('Code-Review-1') != -1 or instance_comment.iloc[indx]["message"].find('Code-Review-2') != -1):
                rejection=True
                break
        if(rejection):
            listWithreject.append(comments[index])
            listWithrejectIndex.append(index)
        rejection=False
    # searching for bypassed reviews in rejected reviews 
    for index in range (len(listWithreject)):
        bypass = False
        AuthorName = "" 
        negRev = ""
        instance_comment = listWithreject[index]
        if (instance_comment.iloc[0]['reviewer.name'] ==instance_comment.iloc[0]['reviewer.name'] and instance_comment.iloc[0]['reviewer.name'] not in QT_Bots): # if owner name(who uploaded the patch, first row of instance comment ) is not Nan and Bot
            AuthorName = instance_comment.iloc[0]['reviewer.name']
        for indx in range (1,len(instance_comment)):
            if (len(AuthorName) > 0 and instance_comment.iloc[indx]['reviewer.name'] == instance_comment.iloc[indx]['reviewer.name'] and instance_comment.iloc[indx]["reviewer.name"] != AuthorName and instance_comment.iloc[indx]["reviewer.name"] not in QT_Bots):
                if (instance_comment.iloc[indx]["message"].find('Code-Review-1') != -1 or instance_comment.iloc[indx]["message"].find('Code-Review-2') != -1):
                    negRev = instance_comment.iloc[indx]["reviewer.name"]
                    Positive_vote_after_neg = 0
                    for indxx in range (indx+1,len(instance_comment)):
                        if (instance_comment.iloc[indxx]["reviewer.name"] == negRev ):
                            # if negative reviewer, reviews and gives positive vote afterward, the review is not bypassed
                            if (instance_comment.iloc[indxx]["message"].find('Code-Review+1') != -1 or instance_comment.iloc[indxx]["message"].find('Code-Review+2') != -1):
                                Positive_vote_after_neg = Positive_vote_after_neg + 1
                    if Positive_vote_after_neg == 0:
                        bypass = True
                        break
                                
        if (bypass):
            smellyList.append(listWithreject[index]) # bypassed patches comments
            smellyListIndex.append(listWithrejectIndex[index]) 
            
    return  listWithreject,smellyList, smellyListIndex#bypassed patchsets

#---------------------------------------calling functions------------------------------- 
reopened_issues = ReopenIssues(jiradataColumn)    
reopened_commitnumbers = ReopenedCommits(jiradataColumn,reopened_issues)
# spliting reopened commits and get the unique list of them 
Reopened_commit_numbers = [] 
Commit_Number_standard_lenghth = 40
for index in range(len(reopened_commitnumbers)):
    commit_number_string = reopened_commitnumbers[index]
    Reopened_Commits_list = commit_number_string.split(" ")
    for indx in range(len(Reopened_Commits_list)):
        if (len(Reopened_Commits_list[indx]) == Commit_Number_standard_lenghth):
            Reopened_commit_numbers.append(Reopened_Commits_list[indx])
            
listWithReject, smellyList, smellyListIndex =  bypassNegative_rev(comments)
Issue_Commits, Review_Commits = linkage(data, patchsets)
Unique_Review_Commits = []
for i in Review_Commits:
    if i not in Unique_Review_Commits:
        Unique_Review_Commits.append(i)

#---------------------------------------------- Missing Context ---------------------------------
Missing_linkage_smell = 0
Missing_linkage_Rev_Comments = []
for index in range (len(Unique_Review_Commits)):
    RevCom = Unique_Review_Commits[index]
    if RevCom not in Issue_Commits:
        Missing_linkage_smell = Missing_linkage_smell + 1
        Missing_linkage_Rev_Comments.append(RevCom)
for index in range (len(patchsets)):
        instance_patch = patchsets[index]
        for indx in range (len(instance_patch)):
            if (instance_patch.iloc[indx]['kind'] == "REWORK"):
                commit_number = instance_patch.iloc[indx]["parents"]
                if commit_number not in 
#----------------------------------------------reopen rate in bypassed patchsed------------------
bypassed_commit_numbers = []  
for index in range (len(smellyListIndex)):
    smelly_index = smellyListIndex[index]
    smelly_patchset = patchsets[smelly_index]
    for indx in range (len(smelly_patchset)):
        smelly_commit = smelly_patchset.iloc[indx]["parents"]
        bypassed_commit_numbers.append(smelly_commit[0])
bypassed_commit_numbers = pd.Series(bypassed_commit_numbers)
bypassed_commit_numbers = bypassed_commit_numbers.value_counts().reset_index()["index"]
bypassed_commit_numbers = bypassed_commit_numbers.tolist()
# counting number of bypassed and reopened commits
bypassed_reopened_commits = []
bypassed_reopened_count = 0 
for index in range (len(bypassed_commit_numbers)):
    bypassed_commit = bypassed_commit_numbers[index]
    for indx in range (len(Reopened_commit_numbers)):
        if (bypassed_commit == Reopened_commit_numbers[indx]):
            bypassed_reopened_count = bypassed_reopened_count + 1
            bypassed_reopened_commits.append(bypassed_commit)
            
bypass_reopen_patchset_count = 0           
for index in range (len(smellyListIndex)):
    smelly_index = smellyListIndex[index]
    smelly_patchset = patchsets[smelly_index]
    for indx in range (len(smelly_patchset)):
        smelly_commit = smelly_patchset.iloc[indx]["parents"]
        for indxx in range (len(bypassed_reopened_commits)):
            if(smelly_commit[0] == bypassed_reopened_commits[indxx]):
                bypass_reopen_patchset_count  = bypass_reopen_patchset_count  + 1

#------------------------------------------bypass and time impact-------------------------------------
seconds_in_day = 24*60*60
bypassedNegative_Time_impact = 0
Time_Impact_Threshold = 2
Average_Review_Completion_Time_Bypassed_reviews = 0
for index in range (len(smellyList)):
    smellypatch_instance = smellyList[index]
    last = smellypatch_instance.iloc[-1]
    if (  last["reviewer.name"] == last["reviewer.name"]  ): # if reviewer name of last row is not Nan 
        if (last["reviewer.name"] not in QT_Bots): # if the reviewer of last task is a Bot 
            smellypatch_instance.drop(smellypatch_instance.tail(1).index,inplace =True)   # drop the last row 
    # substract time stamp of last review operation from first review operation         
    diff = smellypatch_instance.tail(1)["timestamp"].iloc[0] - smellypatch_instance.head(1)["timestamp"].iloc[0]
    diff = diff / seconds_in_day
    Average_Review_Completion_Time_Bypassed_reviews = Average_Review_Completion_Time_Bypassed_reviews + diff
    if(diff > Time_Impact_Threshold ): # if review takes more than one day it considers sleeping review
        bypassedNegative_Time_impact = bypassedNegative_Time_impact + 1 

Average_Review_Completion_Time_Bypassed_reviews = Average_Review_Completion_Time_Bypassed_reviews / len(smellyList)

#------------------------------------------------------bypass smell and ping pong smell impact--------------------------
Ping_Pong_Smell_Threshold = 3
BypassNeg_Ping_Pong_Smell = 0
for index in range (len(smellyList)):
    Ping_Pong_count = 0
    instance_comment =  smellyList[index]
    for indx in range (len(instance_comment)):
        if (instance_comment.iloc[indx]["message"].find('Uploaded') != -1):
            Ping_Pong_count = Ping_Pong_count + 1
    if Ping_Pong_count > Ping_Pong_Smell_Threshold:
        BypassNeg_Ping_Pong_Smell = BypassNeg_Ping_Pong_Smell + 1
                    

                            





















