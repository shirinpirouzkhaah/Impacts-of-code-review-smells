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

#review data                   
df = pd.read_json("eclipse.json", lines=True)

reviewdata = df

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
        if (instance_comment.iloc[0]['reviewer.name'] ==instance_comment.iloc[0]['reviewer.name'] and instance_comment.iloc[0]['reviewer.name'] not in Eclipse_Bots): # if owner name(who uploaded the patch, first row of instance comment ) is not Nan and Bot
            AuthorName = instance_comment.iloc[0]['reviewer.name']
        for indx in range (1,len(instance_comment)):
            if (len(AuthorName) > 0 and instance_comment.iloc[indx]['reviewer.name'] == instance_comment.iloc[indx]['reviewer.name'] and instance_comment.iloc[indx]["reviewer.name"] != AuthorName and instance_comment.iloc[indx]["reviewer.name"] not in Eclipse_Bots):
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
listWithReject, smellyList, smellyListIndex =  bypassNegative_rev(comments)

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
#------------------------------------------------------bypass smell and reviewer's negligence--------------------------
Bypass_ReviewerNegligence_Impact = 0
Average_comments_bypassedReviews = 0
for index in range (len(smellyList)):
    instance_comment =  smellyList[index]
    commentCount = 0
    for indxx in range (len(instance_comment)): # this loop calculates number of comments in each PR
        tempMessage = instance_comment.iloc[indxx]["message"]
        if "comment)" in tempMessage: # 1 comment for reviewer
            commentCount = commentCount+1
        elif "comments)" in tempMessage : # several comments
            commentsString = tempMessage.split("(")[1].split(" comments")[0]
            if (len(commentsString)<3):
                commentCount = commentCount + int(commentsString)
    Average_comments_bypassedReviews = Average_comments_bypassedReviews + commentCount
    if commentCount == 0:
        Bypass_ReviewerNegligence_Impact = Bypass_ReviewerNegligence_Impact + 1
        
Average_comments_bypassedReviews = Average_comments_bypassedReviews / len(smellyList)





