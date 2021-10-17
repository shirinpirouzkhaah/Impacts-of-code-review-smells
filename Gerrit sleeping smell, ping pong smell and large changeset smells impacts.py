# -*- coding: utf-8 -*-
"""


@author: Shirin 
"""

import json 
import numpy as np
import math
import pandas as pd
from pandas import DataFrame
from scipy.stats import norm 
from pandas.io.json import json_normalize
import matplotlib.pyplot as plt
# read jasın eclipse data
df = pd.read_json (r'wireshark_2017-01-01.json', lines=True) 

# eliminate the NEW  commits # we dont eliminate abandoned commits to see abandonment impact in the smells
data = pd.json_normalize(df['data'])
d = data.iloc[0]["status"]
data = data[data.status != 'NEW']
# reseting indices of dataframe 
data = data.reset_index()

# reading nested jason to creat comments list of dataframe
comments = []
for index,row in data.iterrows():
    comments.append(pd.json_normalize(row['comments']))

# reading nested jason to creat patchSets list of dataframe
patchSets = []
for index,row in data.iterrows():
    patchSets.append(pd.json_normalize(row['patchSets']))
# Projects possible Bots
Eclipse_Bots = {"EGit Bot","JGit Bot","Platform Bot","CI Bot","OSEE Bot","BaSyx Bot","Eclipse Genie", "Trace Compass Bot","JDT Bot","Equinox Bot","CDT Bot","M2E Bot","PDE Bot","Orbit Bot","CBI Bot","EASE Bot","QVT-OML Bot", "Jubula Bot","Linux Tools Bot","Xtext Bot","Sirius Bot","DLTK Bot","StatET Bot","Nebula Bot","SWTBot Bot","EMFStore Bot"}    
Wireshark_Bots = {"Petri Dish Buildbot", "Wireshark code review", "human rights"}
LiberOffice_Bots = {"Jenkins", "Jenkins CollaboraOffice", "Pootle bot, LibreOﬃciant", "Weblate", "Gerrit Code Review", "JP", "libreoffice lhm"}
QT_Bots = { "Qt Sanity Bot","Qt CI Bot","Qt Cherry-pick Bot","Qt Submodule Update Bot","Qbs CI Bot","Qt LanceBot","Qt CMake Build Bot","Qt Wayland Headless Tests Bot","Qt Continuous Integration System","Qt Cleanup Bot", "Qt Doc Bot","Qt Forward Merge Bot", "The Qt Project", "Qt3dStudioBot","Qt CI Test Bot","Continuous Integration (KDAB)"}

# This Function gets review data and comments data of each project and return all developer names of that project
def Project_Developers(comments,data):
    Devs = []
    for index in range (len(comments)):
        AuthorName = data.iloc[index]['owner.name']
        if AuthorName == AuthorName:
            Devs.append(AuthorName)
        commentDataframe = comments[index]
        names = commentDataframe["reviewer.name"]
        namelist = names.value_counts().reset_index()["index"] #  unique reviewers of each PR
        for indx in range (namelist.size):
            if namelist[indx] == namelist[indx]:
                Devs.append(namelist[indx])
    return Devs

Devs = Project_Developers(comments,data)
Developers = []
for item in Devs:
    if item not in Developers:
        Developers.append(item)        
Developers = pd.DataFrame(Developers)
Developers.to_csv('devs.txt', sep=' ')


# This function gets review comments data and returns number of iterations and review completion time for each PR
def Review_Time_Iteration(comments):
    Seconds_In_Day = 86400
    TimeDiff = []
    PR_Iterations = []
    for index in range (len(comments)): # for each commit 
        index = 0 
        Iterations = 0 # number of iterations in each PR 
        commentDataframe = comments[index] 
        last = commentDataframe.iloc[-1] # last operation of reviewing a PR
        if (  last["reviewer.name"] == last["reviewer.name"]  ): # if reviewer name of last row is not Nan 
            if (last["reviewer.name"] in Wireshark_Bots): # if the reviewer of last task is a Bot 
                commentDataframe.drop(commentDataframe.tail(1).index,inplace =True)  # drop the last row since it is a Bot 
                print("last bot")
        for indx in range (len(commentDataframe)):
            if (commentDataframe.iloc[indx]["message"].find('Uploaded') != -1): # each Upload show the start of iteration in the reviewing process 
                Iterations = Iterations + 1
        # substract time stamp of last review operation from first review operation         
        diff = commentDataframe.tail(1)["timestamp"].iloc[0] - commentDataframe.head(1)["timestamp"].iloc[0] # review completion time is the difference of first and last operations' timestamp 
        diff = diff / Seconds_In_Day# conver seconds to days 
        TimeDiff.append(diff) # dataframe of time of completion of PR reviews 
        PR_Iterations.append(Iterations) # dataframe of iterations in each PR
    return TimeDiff, PR_Iterations

TimeDiff, PR_Iterations = Review_Time_Iteration(comments)

# sleeping reviews and ping pong smell impact     
Average_SleepingReview_completion_time = 0 # average of time of completion of all sleeping reviews
Average_nonsleepingReviews_completion_time = 0 # average of time of completion of all reviews other than sleeping reviews 
sleeping_smell = 0 # number of sleeping reviews
Nonsleeping_Reviews = 0 # number of non-sleeping reviews
Sleeping_Threshold = 2 #2 days
Ping_Poong_Smell_Uploading_Threshold = 3 # after 3 iterations of uploading and getting feedback from reviewers, the ping pong smell occures
Sleeping_PingPong_smell = 0 # sleeping reviews with more than 3 iterations 
Average_iterations_sleepingrevs = 0 # average number of iterations in sleeping reviews
Average_iterations_Nonsleepingrevs = 0 # average number of iterations in Non sleeping reviews
Sleeping_Reviews_abandonment_Impact = 0
for index in range (len(TimeDiff)):
    if (TimeDiff[index]>Sleeping_Threshold): # if review takes more than two day, it is sleeping review
        Average_SleepingReview_completion_time  = Average_SleepingReview_completion_time  + TimeDiff[index]
        sleeping_smell = sleeping_smell + 1
        if data.iloc[index]["status"] == "ABANDONED": # if it is sleeping review and author abandoned the commit
            Sleeping_Reviews_abandonment_Impact = Sleeping_Reviews_abandonment_Impact + 1
        if PR_Iterations[index] > Ping_Poong_Smell_Uploading_Threshold: # if the number of iterations in the sleeping reviews are more than 3 and ping pong smell occures
            Sleeping_PingPong_smell = Sleeping_PingPong_smell + 1 
        Average_iterations_sleepingrevs = Average_iterations_sleepingrevs + PR_Iterations[index]

    else :
        Average_nonsleepingReviews_completion_time = Average_nonsleepingReviews_completion_time + TimeDiff[index]
        Nonsleeping_Reviews = Nonsleeping_Reviews + 1
        Average_iterations_Nonsleepingrevs = Average_iterations_Nonsleepingrevs + PR_Iterations[index]
# averages  
Average_SleepingReview_completion_time = Average_SleepingReview_completion_time / sleeping_smell
Average_nonsleepingReviews_completion_time  = Average_nonsleepingReviews_completion_time  / Nonsleeping_Reviews 
Average_iterations_sleepingrevs = Average_iterations_sleepingrevs / sleeping_smell
Average_iterations_Nonsleepingrevs = Average_iterations_Nonsleepingrevs / Nonsleeping_Reviews

# large changeset smell and reviewer's negligence impact, ping pong smell impact and completion time impact
LCHS_smell = 0 #large changesets smell freq 
SCHS = 0 # frequency of small changesets 
MCHS = 0 # frequency of meduim changesets 
LCHS_No_Comment_Impact = 0 # reviewer's negligence impact in large changesets showed by no comment reviews 
MCHS_No_Comment_Impact =0 # number of no comment reviews for medium changesets
SCHS_No_Comment_Impact = 0 # number of no comment reviews for small changesets 
Average_LCHS_Comments = 0 # average number of comments in large changesets 
Average_MCHS_Comments = 0 # average number of comments in medium changesets 
Average_SCHS_Comments  = 0 # # average number of comments in small changesets 
No_Comment_Threshold = 0 
Large_changeset_Threshold = 200
Small_changeset_Threshold = 50
LCHS_PingPong_smell = 0 # frequency of ping pong smell in large changesets 
Average_LCHS_Iteration = 0 # average number of iterations in large changesets
Average_MCHS_Iteration = 0
Average_SCHS_Iteration = 0 
LCHS_Time_Impact = 0
Average_review_completion_time_LCHS = 0 
LCHS_abandonment_Impact = 0  
Average_review_completion_time_MCHS = 0
Average_review_completion_time_SCHS = 0
for index in range (len(comments)):
    commentCount = 0 # number of comments in each review is zero at first, during the process it will be added under some conditions
    LOC_changes = 0 # lines of codes in each PR
    instance_comment = comments[index]
    patchSetsDataframe = patchSets[index]
     # calculating number of reviewed changed lines of code
    for indx in range (len(patchSetsDataframe.index)):
        if (patchSetsDataframe.iloc[indx]['kind'] == "REWORK"): # only REWORK type operations are taken into consideration 
            LOC_changes =  LOC_changes +  abs(patchSetsDataframe.iloc[indx]['sizeInsertions']) # only inserted lines are reviewe, deleted lines are reviewed in previous operations, so ther are not considered 
        for indx in range (len(instance_comment)):
            if "comment)" in instance_comment.iloc[indx]["message"]: # calculating number of comments in each PR mentioned in message field in the data 
                commentCount = commentCount+1
            if "comments)" in instance_comment.iloc[indx]["message"]: 
                commentsString = instance_comment.iloc[indx]["message"].split("(")[1].split(" comments")[0]
                if (len(commentsString)<3):
                    commentCount = commentCount + int(commentsString)
    if LOC_changes > Large_changeset_Threshold:
        if data.iloc[index]["status"] == "ABANDONED":
            LCHS_abandonment_Impact = LCHS_abandonment_Impact + 1
        # large changeset smell
        if (TimeDiff[index]>Sleeping_Threshold): # if review takes more than two day, it is sleeping review
            Average_review_completion_time_LCHS  = Average_review_completion_time_LCHS  + TimeDiff[index]
            LCHS_Time_Impact = LCHS_Time_Impact + 1
        if PR_Iterations[index] > Ping_Poong_Smell_Uploading_Threshold: # ping pong smell
            LCHS_PingPong_smell = LCHS_PingPong_smell + 1  
            Average_LCHS_Iteration = Average_LCHS_Iteration + PR_Iterations[index]
        LCHS_smell = LCHS_smell + 1
        Average_LCHS_Comments = Average_LCHS_Comments + commentCount
        if (commentCount == No_Comment_Threshold): # reviewers negligence impact 
            LCHS_No_Comment_Impact = LCHS_No_Comment_Impact + 1
    if Small_changeset_Threshold < LOC_changes < Large_changeset_Threshold:
        MCHS = MCHS + 1
        Average_MCHS_Comments = Average_MCHS_Comments + commentCount
        Average_MCHS_Iteration = Average_MCHS_Iteration + PR_Iterations[index]
        Average_review_completion_time_MCHS  = Average_review_completion_time_MCHS  + TimeDiff[index]
    if LOC_changes < Small_changeset_Threshold:
        SCHS = SCHS + 1
        Average_SCHS_Comments= Average_SCHS_Comments + commentCount
        Average_SCHS_Iteration = Average_SCHS_Iteration + PR_Iterations[index]
        Average_review_completion_time_SCHS  = Average_review_completion_time_SCHS  + TimeDiff[index]
        
Average_LCHS_Comments = Average_LCHS_Comments / LCHS_smell
Average_MCHS_Comments = Average_MCHS_Comments / MCHS
Average_SCHS_Comments = Average_SCHS_Comments / SCHS
Average_LCHS_Iteration = Average_LCHS_Iteration / LCHS_PingPong_smell      
Average_review_completion_time_LCHS = Average_review_completion_time_LCHS / LCHS_Time_Impact
Average_MCHS_Iteration = Average_MCHS_Iteration / MCHS
Average_SCHS_Iteration = Average_SCHS_Iteration / SCHS
Average_review_completion_time_MCHS = Average_review_completion_time_MCHS / MCHS
Average_review_completion_time_SCHS = Average_review_completion_time_SCHS / SCHS 
             
# ping pong smell and abandance impact and review completion time impact 
Ping_Pong_smell = 0
Ping_Pong_abandonment_impact = 0 
Ping_Pong_Time_Impact = 0
Average_Ping_Pong_Review_Completion_Time = 0
for index in range (len(comments)):
    if PR_Iterations[index] > Ping_Poong_Smell_Uploading_Threshold: # ping pong smell
        Ping_Pong_smell = Ping_Pong_smell + 1
        if data.iloc[index]["status"] == "ABANDONED":
            Ping_Pong_abandonment_impact = Ping_Pong_abandonment_impact + 1 
        if  (TimeDiff[index]>Sleeping_Threshold):
            Ping_Pong_Time_Impact = Ping_Pong_Time_Impact + 1
            Average_Ping_Pong_Review_Completion_Time = Average_Ping_Pong_Review_Completion_Time + TimeDiff[index]
            
Average_Ping_Pong_Review_Completion_Time = Average_Ping_Pong_Review_Completion_Time / Ping_Pong_Time_Impact
            









