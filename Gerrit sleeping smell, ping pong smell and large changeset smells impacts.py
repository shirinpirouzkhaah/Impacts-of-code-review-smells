# -*- coding: utf-8 -*-
"""


@author: Shirin 
"""

import pandas as pd
from scipy.stats import norm 
import matplotlib.pyplot as plt
# constants: general
LOG_MESSAGE_TRIGGER_INDEX = 1000
# read jasın eclipse data
pr_data_raw_json = pd.read_json (r'wireshark_2017-01-01.json', lines=True) 

# eliminate the NEW  commits # we dont eliminate abandoned commits to see abandonment impact in the smells
pr_data_normalized = pd.json_normalize(pr_data_raw_json['data'])
d = pr_data_normalized.iloc[0]["status"]
pr_data_normalized = pr_data_normalized[pr_data_normalized.status != 'NEW']
# reseting indices of dataframe 
pr_data_normalized = pr_data_normalized.reset_index()

# reading nested jason to creat comments list of dataframe
pr_data_comments = []
for index,row in pr_data_normalized.iterrows():
    pr_data_comments.append(pd.json_normalize(row['comments']))
    if index % LOG_MESSAGE_TRIGGER_INDEX == 0:
        print(f'{index} comments objects normalized!')
print("\nAll comments normalized! \n")

# reading nested jason to creat patchSets list of dataframe
patchSets = []
for index,row in pr_data_normalized.iterrows():
    patchSets.append(pd.json_normalize(row['patchSets']))
    if index % LOG_MESSAGE_TRIGGER_INDEX == 0:
        print(f'{index} patchsets objects normalized!')

print("\nAll patchsets normalized! \n")

# Projects possible Bots
ECLIPSE_BOTS = {"EGit Bot","JGit Bot","Platform Bot","CI Bot","OSEE Bot","BaSyx Bot","Eclipse Genie", "Trace Compass Bot","JDT Bot","Equinox Bot","CDT Bot","M2E Bot","PDE Bot","Orbit Bot","CBI Bot","EASE Bot","QVT-OML Bot", "Jubula Bot","Linux Tools Bot","Xtext Bot","Sirius Bot","DLTK Bot","StatET Bot","Nebula Bot","SWTBot Bot","EMFStore Bot"}    
WIRESHARK_BOTS = {"Petri Dish Buildbot", "Wireshark code review", "human rights"}
LIBREOFFICE_BOTS = {"Jenkins", "Jenkins CollaboraOffice", "Pootle bot, LibreOﬃciant", "Weblate", "Gerrit Code Review", "JP", "libreoffice lhm"}
QT_BOTS = { "Qt Sanity Bot","Qt CI Bot","Qt Cherry-pick Bot","Qt Submodule Update Bot","Qbs CI Bot","Qt LanceBot","Qt CMake Build Bot","Qt Wayland Headless Tests Bot","Qt Continuous Integration System","Qt Cleanup Bot", "Qt Doc Bot","Qt Forward Merge Bot", "The Qt Project", "Qt3dStudioBot","Qt CI Test Bot","Continuous Integration (KDAB)"}

# This Function gets review data and comments data of each project and return all developer names of that project
def project_developers(comments,data):
    developers = []
    
    for comment_index in range (len(comments)):
        author_name = data.iloc[comment_index]['owner.name']
        if author_name == author_name:
            developers.append(author_name)
        current_pr_comments = comments[comment_index]
        reviewer_names = current_pr_comments["reviewer.name"]
        unique_reviewer_names = reviewer_names.value_counts().reset_index()["index"] #  unique reviewers of each PR
        
        for indx in range (unique_reviewer_names.size):
            if unique_reviewer_names[indx] == unique_reviewer_names[indx]:
                developers.append(unique_reviewer_names[indx])
    
    return developers

developer_names = project_developers(pr_data_comments,pr_data_normalized)
Developers = list(set(developer_names))
# for item in developer_names:
#     if item not in Developers:
#         Developers.append(item)        
Developers = pd.DataFrame(Developers)
Developers.to_csv('devs.txt', sep=' ')


# This function gets review comments data and returns number of iterations and review completion time for each PR
def review_time_iteration(comments, bot_list):
    SECONDS_IN_DAY = 86400
    pr_completion_times = []
    pr_num_of_iterations = []
    
    for index in range (len(comments)): # for each commit 
        num_of_iterations = 0 # number of iterations in each PR 
        current_pr_comments = comments[index] 
        last_comment_message = current_pr_comments.iloc[-1] # last operation of reviewing a PR
        
        if (last_comment_message["reviewer.name"] == last_comment_message["reviewer.name"]  ): # if reviewer name of last row is not Nan 
            if (last_comment_message["reviewer.name"] in WIRESHARK_BOTS): # if the reviewer of last task is a Bot 
                current_pr_comments.drop(current_pr_comments.tail(1).index,inplace =True)  # drop the last row since it is a Bot 
                print("last bot")

        for indx in range (len(current_pr_comments)):
            if (current_pr_comments.iloc[indx]["message"].find('Uploaded') != -1): # each Upload show the start of iteration in the reviewing process 
                num_of_iterations = num_of_iterations + 1
        # substract time stamp of last review operation from first review operation         
        current_pr_completion_time = current_pr_comments.tail(1)["timestamp"].iloc[0] - current_pr_comments.head(1)["timestamp"].iloc[0] # review completion time is the difference of first and last operations' timestamp 
        current_pr_completion_time = current_pr_completion_time / SECONDS_IN_DAY# conver seconds to days 
        pr_completion_times.append(current_pr_completion_time) # dataframe of time of completion of PR reviews 
        pr_num_of_iterations.append(num_of_iterations) # dataframe of iterations in each PR
    
    return pr_completion_times, pr_num_of_iterations

pr_completion_times, pr_num_of_iterations = review_time_iteration(pr_data_comments)

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
for index in range (len(pr_completion_times)):
    if (pr_completion_times[index]>Sleeping_Threshold): # if review takes more than two day, it is sleeping review
        Average_SleepingReview_completion_time  = Average_SleepingReview_completion_time  + pr_completion_times[index]
        sleeping_smell = sleeping_smell + 1
        if pr_data_normalized.iloc[index]["status"] == "ABANDONED": # if it is sleeping review and author abandoned the commit
            Sleeping_Reviews_abandonment_Impact = Sleeping_Reviews_abandonment_Impact + 1
        if pr_num_of_iterations[index] > Ping_Poong_Smell_Uploading_Threshold: # if the number of iterations in the sleeping reviews are more than 3 and ping pong smell occures
            Sleeping_PingPong_smell = Sleeping_PingPong_smell + 1 
        Average_iterations_sleepingrevs = Average_iterations_sleepingrevs + pr_num_of_iterations[index]

    else :
        Average_nonsleepingReviews_completion_time = Average_nonsleepingReviews_completion_time + pr_completion_times[index]
        Nonsleeping_Reviews = Nonsleeping_Reviews + 1
        Average_iterations_Nonsleepingrevs = Average_iterations_Nonsleepingrevs + pr_num_of_iterations[index]
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
for index in range (len(pr_data_comments)):
    commentCount = 0 # number of comments in each review is zero at first, during the process it will be added under some conditions
    LOC_changes = 0 # lines of codes in each PR
    instance_comment = pr_data_comments[index]
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
        if pr_data_normalized.iloc[index]["status"] == "ABANDONED":
            LCHS_abandonment_Impact = LCHS_abandonment_Impact + 1
        # large changeset smell
        if (pr_completion_times[index]>Sleeping_Threshold): # if review takes more than two day, it is sleeping review
            Average_review_completion_time_LCHS  = Average_review_completion_time_LCHS  + pr_completion_times[index]
            LCHS_Time_Impact = LCHS_Time_Impact + 1
        if pr_num_of_iterations[index] > Ping_Poong_Smell_Uploading_Threshold: # ping pong smell
            LCHS_PingPong_smell = LCHS_PingPong_smell + 1  
            Average_LCHS_Iteration = Average_LCHS_Iteration + pr_num_of_iterations[index]
        LCHS_smell = LCHS_smell + 1
        Average_LCHS_Comments = Average_LCHS_Comments + commentCount
        if (commentCount == No_Comment_Threshold): # reviewers negligence impact 
            LCHS_No_Comment_Impact = LCHS_No_Comment_Impact + 1
    if Small_changeset_Threshold < LOC_changes < Large_changeset_Threshold:
        MCHS = MCHS + 1
        Average_MCHS_Comments = Average_MCHS_Comments + commentCount
        Average_MCHS_Iteration = Average_MCHS_Iteration + pr_num_of_iterations[index]
        Average_review_completion_time_MCHS  = Average_review_completion_time_MCHS  + pr_completion_times[index]
    if LOC_changes < Small_changeset_Threshold:
        SCHS = SCHS + 1
        Average_SCHS_Comments= Average_SCHS_Comments + commentCount
        Average_SCHS_Iteration = Average_SCHS_Iteration + pr_num_of_iterations[index]
        Average_review_completion_time_SCHS  = Average_review_completion_time_SCHS  + pr_completion_times[index]
        
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
for index in range (len(pr_data_comments)):
    if pr_num_of_iterations[index] > Ping_Poong_Smell_Uploading_Threshold: # ping pong smell
        Ping_Pong_smell = Ping_Pong_smell + 1
        if pr_data_normalized.iloc[index]["status"] == "ABANDONED":
            Ping_Pong_abandonment_impact = Ping_Pong_abandonment_impact + 1 
        if  (pr_completion_times[index]>Sleeping_Threshold):
            Ping_Pong_Time_Impact = Ping_Pong_Time_Impact + 1
            Average_Ping_Pong_Review_Completion_Time = Average_Ping_Pong_Review_Completion_Time + pr_completion_times[index]
            
Average_Ping_Pong_Review_Completion_Time = Average_Ping_Pong_Review_Completion_Time / Ping_Pong_Time_Impact
            









