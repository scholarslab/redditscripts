"""
A quick and dirty script to parse Reddit dumps
(written using the pushshift 40k top subreddit 2005-2023 archive)
Reads in submission and comment jsonl files, scans for keywords,
then outputs select fields in CSV format.

Written to support Emma Barrett's autism perceptions project.
"""

REDDITS = ["books","horror","horrorlit", "autism"]
KEYWORDS = [["autism","aspergers","on the spectrum"],["autistic","autist"], ["sociopath", "sociopathic"],["psychopath","psycpathic"],["childish"],["stunted"],["mental illness", "mentally ill"],["mental health"],["unreliable"],["ocd","obsessive compulsive"],["anxiety","anxious"]]

# We're treating the autism subreddit differently
AUTISM_KEYWORDS = [["shirley jackson"],["we have always lived in the castle"],["horror books","horror book","horror fiction","horror novels", "horror novel", "horror story", "horror stories"]]

SUBMISSION_COLUMNS = ["subreddit","type","title","author","score","selftext","url","id","permalink","created_utc","date"]
COMMENT_COLUMNS = ["subreddit","type","author","score","body","id","permalink","created_utc","date"]

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

SAMPLE = False

import json
import csv
from datetime import datetime 
import re, string

cleanup_pattern = re.compile(r'[\W_]+')
for reddit in REDDITS:
    if reddit == "autism":
        keywords_list = AUTISM_KEYWORDS
    else:
        keywords_list = KEYWORDS
    for keywords in keywords_list:
        if SAMPLE:
            submissions_filename = reddit+"_submissions_sample"
        else:
            submissions_filename = reddit+"_submissions"
        with open(submissions_filename,"r", encoding="UTF-8") as submissions_file:
            submissions = []
            for line in submissions_file:
                j = json.loads(line)
                title = " "+cleanup_pattern.sub(' ', j["title"].lower())+" "
                selftext = " "+cleanup_pattern.sub(' ', j["selftext"].lower())+" "
                if any([" "+keyword+" " in selftext or " "+keyword+" " in title for keyword in keywords]):
                    submission = {}
                    submission["subreddit"] = j["subreddit"]
                    submission["type"] = "submission"
                    submission["title"] = j["title"]
                    submission["author"] = j["author"]
                    submission["score"] = j["score"]
                    submission["selftext"] = j["selftext"]
                    submission["url"] = j["url"]
                    submission["id"] = j["id"]
                    submission["permalink"] = j["permalink"]
                    submission["created_utc"] = j["created_utc"]
                    submission["date"] = datetime.fromtimestamp(int(j["created_utc"])).strftime('%Y-%m-%d')
                    submissions.append(submission)
                continue
        with open("./output/"+reddit+"_submissions_"+keywords[0]+".csv","w",encoding="UTF-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=SUBMISSION_COLUMNS)
            writer.writeheader()
            for submission in submissions:
                writer.writerow(submission)

        if SAMPLE:
            comments_filename = reddit+"_comments_sample"
        else:
            comments_filename = reddit+"_comments"
        with open(comments_filename,"r", encoding="UTF-8") as comments_file:
            comments = []
            for line in comments_file:
                j = json.loads(line)
                ["subreddit","type","author","score","body","id","permalink","created_utc","date"]                
                body = " "+cleanup_pattern.sub(' ', j["body"].lower())+" "
                if any([" "+keyword+" " in body for keyword in keywords]):
                    comment = {}
                    comment["subreddit"] = j["subreddit"]
                    comment["type"] = "comment"
                    comment["author"] = j["author"]
                    comment["score"] = j["score"]
                    comment["body"] = j["body"]
                    comment["id"] = j["id"]
                    if "permalink" in j:
                        comment["permalink"] = j["permalink"]
                    else:
                        # sometimes (maybe because of older API versions) there aren't permalinks
                        comment["permalink"] = "NONE"
                    comment["created_utc"] = j["created_utc"]
                    comment["date"] = datetime.fromtimestamp(int(j["created_utc"])).strftime('%Y-%m-%d')
                    comments.append(comment)
                continue
        with open("./output/"+reddit+"_comments_"+keywords[0]+".csv","w",encoding="UTF-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=COMMENT_COLUMNS)
            writer.writeheader()
            for comment in comments:
                writer.writerow(comment)