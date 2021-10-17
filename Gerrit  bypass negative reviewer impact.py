import numpy as np
import pandas as pd
from pandas import DataFrame
from scipy.stats import norm
from pandas.io.json import json_normalize
import matplotlib.pyplot as plt

# --------------------------------------reading data ----------------------------------

# review data
pr_data_raw = pd.read_json("eclipse.json", lines=True)

# extract nested 'data' column
pr_data_nested = []
for index, row in pr_data_raw.iterrows():
    pr_data_nested.append(pd.json_normalize(row["data"]))

pr_data_search_fields = []
for index, row in pr_data_raw.iterrows():
    pr_data_search_fields.append(pd.json_normalize(row["search_fields"]))

# get nested 'comments' and 'patchset' columns
patchsets = []
comments = []

for index in range(len(pr_data_nested)):
    current_row = pr_data_nested[index]
    if (
        current_row.iloc[0]["status"] != "NEW"
        and current_row.iloc[0]["status"] != "ABANDONED"
    ):
        for index3, row in current_row.iterrows():
            patchsets.append(pd.json_normalize(row["patchSets"]))
            comments.append(pd.json_normalize(row["comments"]))

# Bots list
# personally, I would like to have separate text files for each project along with their PR data to import and use them as needed
# > rather than having them all in one place

ECLIPSE_BOTS = {
    "EGit Bot",
    "JGit Bot",
    "Platform Bot",
    "CI Bot",
    "OSEE Bot",
    "BaSyx Bot",
    "Eclipse Genie",
    "Trace Compass Bot",
    "JDT Bot",
    "Equinox Bot",
    "CDT Bot",
    "M2E Bot",
    "PDE Bot",
    "Orbit Bot",
    "CBI Bot",
    "EASE Bot",
    "QVT-OML Bot",
    "Jubula Bot",
    "Linux Tools Bot",
    "Xtext Bot",
    "Sirius Bot",
    "DLTK Bot",
    "StatET Bot",
    "Nebula Bot",
    "SWTBot Bot",
    "EMFStore Bot",
}
WIRESHARK_BOTS = {"Petri Dish Buildbot", "Wireshark code review", "human rights"}
LIBREOFFICE_BOTS = {
    "Jenkins",
    "Jenkins CollaboraOffice",
    "Pootle bot, LibreOﬃciant",
    "Weblate",
    "Gerrit Code Review",
    "JP",
    "libreoffice lhm",
}
QT_BOTS = {
    "Qt Sanity Bot",
    "Qt CI Bot",
    "Qt Cherry-pick Bot",
    "Qt Submodule Update Bot",
    "Qbs CI Bot",
    "Qt LanceBot",
    "Qt CMake Build Bot",
    "Qt Wayland Headless Tests Bot",
    "Qt Continuous Integration System",
    "Qt Cleanup Bot",
    "Qt Doc Bot",
    "Qt Forward Merge Bot",
    "The Qt Project",
    "Qt3dStudioBot",
    "Qt CI Test Bot",
    "Continuous Integration (KDAB)",
}

# --------------------------------------Functions---------------------------------------

# this function gets review data, commits, and returns 3 array  patches that have at least one negative vote
# and bypassed negative reviewer patches
def bypass_negative_reviewer(comments, bot_list):
    pr_with_negative_vote_comments = []
    pr_with_negative_vote_indices = []
    pr_with_bypass_smell_comments = []
    pr_with_bypass_smell_indices = []
    rejection = False

    for index in range(len(comments)):
        current_pr_comments = comments[index]

        for indx in range(len(current_pr_comments)):
            # -1 and -2 are negative votes that reviewers give
            if (
                current_pr_comments.iloc[indx]["message"].find("Code-Review-1") != -1
                or current_pr_comments.iloc[indx]["message"].find("Code-Review-2") != -1
            ):
                rejection = True
                break

        if rejection:
            pr_with_negative_vote_comments.append(comments[index])
            pr_with_negative_vote_indices.append(index)

        rejection = False
    # searching for bypassed reviews in rejected reviews
    for index in range(len(pr_with_negative_vote_comments)):
        bypass = False
        author_name = ""
        negative_voter = ""
        current_pr_comments = pr_with_negative_vote_comments[index]

        if (
            current_pr_comments.iloc[0]["reviewer.name"]
            == current_pr_comments.iloc[0]["reviewer.name"]
            and current_pr_comments.iloc[0]["reviewer.name"] not in bot_list
        ):  # if owner name(who uploaded the patch, first row of instance comment ) is not Nan and Bot
            author_name = current_pr_comments.iloc[0]["reviewer.name"]

        for indx in range(1, len(current_pr_comments)):
            if (
                len(author_name) > 0
                and current_pr_comments.iloc[indx]["reviewer.name"]
                == current_pr_comments.iloc[indx]["reviewer.name"]
                and current_pr_comments.iloc[indx]["reviewer.name"] != author_name
                and current_pr_comments.iloc[indx]["reviewer.name"] not in bot_list
            ):
                if (
                    current_pr_comments.iloc[indx]["message"].find("Code-Review-1")
                    != -1
                    or current_pr_comments.iloc[indx]["message"].find("Code-Review-2")
                    != -1
                ):
                    negative_voter = current_pr_comments.iloc[indx]["reviewer.name"]
                    positive_vote_after_negative_vote = 0

                    for indxx in range(indx + 1, len(current_pr_comments)):
                        if (
                            current_pr_comments.iloc[indxx]["reviewer.name"]
                            == negative_voter
                        ):
                            # if negative reviewer, reviews and gives positive vote afterward, the review is not bypassed
                            if (
                                current_pr_comments.iloc[indxx]["message"].find(
                                    "Code-Review+1"
                                )
                                != -1
                                or current_pr_comments.iloc[indxx]["message"].find(
                                    "Code-Review+2"
                                )
                                != -1
                            ):
                                positive_vote_after_negative_vote = positive_vote_after_negative_vote + 1

                    if positive_vote_after_negative_vote == 0:
                        bypass = True
                        break

        if bypass:
            pr_with_bypass_smell_comments.append(
                pr_with_negative_vote_comments[index]
            )  # bypassed patches comments
            pr_with_bypass_smell_indices.append(
                pr_with_negative_vote_indices[index]
            )

    return (
        pr_with_negative_vote_comments,
        pr_with_bypass_smell_comments,
        pr_with_bypass_smell_indices,
    )  # bypassed patchsets


# ---------------------------------------calling functions-------------------------------
pr_with_negative_vote_comments, pr_bypassed_list_comments, pr_bypassed_list_indices = bypass_negative_reviewer(comments)

# ------------------------------------------bypass and time impact-------------------------------------
SECONDS_IN_DAY = 24 * 60 * 60
SLEEPING_REVIEW_THRESHOLD_IN_DAYS = 2
pr_bypassed_and_sleeping_count = 0
pr_bypassed_reviews_mean_completion_time = 0
for index in range(len(pr_bypassed_list_comments)):
    pr_bypassed_comments_instance = pr_bypassed_list_comments[index]
    last_comment = pr_bypassed_comments_instance.iloc[-1]
    
    if (
        last_comment["reviewer.name"] == last_comment["reviewer.name"]
    ):  # if reviewer name of last row is not Nan
        if (
            last_comment["reviewer.name"] not in bot_list
        ):  # if the reviewer of last task is a Bot
            pr_bypassed_comments_instance.drop(
                pr_bypassed_comments_instance.tail(1).index, inplace=True
            )  # drop the last row
    # substract time stamp of last review operation from first review operation
    pr_completion_time_days = (
        pr_bypassed_comments_instance.tail(1)["timestamp"].iloc[0]
        - pr_bypassed_comments_instance.head(1)["timestamp"].iloc[0]
    )
    pr_completion_time_days = pr_completion_time_days / SECONDS_IN_DAY
    pr_bypassed_reviews_mean_completion_time = (
        pr_bypassed_reviews_mean_completion_time + pr_completion_time_days
    )
    if (
        pr_completion_time_days > SLEEPING_REVIEW_THRESHOLD_IN_DAYS
    ):  # if review takes more than one day it considers sleeping review
        pr_bypassed_and_sleeping_count = pr_bypassed_and_sleeping_count + 1

pr_bypassed_reviews_mean_completion_time = (
    pr_bypassed_reviews_mean_completion_time / len(pr_bypassed_list_comments)
)

# ------------------------------------------------------bypass smell and ping pong smell impact--------------------------
PING_PONG_SMELL_LOOP_THRESHOLD = 3
pr_bypassed_ping_pong_count = 0

for index in range(len(pr_bypassed_list_comments)):
    ping_pong_count = 0
    comments_instance = pr_bypassed_list_comments[index]
    
    for indx in range(len(comments_instance)):
        if comments_instance.iloc[indx]["message"].find("Uploaded") != -1:
            ping_pong_count = ping_pong_count + 1
    if ping_pong_count > PING_PONG_SMELL_LOOP_THRESHOLD:
        pr_bypassed_ping_pong_count = pr_bypassed_ping_pong_count + 1
# ------------------------------------------------------bypass smell and reviewer's negligence--------------------------
pr_bypassed_reviewer_negligence_count = 0
pr_bypassed_mean_num_of_comments = 0

for index in range(len(pr_bypassed_list_comments)):
    comments_instance = pr_bypassed_list_comments[index]
    comment_count = 0
    
    for indxx in range(
        len(comments_instance)
    ):  # this loop calculates number of comments in each PR
        current_message = comments_instance.iloc[indxx]["message"]
    
        if "comment)" in current_message:  # 1 comment for reviewer
            comment_count = comment_count + 1
    
        elif "comments)" in current_message:  # several comments
            comment_count_extracted = current_message.split("(")[1].split(" comments")[0]
    
            if len(comment_count_extracted) < 3:
                comment_count = comment_count + int(comment_count_extracted)
                
    pr_bypassed_mean_num_of_comments = pr_bypassed_mean_num_of_comments + comment_count
    if comment_count == 0:
        pr_bypassed_reviewer_negligence_count = pr_bypassed_reviewer_negligence_count + 1

pr_bypassed_mean_num_of_comments = pr_bypassed_mean_num_of_comments / len(pr_bypassed_list_comments)
