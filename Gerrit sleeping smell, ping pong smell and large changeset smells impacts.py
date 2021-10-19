# -*- coding: utf-8 -*-
"""
@author: Shirin 
"""

import pandas as pd
from scipy.stats import norm
import matplotlib.pyplot as plt
import pprint as pp

# constants: general
LOG_MESSAGE_TRIGGER_INDEX = 1000
# read jasın eclipse data
pr_data_raw_json = pd.read_json(r"eclipse_cr_data.json", lines=True)

# eliminate the NEW  commits # we dont eliminate abandoned commits to see abandonment impact in the smells
pr_data_normalized = pd.json_normalize(pr_data_raw_json["data"])
d = pr_data_normalized.iloc[0]["status"]
pr_data_normalized = pr_data_normalized[pr_data_normalized.status != "NEW"]
# reseting indices of dataframe
pr_data_normalized = pr_data_normalized.reset_index()

# reading nested jason to creat comments list of dataframe
pr_data_comments = []
for index, row in pr_data_normalized.iterrows():
    pr_data_comments.append(pd.json_normalize(row["comments"]))
    if index % LOG_MESSAGE_TRIGGER_INDEX == 0:
        print(f"{index} comments objects normalized!")

print("\nAll comments normalized! \n")

# reading nested jason to creat patchSets list of dataframe
patchSets = []
for index, row in pr_data_normalized.iterrows():
    patchSets.append(pd.json_normalize(row["patchSets"]))
    if index % LOG_MESSAGE_TRIGGER_INDEX == 0:
        print(f"{index} patchsets objects normalized!")

print("\nAll patchsets normalized! \n")

# This Function gets review data and comments data of each project and return all developer names of that project
def project_developers(comments, data):
    developers = []

    for comment_index in range(len(comments)):
        author_name = data.iloc[comment_index]["owner.name"]
        if author_name == author_name:
            developers.append(author_name)

        current_pr_comments = comments[comment_index]
        reviewer_names = current_pr_comments["reviewer.name"]
        unique_reviewer_names = reviewer_names.value_counts().reset_index()[
            "index"
        ]  #  unique reviewers of each PR

        for indx in range(unique_reviewer_names.size):
            if unique_reviewer_names[indx] == unique_reviewer_names[indx]:
                developers.append(unique_reviewer_names[indx])

    return developers


developer_names = project_developers(pr_data_comments, pr_data_normalized)
developer_names_unique = list(set(developer_names))
developer_names_unique = pd.DataFrame(developer_names_unique)
developer_names_unique.to_csv("devs.txt", sep=" ")


# This function gets review comments data and returns number of iterations and review completion time for each PR
def review_time_iteration(comments, bot_list):
    SECONDS_IN_DAY = 86400
    pr_completion_times = []
    pr_num_of_iterations = []

    for index in range(len(comments)):  # for each commit
        num_of_iterations = 0  # number of iterations in each PR
        current_pr_comments = comments[index]
        last_comment_message = current_pr_comments.iloc[
            -1
        ]  # last operation of reviewing a PR

        if (
            last_comment_message["reviewer.name"]
            == last_comment_message["reviewer.name"]
        ):
            if last_comment_message["reviewer.name"] in ECLIPSE_BOTS:
                current_pr_comments.drop(
                    current_pr_comments.tail(1).index, inplace=True
                )

        for indx in range(len(current_pr_comments)):
            if (
                current_pr_comments.iloc[indx]["message"].find("Uploaded") != -1
            ):  # each Upload show the start of iteration in the reviewing process
                num_of_iterations = num_of_iterations + 1

        # substract time stamp of last review operation from first review operation
        current_pr_completion_time = (
            current_pr_comments.tail(1)["timestamp"].iloc[0]
            - current_pr_comments.head(1)["timestamp"].iloc[0]
        )  # review completion time is the difference of first and last operations' timestamp
        current_pr_completion_time = (
            current_pr_completion_time / SECONDS_IN_DAY
        )  # conver seconds to days
        pr_completion_times.append(
            current_pr_completion_time
        )  # dataframe of time of completion of PR reviews
        pr_num_of_iterations.append(
            num_of_iterations
        )  # dataframe of iterations in each PR
    
        if index % LOG_MESSAGE_TRIGGER_INDEX == 0:
            print(f"{index} PRs processed for completion times and number of iterations")

    return pr_completion_times, pr_num_of_iterations


pr_completion_times, pr_num_of_iterations = review_time_iteration(
    pr_data_comments, ECLIPSE_BOTS
)

# sleeping reviews and ping pong smell impact

# constants: sleeping reviews x ping pong
SLEEPING_REVIEWS_THRESHOLD_DAYS = 2  # 2 days
PING_PONG_SMELL_LOOP_THRESHOLD = 3

# var: declarations

sleeping = {}
nonsleeping = {}

# vars: sleeping reviews general
sleeping['reviews_count'] = 0  # number of sleeping reviews
nonsleeping['reviews_count'] = 0  # number of non-sleeping reviews
sleeping['reviews_mean_completion_time'] = 0
nonsleeping['reviews_mean_completion_time'] = 0

# vars: sleeping reviews x ping pong
sleeping['reviews_with_ping_pong_count'] = 0
sleeping['reviews_mean_iterations'] = 0  
nonsleeping['reviews_mean_iterations'] = 0

# vars: sleeping review x abandoned
sleeping['reviews_abandoned_count'] = 0
for index in range(len(pr_completion_times)):
    if pr_completion_times[index] > SLEEPING_REVIEWS_THRESHOLD_DAYS:
        sleeping['reviews_mean_completion_time'] = (
            sleeping['reviews_mean_completion_time'] + pr_completion_times[index]
        )
        sleeping['reviews_count'] = sleeping['reviews_count'] + 1

        if pr_data_normalized.iloc[index]["status"] == "ABANDONED":
            sleeping['reviews_abandoned_count'] = sleeping['reviews_abandoned_count'] + 1

        if (
            pr_num_of_iterations[index] > PING_PONG_SMELL_LOOP_THRESHOLD
        ):  # if the number of iterations in the sleeping reviews are more than 3 and ping pong smell occures
            sleeping['reviews_with_ping_pong_count'] = (
                sleeping['reviews_with_ping_pong_count'] + 1
            )
        sleeping['reviews_mean_iterations'] = (
            sleeping['reviews_mean_iterations'] + pr_num_of_iterations[index]
        )

    else:
        nonsleeping['reviews_mean_completion_time'] = (
            nonsleeping['reviews_mean_completion_time'] + pr_completion_times[index]
        )
        nonsleeping['reviews_count'] = nonsleeping['reviews_count'] + 1
        nonsleeping['reviews_mean_iterations'] = (
            nonsleeping['reviews_mean_iterations'] + pr_num_of_iterations[index]
        )

    if index % LOG_MESSAGE_TRIGGER_INDEX == 0:
        print(f"{index} PRs processed for sleeping review and impacts")
# averages

sleeping['reviews_mean_completion_time'] = (
    sleeping['reviews_mean_completion_time'] / sleeping['reviews_count']
)
nonsleeping['reviews_mean_completion_time'] = (
    nonsleeping['reviews_mean_completion_time'] / nonsleeping['reviews_count']
)
sleeping['reviews_mean_iterations'] = (
    sleeping['reviews_mean_iterations'] / sleeping['reviews_count']
)
nonsleeping['reviews_mean_iterations'] = (
    nonsleeping['reviews_mean_iterations'] / nonsleeping['reviews_count']
)

# large changeset smell and reviewer's negligence impact, ping pong smell impact and completion time impact

# constants: changeset size
NO_COMMENT_THRESHOLD = 0
LARGE_CHANGESET_THRESHOLD_LINES = 200
SMALL_CHANGESET_THRESHOLD_LINES = 50

# var declarations
large_changeset = {}
medium_changeset = {}
small_changeset = {}

# vars: changeset size general
large_changeset['reviews_count'] = 0  # large changesets smell freq
small_changeset['reviews_count'] = 0  # frequency of small changesets
medium_changeset['reviews_count'] = 0  # frequency of meduim changesets

# vars: changeset size x (no) comments
large_changeset['no_comment_reviews_count'] = 0
medium_changeset['no_comment_reviews_count'] = 0
small_changeset['no_comment_reviews_count'] = 0
large_changeset['reviews_mean_comments'] = 0
medium_changeset['reviews_mean_comments'] = 0
small_changeset['reviews_mean_comments'] = 0

# vars: changeset size x ping pong
large_changeset['ping_pong_reviews_count'] = 0
large_changeset['reviews_mean_iterations'] = 0
medium_changeset['reviews_mean_iterations'] = 0
small_changeset['reviews_mean_iterations'] = 0

# vars: changeset size x sleeping
large_changeset['reviews_sleeping_count'] = 0
large_changeset['reviews_mean_completion_time'] = 0
medium_changeset['reviews_mean_completion_time'] = 0
small_changeset['mean_completion_time'] = 0

# vars: changeset size x abandoned
large_changeset['reviews_abandoned_count'] = 0

for index in range(len(pr_data_comments)):
    comment_count = 0  # number of comments in each review is zero at first, during the process it will be added under some conditions
    lines_changed = 0  # lines of codes in each PR
    pr_comments_instance = pr_data_comments[index]
    pr_patchset = patchSets[index]

    # calculating number of reviewed changed lines of code
    for indx in range(len(pr_patchset.index)):
        if (
            pr_patchset.iloc[indx]["kind"] == "REWORK"
        ):  # only REWORK type operations are taken into consideration
            lines_changed = lines_changed + abs(
                pr_patchset.iloc[indx]["sizeInsertions"]
            )  # only inserted lines are reviewe, deleted lines are reviewed in previous operations, so ther are not considered

        for indx in range(len(pr_comments_instance)):
            if "comment)" in pr_comments_instance.iloc[indx]["message"]:
                comment_count = comment_count + 1
            if "comments)" in pr_comments_instance.iloc[indx]["message"]:
                commentsString = (
                    pr_comments_instance.iloc[indx]["message"]
                    .split("(")[1]
                    .split(" comments")[0]
                )

                if len(commentsString) < 3:
                    comment_count = comment_count + int(commentsString)

    if lines_changed > LARGE_CHANGESET_THRESHOLD_LINES:
        large_changeset['reviews_count'] = large_changeset['reviews_count'] + 1
        large_changeset['reviews_mean_comments'] = (
            large_changeset['reviews_mean_comments'] + comment_count
        )

        if pr_data_normalized.iloc[index]["status"] == "ABANDONED":
            large_changeset['reviews_abandoned_count'] = (
                large_changeset['reviews_abandoned_count'] + 1
            )

        # large changeset smell
        if pr_completion_times[index] > SLEEPING_REVIEWS_THRESHOLD_DAYS:
            large_changeset['reviews_mean_completion_time'] = (
                large_changeset['reviews_mean_completion_time']
                + pr_completion_times[index]
            )
            large_changeset['reviews_sleeping_count'] = (
                large_changeset['reviews_sleeping_count'] + 1
            )

        if (
            pr_num_of_iterations[index] > PING_PONG_SMELL_LOOP_THRESHOLD
        ):  # ping pong smell
            large_changeset['ping_pong_reviews_count'] = (
                large_changeset['ping_pong_reviews_count'] + 1
            )
            large_changeset['reviews_mean_iterations'] = (
                large_changeset['reviews_mean_iterations'] + pr_num_of_iterations[index]
            )

        if comment_count == NO_COMMENT_THRESHOLD:  # reviewers negligence impact
            large_changeset['no_comment_reviews_count'] = (
                large_changeset['no_comment_reviews_count'] + 1
            )

    if (
        SMALL_CHANGESET_THRESHOLD_LINES
        < lines_changed
        < LARGE_CHANGESET_THRESHOLD_LINES
    ):
        medium_changeset['reviews_count'] = medium_changeset['reviews_count'] + 1
        medium_changeset['reviews_mean_comments'] = (
            medium_changeset['reviews_mean_comments'] + comment_count
        )
        medium_changeset['reviews_mean_iterations'] = (
            medium_changeset['reviews_mean_iterations'] + pr_num_of_iterations[index]
        )
        medium_changeset['reviews_mean_completion_time'] = (
            medium_changeset['reviews_mean_completion_time'] + pr_completion_times[index]
        )

    if lines_changed < SMALL_CHANGESET_THRESHOLD_LINES:
        small_changeset['reviews_count'] = small_changeset['reviews_count'] + 1
        small_changeset['reviews_mean_comments'] = (
            small_changeset['reviews_mean_comments'] + comment_count
        )
        small_changeset['reviews_mean_iterations'] = (
            small_changeset['reviews_mean_iterations'] + pr_num_of_iterations[index]
        )
        small_changeset['mean_completion_time'] = (
            small_changeset['mean_completion_time'] + pr_completion_times[index]
        )

    if index % LOG_MESSAGE_TRIGGER_INDEX == 0:
        print(f"{index} PRs processed for changeset size impacts")

large_changeset['reviews_mean_comments'] = (
    large_changeset['reviews_mean_comments'] / large_changeset['reviews_count']
)
medium_changeset['reviews_mean_comments'] = (
    medium_changeset['reviews_mean_comments'] / medium_changeset['reviews_count']
)
small_changeset['reviews_mean_comments'] = (
    small_changeset['reviews_mean_comments'] / small_changeset['reviews_count']
)
large_changeset['reviews_mean_iterations'] = (
    large_changeset['reviews_mean_iterations'] / large_changeset['ping_pong_reviews_count']
)
large_changeset['reviews_mean_completion_time'] = (
    large_changeset['reviews_mean_completion_time']
    / large_changeset['reviews_sleeping_count']
)
medium_changeset['reviews_mean_iterations'] = (
    medium_changeset['reviews_mean_iterations'] / medium_changeset['reviews_count']
)
small_changeset['reviews_mean_iterations'] = (
    small_changeset['reviews_mean_iterations'] / small_changeset['reviews_count']
)
medium_changeset['reviews_mean_completion_time'] = (
    medium_changeset['reviews_mean_completion_time'] / medium_changeset['reviews_count']
)
small_changeset['mean_completion_time'] = (
    small_changeset['mean_completion_time'] / small_changeset['reviews_count']
)

# ping pong smell and abandance impact and review completion time impact
# var declarations
ping_pong = {}

ping_pong['review_count'] = 0
ping_pong['reviews_abandoned_count'] = 0
ping_pong['reviews_sleeping_count'] = 0
ping_pong['reviews_mean_completion_time'] = 0
for index in range(len(pr_data_comments)):
    if pr_num_of_iterations[index] > PING_PONG_SMELL_LOOP_THRESHOLD:  # ping pong smell
        ping_pong['review_count'] = ping_pong['review_count'] + 1

        if pr_data_normalized.iloc[index]["status"] == "ABANDONED":
            ping_pong['reviews_abandoned_count'] = ping_pong['reviews_abandoned_count'] + 1

        if pr_completion_times[index] > SLEEPING_REVIEWS_THRESHOLD_DAYS:
            ping_pong['reviews_sleeping_count'] = ping_pong['reviews_sleeping_count'] + 1
            ping_pong['reviews_mean_completion_time'] = (
                ping_pong['reviews_mean_completion_time'] + pr_completion_times[index]
            )

    if index % LOG_MESSAGE_TRIGGER_INDEX == 0:
        print(f"{index} PRs processed for ping pong and impacts")

ping_pong['reviews_mean_completion_time'] = (
    ping_pong['reviews_mean_completion_time'] / ping_pong['reviews_sleeping_count']
)

pp.pprint(f"total number of issues:{len(pr_data_normalized)}")
pp.pprint(f"sleeping:{sleeping}")
pp.pprint(f"nonsleeping: {nonsleeping}")
pp.pprint(f"large_changeset: {large_changeset}")
pp.pprint(f"medium_changeset: {medium_changeset}")
pp.pprint(f"small_changeset: {small_changeset}")
pp.pprint(f"ping_pong: {ping_pong}")
