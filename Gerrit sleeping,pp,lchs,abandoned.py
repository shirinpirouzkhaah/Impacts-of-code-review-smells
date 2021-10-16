# -*- coding: utf-8 -*-
"""
@author: Shirin
"""

from datetime import datetime
import pandas as pd
from scipy.stats import norm 
import matplotlib.pyplot as plt

# constants: general
NUM_OF_SECONDS_IN_ONE_DAY = 86400
LOG_MESSAGE_TRIGGER_INDEX = 1000
# read jasın eclipse data
cr_data_raw_json = pd.read_json (r'libreoffice_cr_data.json', lines=True) 

# eliminate the NEW  commits # we dont eliminate abandoned commits to see abandence impact in the smells, so the ratio of each smell may change 
cr_data_normalized_json = pd.json_normalize(cr_data_raw_json['data'])
cr_data_normalized_json = cr_data_normalized_json[cr_data_normalized_json.status != 'NEW']

# reseting indices of dataframe 
cr_data_normalized_json = cr_data_normalized_json.reset_index()

# reading nested jason to creat comments list of dataframe
cr_data_comments = []
for index,row in cr_data_normalized_json.iterrows():
    cr_data_comments.append(pd.json_normalize(row['comments']))
    if index % LOG_MESSAGE_TRIGGER_INDEX == 0:
        print(f'{index} comments objects normalized!')
print("\nAll comments normalized! \n")


# reading nested jason to creat patchSets list of dataframe
cr_data_patchsets = []
for index,row in cr_data_normalized_json.iterrows():
    cr_data_patchsets.append(pd.json_normalize(row['patchSets']))
    if index % LOG_MESSAGE_TRIGGER_INDEX == 0:
        print(f'{index} patchsets objects normalized!')

print("\nAll patchsets normalized! \n")
# print(datetime.now())    

# calculating time of completion of each commit review
# droping commits with Nan reviewer names 
# droping last operation of a review if it is done by a Bot
pr_completion_duration = []
pr_num_of_iterations = []
# number of iterations and review completion time for each PR
for index in range (len(cr_data_comments)): # for each merged commit 
    num_of_iterations = 0 # number of iterations in each PR
    current_pr_comments = cr_data_comments[index]
    last_comment = current_pr_comments.iloc[-1] # last operation of reviewing a PR
    num_of_comments = len(current_pr_comments.index)-1 # number of operations in reviewing a PR
    
    if (  last_comment["reviewer.name"] == last_comment["reviewer.name"]  ): # if reviewer name of last row is not Nan 
        if (last_comment["reviewer.name"].find("Bot") != -1): # if the reviewer of last task is a Bot 
            current_pr_comments.drop(current_pr_comments.tail(1).index,inplace =True)  # drop the last row since it is a Bot 
    
    for indx in range (len(current_pr_comments)):
        if (current_pr_comments.iloc[indx]["message"].find('Uploaded') != -1): # each Upload show the start of iteration in the reviewing process 
            num_of_iterations = num_of_iterations + 1

    # substract time stamp of last review operation from first review operation         
    current_pr_time_difference = current_pr_comments.tail(1)["timestamp"].iloc[0] - current_pr_comments.head(1)["timestamp"].iloc[0]
    current_pr_time_difference = current_pr_time_difference / NUM_OF_SECONDS_IN_ONE_DAY# conver seconds to days 
    pr_completion_duration.append(current_pr_time_difference) # dataframe of time of completion of PR reviews 
    pr_num_of_iterations.append(num_of_iterations) # dataframe of iterations in each PR 


## SLEEPING REVIEWS smell x PING PONG smell ##

# vars + constants: sleeping reviews
SLEEPING_SMELL_THRESHOLD_DAYS = 2 #2 days
sleeping_reviews_count = 0 # number of sleeping reviews
sleeping_reviews_sum_completion_time = 0 # average of time of completion of all sleeping reviews

# vars: non-sleeping reviews
nonsleeping_reviews_count = 0 # number of non-sleeping reviews
nonsleeping_reviews_sum_completion_time = 0 # average of time of completion of all reviews other than sleeping reviews 
nonsleeping_reviews_sum_num_of_iterations = 0 # average number of iterations in Non sleeping reviews

# vars + constants: sleeping reviews + ping pong reviews 
PING_PONG_SMELL_LOOP_THRESHOLD = 3 # after 3 iterations of uploading and getting feedback from reviewers, the ping pong smell occures
sleeping_reviews_sum_num_of_iterations = 0 # average number of iterations in sleeping reviews
sleeping_reviews_with_ping_pong_smell_count = 0 # sleeping reviews with more than 3 iterations 

# vars: sleeping reviews + abandoned reviews
sleeping_reviews_abandoned_count = 0

for index in range (len(pr_completion_duration)):
    if (pr_completion_duration[index]>SLEEPING_SMELL_THRESHOLD_DAYS): # if review takes more than two day, it is sleeping review
        sleeping_reviews_sum_completion_time  = sleeping_reviews_sum_completion_time  + pr_completion_duration[index]
        sleeping_reviews_count =sleeping_reviews_count + 1
        
        if cr_data_normalized_json.iloc[index]["status"] == "ABANDONED":
            sleeping_reviews_abandoned_count = sleeping_reviews_abandoned_count + 1
        
        if pr_num_of_iterations[index] > PING_PONG_SMELL_LOOP_THRESHOLD: # if the number of iterations in the sleeping reviews are more than 3
            sleeping_reviews_with_ping_pong_smell_count = sleeping_reviews_with_ping_pong_smell_count + 1 
        sleeping_reviews_sum_num_of_iterations = sleeping_reviews_sum_num_of_iterations + pr_num_of_iterations[index]

    else :
         nonsleeping_reviews_sum_completion_time = nonsleeping_reviews_sum_completion_time + pr_completion_duration[index]
         nonsleeping_reviews_count = nonsleeping_reviews_count + 1
         nonsleeping_reviews_sum_num_of_iterations = nonsleeping_reviews_sum_num_of_iterations + pr_num_of_iterations[index]
# averages  
sleeping_reviews_mean_completion_time = sleeping_reviews_sum_completion_time / sleeping_reviews_count
nonsleeping_reviews_mean_completion_time  = nonsleeping_reviews_sum_completion_time  / nonsleeping_reviews_count 
sleeping_reviews_mean_num_of_iterations = sleeping_reviews_sum_num_of_iterations / sleeping_reviews_count
nonsleeping_reviews_mean_num_of_iterations = nonsleeping_reviews_sum_num_of_iterations / nonsleeping_reviews_count


# large changeset smell and reviewer's negligence impact, ping pong smell impact and completion time impact
# constants: changeset size and comments
THRESHOLD_FOR_NO_COMMENTS_SMELL = 0 
THRESHOLD_LOC_FOR_LARGE_CHANGESET = 200
THRESHOLD_LOC_FOR_SMALL_CHANGESET = 50

# vars: changeset size counts
large_changeset_reviews_count = 0 #large changesets smell freq 
small_changeset_reviews_count = 0 # frequency of small changesets 
medium_changeset_reviews_count = 0 # frequency of meduim changesets 

# vars: comment counts by changeset size
large_changeset_reviews_no_comment_count = 0 # reviewer's negligence impact in large changesets showed by no comment reviews 
medium_changeset_reviews_no_comment_count =0 # number of no comment reviews for medium changesets
small_changeset_reviews_no_comment_count = 0 # number of no comment reviews for small changesets 
large_changeset_reviews_mean_comment_count = 0 # average number of comments in large changesets 
medium_changeset_reviews_mean_comment_count = 0 # average number of comments in medium changesets 
small_changeset_reviews_mean_comment_count  = 0 # # average number of comments in small changesets 

# vars: ping-pong frequency by changeset size
large_changeset_reviews_with_ping_pong_count = 0 # frequency of ping pong smell in large changesets 
large_changeset_mean_iterations = 0 # average number of iterations in large changesets
medium_changeset_mean_iterations = 0
small_changeset_mean_iterations = 0 

# vars: review completion duration by changeset size
large_changeset_mean_review_completion_time = 0 
medium_changeset_mean_review_completion_time = 0
medium_changeset_mean_review_completion_time = 0
large_changeset_abandoned_review_count = 0  
large_changeset_sleeping_reviews_count = 0

for index in range (len(cr_data_comments)):
    commentCount = 0 # number of comments in each review is zero at first, during the process it will be added under some conditions
    LOC_changes = 0 # lines of codes in each PR
    current_review_comments = cr_data_comments[index]
    current_review_patchsets = cr_data_patchsets[index]
     # calculating number of reviewed changed lines of code
    for indx in range (len(current_review_patchsets.index)):
        if (current_review_patchsets.iloc[indx]['kind'] == "REWORK"): # only REWORK type operations are taken into consideration 
            LOC_changes =  LOC_changes +  abs(current_review_patchsets.iloc[indx]['sizeInsertions']) # only inserted lines are reviewe, deleted lines are reviewed in previous operations, so ther are not considered 
        
        for indx in range (len(current_review_comments)):
            if "comment)" in current_review_comments.iloc[indx]["message"]: # calculating number of comments in each PR mentioned in message field in the data 
                commentCount = commentCount+1
           
            if "comments)" in current_review_comments.iloc[indx]["message"]: 
                commentsString = current_review_comments.iloc[indx]["message"].split("(")[1].split(" comments")[0]
                
                if (len(commentsString)<3):
                    commentCount = commentCount + int(commentsString)
    
    if LOC_changes > THRESHOLD_LOC_FOR_LARGE_CHANGESET:
        if cr_data_normalized_json.iloc[index]["status"] == "ABANDONED":
            large_changeset_abandoned_review_count = large_changeset_abandoned_review_count + 1
        
        # large changeset smell
        large_changeset_reviews_count = large_changeset_reviews_count + 1
        large_changeset_reviews_mean_comment_count = large_changeset_reviews_mean_comment_count + commentCount

        if (pr_completion_duration[index] > SLEEPING_SMELL_THRESHOLD_DAYS): # if review takes more than two day, it is sleeping review
            large_changeset_mean_review_completion_time  = large_changeset_mean_review_completion_time  + pr_completion_duration[index]
            large_changeset_sleeping_reviews_count = large_changeset_sleeping_reviews_count + 1
        
        if pr_num_of_iterations[index] > PING_PONG_SMELL_LOOP_THRESHOLD: # ping pong smell
            large_changeset_reviews_with_ping_pong_count = large_changeset_reviews_with_ping_pong_count + 1  
            large_changeset_mean_iterations = large_changeset_mean_iterations + pr_num_of_iterations[index]
        
        if (commentCount == THRESHOLD_FOR_NO_COMMENTS_SMELL): # reviewers negligence impact 
            large_changeset_reviews_no_comment_count = large_changeset_reviews_no_comment_count + 1
    
    if THRESHOLD_LOC_FOR_SMALL_CHANGESET < LOC_changes < THRESHOLD_LOC_FOR_LARGE_CHANGESET:
        medium_changeset_reviews_count = medium_changeset_reviews_count + 1
        medium_changeset_reviews_mean_comment_count = medium_changeset_reviews_mean_comment_count + commentCount
        medium_changeset_mean_iterations = medium_changeset_mean_iterations + pr_num_of_iterations[index]
        medium_changeset_mean_review_completion_time  = medium_changeset_mean_review_completion_time  + pr_completion_duration[index]
    
    if LOC_changes < THRESHOLD_LOC_FOR_SMALL_CHANGESET:
        small_changeset_reviews_count = small_changeset_reviews_count + 1
        small_changeset_reviews_mean_comment_count= small_changeset_reviews_mean_comment_count + commentCount
        small_changeset_mean_iterations = small_changeset_mean_iterations + pr_num_of_iterations[index]
        medium_changeset_mean_review_completion_time  = medium_changeset_mean_review_completion_time  + pr_completion_duration[index]
        
large_changeset_reviews_mean_comment_count = large_changeset_reviews_mean_comment_count / large_changeset_reviews_count
medium_changeset_reviews_mean_comment_count = medium_changeset_reviews_mean_comment_count / medium_changeset_reviews_count
small_changeset_reviews_mean_comment_count = small_changeset_reviews_mean_comment_count / small_changeset_reviews_count
large_changeset_mean_iterations = large_changeset_mean_iterations / large_changeset_reviews_with_ping_pong_count      
large_changeset_mean_review_completion_time = large_changeset_mean_review_completion_time / large_changeset_sleeping_reviews_count
medium_changeset_mean_iterations = medium_changeset_mean_iterations / medium_changeset_reviews_count
small_changeset_mean_iterations = small_changeset_mean_iterations / small_changeset_reviews_count
medium_changeset_mean_review_completion_time = medium_changeset_mean_review_completion_time / medium_changeset_reviews_count
medium_changeset_mean_review_completion_time = medium_changeset_mean_review_completion_time / small_changeset_reviews_count 
             
# ping pong smell and abandance impact and review completion time impact 
ping_pong_reviews_smell_count = 0
ping_pong_reviews_abandoned_count = 0 
ping_pong_reviews_sleeping_count = 0
ping_pong_reviews_sum_completion_time = 0

for index in range (len(cr_data_comments)):
    
    if pr_num_of_iterations[index] > PING_PONG_SMELL_LOOP_THRESHOLD: # ping pong smell
        ping_pong_reviews_smell_count = ping_pong_reviews_smell_count + 1
        
        if cr_data_normalized_json.iloc[index]["status"] == "ABANDONED":
            ping_pong_reviews_abandoned_count = ping_pong_reviews_abandoned_count + 1 
        
        if  (pr_completion_duration[index] > SLEEPING_SMELL_THRESHOLD_DAYS):
            ping_pong_reviews_sleeping_count = ping_pong_reviews_sleeping_count + 1
            ping_pong_reviews_sum_completion_time = ping_pong_reviews_sum_completion_time + pr_completion_duration[index]
            
ping_pong_reviews_mean_completion_time = ping_pong_reviews_sum_completion_time / ping_pong_reviews_sleeping_count
            









