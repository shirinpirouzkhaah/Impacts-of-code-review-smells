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

# constants
SECONDS_PER_DAY =  86400
NO_COMMENTS_SMELL_COMMENTS_THRESHOLD = 0

# read json oss code review/pull request data
cr_data_raw_json = pd.read_json (r'libreoffice_cr_data.json', lines=True) 

# eliminate the NEW and ABANDONED commits (only successfully merged commits considered)
cr_data_normalized = pd.json_normalize(cr_data_raw_json['data'])
cr_data_normalized = cr_data_normalized[cr_data_normalized.status != 'NEW']
cr_data_normalized = cr_data_normalized[cr_data_normalized.status != 'ABANDONED'] 

# reseting indices of dataframe 
cr_data_normalized = cr_data_normalized.reset_index()

# intialize comments and patchsets data structures
comments = []
for index,row in cr_data_normalized.iterrows():
    comments.append(pd.json_normalize(row['comments']))
    
# convert from individual table per comment object to unified normalized table with 1 row per object 
comments_concat = pd.concat(comments)
names = comments_concat["reviewer.name"]
# term frequency of reviewer names to have all unique reviewer names 
unique_names_in_current_pr_comments = names.value_counts() 

# read and normalize patchsets data
patchsets = []
for index,row in cr_data_normalized.iterrows():
    patchsets.append(pd.json_normalize(row['patchSets']))


#-----------------------------------------------------review buddies smell and time impact--------------------------
# calculating time of completion of each commit review
pr_completion_times = []
    
# empity list of revıewer-author pairs , LOCs of each pair authors, revıewers, and their indices
# empity list of kinds of operations in each commit review
author_reviewer_pairs =[]  
author_names = []
reviewer_names = []
lines_of_code_per_author_reviewer_pair =[] 
num_of_comments_per_reviewer_author_pair = []


for index in range (len(comments)):
    if (cr_data_normalized.iloc[index]['owner.name'] == cr_data_normalized.iloc[index]['owner.name']): # if owner name is not Nan, it is equal to itself
        author_name = cr_data_normalized.iloc[index]['owner.name']
    
    current_pr_comments = comments[index]
    last_comment_message = current_pr_comments.iloc[-1] # last row of commentDataframe
    num_of_messages_in_current_pr_comments = len(current_pr_comments.index)-1
    
    if (last_comment_message["reviewer.name"] == last_comment_message["reviewer.name"]  ): # if reviewer name of last row is not Nan 
        if (last_comment_message["reviewer.name"].find("Bot") != -1): # if the reviewer of last task is a Bot 
            current_pr_comments.drop(current_pr_comments.tail(1).index,inplace =True)   # drop the last row 
    
    # calculate completion time = last commment time - first comment time      
    current_pr_completion_time = current_pr_comments.tail(1)["timestamp"].iloc[0] - current_pr_comments.head(1)["timestamp"].iloc[0]
    current_pr_completion_time = current_pr_completion_time / SECONDS_PER_DAY # convert seconds to days 
    names = current_pr_comments["reviewer.name"]
    unique_names_in_current_pr_comments = names.value_counts().reset_index()["index"] #  unique reviewers of each commit review
    
    for name_index in range (unique_names_in_current_pr_comments.size):
        num_of_comments = 0
        num_of_lines_changed = 0
        # if reviewer name is not Nan and if commit is not self reviewed and if reviewer is not a Bot append items to corresponding lists
        if ( (unique_names_in_current_pr_comments[name_index] == unique_names_in_current_pr_comments[name_index]) and (unique_names_in_current_pr_comments[name_index] != author_name) and (unique_names_in_current_pr_comments[name_index].find("Bot") == -1) and (unique_names_in_current_pr_comments[name_index].find("code") == -1) and (unique_names_in_current_pr_comments[name_index].find("review") == -1) and (unique_names_in_current_pr_comments[name_index].find("Buildbot") == -1) ) :
            messages_in_comments_by_current_name = current_pr_comments[current_pr_comments['reviewer.name'] == unique_names_in_current_pr_comments[name_index]]
    
            for comment_count_calc_index in range (len(messages_in_comments_by_current_name)):
                current_message = messages_in_comments_by_current_name.iloc[comment_count_calc_index]["message"]
                
                if "comment)" in current_message: # 1 comment for reviewer
                    num_of_comments = num_of_comments + 1
                
                elif "comments)" in current_message : # several comments
                    comments_string = current_message.split("(")[1].split(" comments")[0]
    
                    if (len(comments_string) < 3):
                        num_of_comments = num_of_comments + int(comments_string)
                    else:
                        print(comments_string)
                elif (name_index < 100):
                    print(current_message)
    
            author_names.append(author_name)
            reviewer_names.append(unique_names_in_current_pr_comments[name_index])
            author_reviewer_pairs.append( author_name + "-" + unique_names_in_current_pr_comments[name_index]) 
            pr_completion_times.append(current_pr_completion_time)  # dataframe of time of completion of all merged commit
            num_of_comments_per_reviewer_author_pair.append(num_of_comments)
            
            current_patchset = patchsets[index]
            for patchset_row_index in range (len(current_patchset.index)):
                if (current_patchset.iloc[patchset_row_index]['kind'] == "REWORK"):
                    num_of_lines_changed =  num_of_lines_changed +  abs(current_patchset.iloc[patchset_row_index]['sizeInsertions'])
    
            lines_of_code_per_author_reviewer_pair.append(num_of_lines_changed) 

# unique values of pairs and their TF
author_reviewer_pairs = (pd.Series(author_reviewer_pairs)).value_counts() 
author_reviewer_pairs = author_reviewer_pairs.to_frame()

combined_data_table = []
for combined_data_table_index in range (len(reviewer_names)):
    combined_data_table.append([author_reviewer_pairs[combined_data_table_index],lines_of_code_per_author_reviewer_pair[combined_data_table_index],author_names[combined_data_table_index],reviewer_names[combined_data_table_index],pr_completion_times[combined_data_table_index],num_of_comments_per_reviewer_author_pair[combined_data_table_index]]) 

combined_data_table = pd.DataFrame(combined_data_table,columns = ["pairs","LOC","authors","reviewers","time","comments"])

reviewer_author_mean_completion_time = []
for index in range(author_reviewer_pairs.size):
    messages_in_comments_by_current_name = combined_data_table[combined_data_table['pairs'] == author_reviewer_pairs.index[index]] 
    reviewer_author_mean_completion_time.append( np.sum(messages_in_comments_by_current_name["time"])/messages_in_comments_by_current_name.size)

reviewer_author_mean_completion_time = pd.DataFrame(reviewer_author_mean_completion_time)
reviewer_author_mean_completion_time.columns = ["average_time"]
author_reviewer_pairs.columns = ["freq"]

mean = author_reviewer_pairs.mean()
standard_deviation = np.std(author_reviewer_pairs)
review_buddies_smell_threshold =  int(mean + standard_deviation)
sleeping_review_time_threshold = 2 # 2 days 
review_buddies_smell_count = 0
review_buddies_with_sleeping_smell = 0
review_buddies_mean_review_completion_time = 0 

for index in range(author_reviewer_pairs.size):
    if author_reviewer_pairs.freq[index] > review_buddies_smell_threshold:
        review_buddies_smell_count = review_buddies_smell_count + 1

        if reviewer_author_mean_completion_time.average_time[index] > 2:
            review_buddies_with_sleeping_smell = review_buddies_with_sleeping_smell + 1
            review_buddies_mean_review_completion_time = review_buddies_mean_review_completion_time + reviewer_author_mean_completion_time.average_time[index]
            
review_buddies_mean_review_completion_time = review_buddies_mean_review_completion_time /review_buddies_smell_count       
        
#-----------------------------------------------------review buddies smell and reviewer's negligence impact--------------------------

reviewer_author_mean_number_of_comments = []
for index in range(author_reviewer_pairs.size):
    messages_in_comments_by_current_name = combined_data_table[combined_data_table['pairs'] == author_reviewer_pairs.index[index]] 
    reviewer_author_mean_number_of_comments.append( np.sum(messages_in_comments_by_current_name["comments"])/messages_in_comments_by_current_name.size)

reviewer_author_mean_number_of_comments = pd.DataFrame(reviewer_author_mean_number_of_comments)
reviewer_author_mean_number_of_comments.columns = ["average_number_of_comments"]

review_buddies_smell_count = 0
review_buddies_smell_reviewer_negligence_count = 0
review_buddies_mean_num_of_comments = 0 

for index in range(author_reviewer_pairs.size):
    if author_reviewer_pairs.freq[index] > review_buddies_smell_threshold:
        review_buddies_smell_count = review_buddies_smell_count + 1

        if reviewer_author_mean_number_of_comments.average_number_of_comments[index] > NO_COMMENTS_SMELL_COMMENTS_THRESHOLD:
            review_buddies_smell_reviewer_negligence_count = review_buddies_smell_reviewer_negligence_count + 1
            review_buddies_mean_num_of_comments = review_buddies_mean_num_of_comments + reviewer_author_mean_number_of_comments.average_number_of_comments[index]
            
review_buddies_mean_num_of_comments =  review_buddies_mean_num_of_comments / review_buddies_smell_reviewer_negligence_count      
        
#---------------------------------------------------------review buddies smell and shared knowledge and file ownership impact--------------------------
reviewer_author_lines_of_code = []
for index in range(author_reviewer_pairs.size):
    messages_in_comments_by_current_name = combined_data_table.loc[combined_data_table['pairs'] == author_reviewer_pairs.index[index]]
    reviewer_author_lines_of_code.append( np.sum(messages_in_comments_by_current_name["LOC"]))

reviewer_author_lines_of_code = pd.DataFrame(reviewer_author_lines_of_code)
reviewer_author_lines_of_code.columns = ["LOC"]
author_reviewer_pairs.columns = ["freq"]

author_reviewer_pairs_review_buddies = []
lines_of_code_of_review_buddies = []
author_reviewer_non_review_buddies = []
lines_of_code_of_non_review_buddies = []

for index in range(author_reviewer_pairs.size):
    if author_reviewer_pairs.iloc[index]["freq"] > review_buddies_smell_threshold: # review buddies 
        author_reviewer_pairs_review_buddies.append(author_reviewer_pairs.iloc[index]["freq"])
        lines_of_code_of_review_buddies.append(reviewer_author_lines_of_code.iloc[index]["LOC"])
    else:
        author_reviewer_non_review_buddies.append(author_reviewer_pairs.iloc[index]["freq"])
        lines_of_code_of_non_review_buddies.append(reviewer_author_lines_of_code.iloc[index]["LOC"])

plt.scatter(author_reviewer_pairs_review_buddies,lines_of_code_of_review_buddies )
plt.scatter(author_reviewer_non_review_buddies,lines_of_code_of_non_review_buddies)
plt.xlabel('occurence frequency of the author-reviewer pairs')
plt.ylabel('total # of lines reviewed (LOC)')
plt.show()
           
review_buddies_mean_lines_of_code = np.sum(lines_of_code_of_review_buddies)/len(lines_of_code_of_review_buddies)
non_review_buddies_mean_lines_of_code = np.sum(lines_of_code_of_non_review_buddies)/len(lines_of_code_of_non_review_buddies)