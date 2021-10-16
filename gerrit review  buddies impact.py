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
df = pd.read_json (r'eclipse.json', lines=True) 


# eliminate the NEW and ABANDONED commits and only merged commits are consıdered

data = pd.json_normalize(df['data'])
data = data[data.status != 'NEW']
data = data[data.status != 'ABANDONED'] 

# reseting indices of dataframe 
data = data.reset_index()


# reading nested jason (comments column) to creat comments list of dataframe
comments = []
for index,row in data.iterrows():
    comments.append(pd.json_normalize(row['comments']))
    
# concatting all comments to get all reviewer names 
MeregedComments = pd.concat(comments)
names = MeregedComments["reviewer.name"]
# term frequency of reviewer names to have all unique reviewer names 
namelist = names.value_counts() 
# reading nested jason (patchset column) to creat patchSets list of dataframe
patchSets = []
for index,row in data.iterrows():
    patchSets.append(pd.json_normalize(row['patchSets']))

# Projects possible Bots
Eclipse_Bots = {"EGit Bot","JGit Bot","Platform Bot","CI Bot","OSEE Bot","BaSyx Bot","Eclipse Genie", "Trace Compass Bot","JDT Bot","Equinox Bot","CDT Bot","M2E Bot","PDE Bot","Orbit Bot","CBI Bot","EASE Bot","QVT-OML Bot", "Jubula Bot","Linux Tools Bot","Xtext Bot","Sirius Bot","DLTK Bot","StatET Bot","Nebula Bot","SWTBot Bot","EMFStore Bot"}    
Wireshark_Bots = {"Petri Dish Buildbot", "Wireshark code review", "human rights"}
LiberOffice_Bots = {"Jenkins", "Jenkins CollaboraOffice", "Pootle bot, LibreOﬃciant", "Weblate", "Gerrit Code Review", "JP", "libreoffice lhm"}
QT_Bots = { "Qt Sanity Bot","Qt CI Bot","Qt Cherry-pick Bot","Qt Submodule Update Bot","Qbs CI Bot","Qt LanceBot","Qt CMake Build Bot","Qt Wayland Headless Tests Bot","Qt Continuous Integration System","Qt Cleanup Bot", "Qt Doc Bot","Qt Forward Merge Bot", "The Qt Project", "Qt3dStudioBot","Qt CI Test Bot","Continuous Integration (KDAB)"}

#-----------------------------------------------------review buddies smell and time impact--------------------------

def Author_Reviewer_Pairs(comments):
    Seconds_per_day = 86400  
    # list of review completion time of each reviewer while reviewing an anthor's PR,
    # reviewer-author pairs , LOCs of each pair, authors, reviewers and number of comments 
    # that a reviewer gives to an author
    TimeDiff = []
    Author_ReviewerPairs =[]  
    Author_ReviewerPairsLOC =[] 
    authors = []
    reviewers = []
    Pairs_Comments = []
    # for each of commits
    for index in range (len(comments)):
        if (data.iloc[index]['owner.name'] == data.iloc[index]['owner.name']): # if owner name is not Nan, it is equal to itself
            AuthorName = data.iloc[index]['owner.name']
        commentDataframe = comments[index]
        last = commentDataframe.iloc[-1] # last row of commentDataframe as last operation of reviewing a PR
        if (  last["reviewer.name"] == last["reviewer.name"]  ): # if reviewer name of last row is not Nan 
            if (last["reviewer.name"] in Wireshark_Bots): # if the reviewer of last task is a Bot 
                commentDataframe.drop(commentDataframe.tail(1).index,inplace =True)  # drop the last row since it is done by Bot (we are analyzing developers' behaviour.)
        # substract time stamp of last review operation from first review operation         
        diff = commentDataframe.tail(1)["timestamp"].iloc[0] - commentDataframe.head(1)["timestamp"].iloc[0]
        diff = diff / Seconds_per_day # conver seconds to days 
        names = commentDataframe["reviewer.name"]
        namelist = names.value_counts().reset_index()["index"] #  unique reviewers of each commit 
        for indx in range (namelist.size):
            commentCount = 0 # number of comments given to each PR
            LOC_changes = 0 # changed lines of codes in each PR
            # if reviewer name is not Nan and if commit is not self reviewed and if reviewer is not a Bot, we consider these operations in a PR review
            if ( (namelist[indx] == namelist[indx]) and (namelist[indx] != AuthorName) and (namelist[indx] not in Wireshark_Bots) ) :
                tempDf = commentDataframe[commentDataframe['reviewer.name'] == namelist[indx]]
                for indxx in range (len(tempDf)): # this loop calculates number of comments in each PR
                    tempMessage = tempDf.iloc[indxx]["message"]
                    if "comment)" in tempMessage: # 1 comment for reviewer
                        commentCount = commentCount+1
                    elif "comments)" in tempMessage : # several comments
                        commentsString = tempMessage.split("(")[1].split(" comments")[0]
                        if (len(commentsString)<3):
                            commentCount = commentCount + int(commentsString)
                authors.append(AuthorName)
                reviewers.append(namelist[indx])
                Author_ReviewerPairs.append( AuthorName + "-" +namelist[indx]) 
                TimeDiff.append(diff)  # dataframe of time of completion of all commit
                Pairs_Comments.append(commentCount)
                patchSetsDataframe = patchSets[index]
                for indxx in range (len(patchSetsDataframe.index)):
                    if (patchSetsDataframe.iloc[indxx]['kind'] == "REWORK"):
                        LOC_changes =  LOC_changes +  abs(patchSetsDataframe.iloc[indxx]['sizeInsertions'])
                Author_ReviewerPairsLOC.append(LOC_changes) 
        return authors, reviewers, Author_ReviewerPairs, TimeDiff, Pairs_Comments, Author_ReviewerPairsLOC
    
authors, reviewers, Author_ReviewerPairs, TimeDiff, Pairs_Comments, Author_ReviewerPairsLOC = Author_Reviewer_Pairs(comments)


# unique values of pairs and their TF
Pairs = (pd.Series(Author_ReviewerPairs)).value_counts() 
Pairs = Pairs.to_frame()


MainDataframe =[]
for index in range (len(reviewers)):
    MainDataframe.append([Author_ReviewerPairs[index],Author_ReviewerPairsLOC[index],authors[index],reviewers[index],TimeDiff[index],Pairs_Comments[index]]) 
MainDataframe = pd.DataFrame(MainDataframe,columns = ["pairs","LOC","authors","reviewers","time","comments"])


Pair_Average_Review_completion_time = []
for index in range(Pairs.size):
    tempDf = MainDataframe[MainDataframe['pairs'] == Pairs.index[index]] 
    Pair_Average_Review_completion_time.append( np.sum(tempDf["time"])/tempDf.size)
Pair_Average_Review_completion_time = pd.DataFrame(Pair_Average_Review_completion_time)

Pair_Average_Review_completion_time.columns = ["Average_time"]
Pairs.columns = ["freq"]

mean = Pairs.mean()
STD = np.std(Pairs)
reviewBuddies_threshold =  int(mean + STD)
Time_Threshold = 2 # 2 days 
Review_Buddies_Smell = 0
Review_Buddies_Time_impact = 0
Average_Review_Buddies_Time = 0 
for index in range(Pairs.size):
    if Pairs.freq[index] > reviewBuddies_threshold:
        Review_Buddies_Smell = Review_Buddies_Smell + 1
        if Pair_Average_Review_completion_time.Average_time[index] > 2:
            Review_Buddies_Time_impact = Review_Buddies_Time_impact + 1
            Average_Review_Buddies_Time = Average_Review_Buddies_Time + Pair_Average_Review_completion_time.Average_time[index]
            
Average_Review_Buddies_Time = Average_Review_Buddies_Time /Review_Buddies_Smell       
        
#-----------------------------------------------------review buddies smell and reviewer's negligence impact--------------------------

Pair_Average_Comments = []
for index in range(Pairs.size):
    tempDf = MainDataframe[MainDataframe['pairs'] == Pairs.index[index]] 
    Pair_Average_Comments.append( np.sum(tempDf["comments"])/tempDf.size)
Pair_Average_Comments = pd.DataFrame(Pair_Average_Comments)
Pair_Average_Comments.columns = ["Average_number_of_comments"]

Review_Buddies_Smell = 0
Review_Buddies_Reviewer_negligence_impact = 0
Average_Review_Buddies_Comments = 0 
No_Comments_Threshold = 0
for index in range(Pairs.size):
    if Pairs.freq[index] > reviewBuddies_threshold:
        Review_Buddies_Smell = Review_Buddies_Smell + 1
        if Pair_Average_Comments.Average_number_of_comments[index]  ==  No_Comments_Threshold:
            Review_Buddies_Reviewer_negligence_impact = Review_Buddies_Reviewer_negligence_impact + 1
        Average_Review_Buddies_Comments = Average_Review_Buddies_Comments + Pair_Average_Comments.Average_number_of_comments[index]
            
Average_Review_Buddies_Comments =  Average_Review_Buddies_Comments / Review_Buddies_Reviewer_negligence_impact      
        

#---------------------------------------------------------review buddies smell and shared knowledge and file ownership impact--------------------------
Pair_LOC = []
for index in range(Pairs.size):
    tempDf = MainDataframe.loc[MainDataframe['pairs'] == Pairs.index[index]] 
    Pair_LOC.append( np.sum(tempDf["LOC"]))
Pair_LOC = pd.DataFrame(Pair_LOC)
Pair_LOC.columns = ["LOC"]
Pairs.columns = ["freq"]

pairsOver = []
pairsLOC_Over = []
pairsUnder = []
pairsLOC_Under = []
for index in range(Pairs.size):
    if  Pairs.iloc[index]["freq"] > reviewBuddies_threshold and Pairs.iloc[index]["freq"] > 1: # review buddies 
        pairsOver.append(Pairs.iloc[index]["freq"])
        pairsLOC_Over.append(Pair_LOC.iloc[index]["LOC"])
    elif Pairs.iloc[index]["freq"] < reviewBuddies_threshold and Pairs.iloc[index]["freq"] > 1:
        pairsUnder.append(Pairs.iloc[index]["freq"])
        pairsLOC_Under.append(Pair_LOC.iloc[index]["LOC"])
PairCount= 0
for index in range(len(Pairs)):
    if Pairs.iloc[index]["freq"] > 1:
        PairCount = PairCount + 1
        
plt.scatter(pairsOver,pairsLOC_Over )
plt.scatter(pairsUnder,pairsLOC_Under) 
plt.xlabel('occurence frequency of the author-reviewer pairs')
plt.ylabel('total # of lines reviewed (LOC)')
           
            
Average_LOC_Review_Buddies = np.sum(pairsLOC_Over)/len(pairsLOC_Over)
Average_LOC_NonReview_Buddies = np.sum(pairsLOC_Under)/len(pairsLOC_Under)


















