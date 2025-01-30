"""
A quick and dirty script to parse Reddit dumps
(written using the pushshift 40k top subreddit 2005-2023 archive)
Reads in submission and comment jsonl files, scans for keywords,
then outputs select fields in CSV format.

Submissions and comments are in chronological order.

Finds and outputs matching submissions and all comments belonging
to matching submissions, ignores matching comments to non-matching
submissions. Most useful for structured analysis when the keywords
do a good job of identifying relevant submissions.
"""

REDDITS = ["breastcancer"]
KEYWORDS = [" aesthetic closure", " goldilock", " explant", " flat chest", " aesthetic flat", " be flat", " being flat", " is flat", " are flat", " i am flat", " i m flat", " am flat", " was flat", " go flat", " gone flat"," going flat", " went flat", " stay flat", " staying flat", " stayed flat", " flat ambassador", " flat closure", " flatties", " years flat", " year flat", " remove the implant"," removed the implant", " removing the implant", " remove my implant", " removed my implant", " removing my implant", " post-explant"]

SUBMISSION_COLUMNS = ["subreddit","type","title","author","score","selftext","url","id","permalink","created_utc","date", "month"]
COMMENT_COLUMNS = ["subreddit","type","author","score","body","id","parent_id","submission_id","submission_title","permalink","created_utc","date",]

SAMPLE = False

# Reddit API notes
# 'score' is the total score ('ups' - 'downs') of a post. 'ups' and
#     downs' are deprecated - 'ups' is always the same as 'score' and
#     'downs' is always zero.
# 'controversality' is a boolean flag to show that a comment has a high,
#     but roughly similar number of likes/dislikes
#
# Reddit API changes mean that some fields (e.g. created_utc) are
# different types over time and some (e.g. permalinks) may not exist
# at all.

# Reddit Thing Fullnames (from the Reddit API docs)
# "A fullname is a combination of a thing's type (e.g. Link) and its unique ID which forms a compact encoding of a globally unique ID on reddit.
#  Fullnames start with the type prefix for the object's type, followed by the thing's unique ID in base 36. For example, t3_15bfi0."

# type  prefixes
# t1_	Comment
# t2_	Account
# t3_	Link (and submissions??)
# t4_	Message
# t5_	Subreddit
# t6_	Award



import json
import csv
from datetime import datetime 
import re, string
from collections import defaultdict

def get_submission(j, comments):
    parent_ids = []
    while 1:
        if j["parent_id"][0:3] == "t3_":
            return j["parent_id"]
        parent_ids.append(j["parent_id"])
        if j["parent_id"] in comments.keys():
            j = comments[j["parent_id"]]
        else:
            return None

cleanup_pattern = re.compile(r'[\W_]+')
submission_ids = {}
for reddit in REDDITS:
    if SAMPLE:
        submissions_filename = reddit+"_submissions_sample"
    else:
        submissions_filename = reddit+"_submissions"
    with open(submissions_filename,"r", encoding="UTF-8") as submissions_file:
        submissions = {}
        for line in submissions_file:
            j = json.loads(line)
            title = " "+cleanup_pattern.sub(' ', j["title"].lower())+" "
            selftext = " "+cleanup_pattern.sub(' ', j["selftext"].lower())+" "
            if any([(keyword in selftext or keyword in title) for keyword in KEYWORDS]):
                submission = {}
                submission["subreddit"] = j["subreddit"]
                submission["type"] = "submission"
                submission["title"] = j["title"]
                submission["author"] = j["author"]
                submission["score"] = j["score"]
                submission["selftext"] = j["selftext"]
                submission["url"] = j["url"]
                submission["id"] = "t3_"+j["id"]
                submission["permalink"] = "https://www.reddit.com"+j["permalink"]
                submission["created_utc"] = j["created_utc"]
                submission["date"] = datetime.fromtimestamp(int(j["created_utc"])).strftime('%Y-%m-%d')
                submission["month"] = datetime.fromtimestamp(int(j["created_utc"])).strftime('%Y-%m')
                submissions[submission["id"]] = submission
            continue
        submission_ids[reddit] = [submission["id"] for submission in submissions.values()]
    with open("./output/"+reddit+"_submissions"+".csv","w",encoding="UTF-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=SUBMISSION_COLUMNS)
        writer.writeheader()
        for submission in submissions.values():
            writer.writerow(submission)
    with open("./output/"+reddit+"_submissions"+".json","w",encoding="UTF-8") as jsonfile:
        json.dump(submissions, jsonfile)

    if SAMPLE:
        comments_filename = reddit+"_comments_sample"
    else:
        comments_filename = reddit+"_comments"
    with open(comments_filename,"r", encoding="UTF-8") as comments_file:
        comments = {}
        comments_by_thread = defaultdict(list)
        for line in comments_file:
            j = json.loads(line)
            body = " "+cleanup_pattern.sub(' ', j["body"].lower())+" "
            # This only works because the comments are in chronological order
            # and children cannot come before parents!
            if j["parent_id"] in submission_ids[reddit] or j["parent_id"] in comments.keys():
                comment = {}
                comment["subreddit"] = j["subreddit"]
                comment["type"] = "comment"
                comment["author"] = j["author"]
                comment["score"] = j["score"]
                comment["body"] = j["body"]
                comment["id"] = "t1_"+j["id"]
                comment["parent_id"] = j["parent_id"]
                comment["submission_id"] = get_submission(j,comments)
                comment["submission_title"] = submissions[get_submission(j,comments)]["title"]
                if "permalink" in j:
                    comment["permalink"] = "https://www.reddit.com"+j["permalink"]
                else:
                    # sometimes (maybe because of older API versions) there aren't permalinks
                    comment["permalink"] = "NONE"
                comment["created_utc"] = j["created_utc"]
                comment["date"] = datetime.fromtimestamp(int(j["created_utc"])).strftime('%Y-%m-%d')
                comments[comment["id"]] = comment
                comments_by_thread[comment["parent_id"]].append(comment)
            continue
        with open("./output/"+reddit+"_comments"+".csv","w",encoding="UTF-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=COMMENT_COLUMNS)
            writer.writeheader()
            for thread_id in comments_by_thread:
                for comment in comments_by_thread[thread_id]:
                    writer.writerow(comment)
        with open("./output/"+reddit+"_comments"+".json","w",encoding="UTF-8") as jsonfile:
            json.dump(comments, jsonfile)