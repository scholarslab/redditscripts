"""
A quick and dirty script to parse Reddit dumps
(written using the pushshift 40k top subreddit 2005-2023 archive)
Reads in submission and comment jsonl files, scans for keywords,
then outputs select fields in CSV format.

Outputs body and header as text blobs per month, based on the UTC
month that each submission and comment were posted.
"""

REDDITS = ["breastcancer"]
KEYWORDS = ["flat", "aesthetic closure", "goldilocks", "goldilock"]

SUBMISSION_COLUMNS = ["subreddit","type","title","author","score","selftext","url","id","permalink","created_utc","date"]
COMMENT_COLUMNS = ["subreddit","type","author","score","body","id","permalink","created_utc","date"]

CUSTOM_STOPWORDS = KEYWORDS+["breast", "breasts", "cancer","chest","surgeon","surgery","closure","procedure", "goldilock", "reconstruction","mastectomy","boobs","boobies","boob","implant","implants"]

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
from collections import defaultdict
from nltk.tokenize import word_tokenize
import nltk
from nltk.corpus import stopwords
import re, string

cleanup_pattern = re.compile(r'[\W_]+')
for reddit in REDDITS:
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
            if any([(" "+keyword+" " in selftext or " "+keyword+" " in title) for keyword in KEYWORDS]):
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
                submission["month"] = datetime.fromtimestamp(int(j["created_utc"])).strftime('%Y-%m')
                submissions.append(submission)
            continue
    
    textbymonth = defaultdict(str)
    wordsbymonth = defaultdict(list)

    for submission in submissions:
        words = re.findall(r'\w+', submission["title"]+" "+submission["selftext"])
        # words = word_tokenize(submission["title"]+" "+submission["selftext"])
        wordsbymonth[submission["month"]].extend(words)
        words.append(" ")
        textbymonth[submission["month"]]+=" ".join(words)

    if SAMPLE:
        comments_filename = reddit+"_comments_sample"
    else:
        comments_filename = reddit+"_comments"
    with open(comments_filename,"r", encoding="UTF-8") as comments_file:
        comments = []
        for line in comments_file:
            j = json.loads(line)
            body = " "+cleanup_pattern.sub(' ', j["body"].lower())+" "
            if any([" "+keyword+" " in body for keyword in KEYWORDS]):
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
                comment["month"] = datetime.fromtimestamp(int(j["created_utc"])).strftime('%Y-%m')
                comments.append(comment)
            continue
    for comment in comments:
        words = re.findall(r'\w+', comment["body"])
        # words = word_tokenize(submission["title"]+" "+submission["selftext"])
        wordsbymonth[comment["month"]].extend(words)
        words.append(" ")
        textbymonth[comment["month"]]+=" ".join(words)

wordcount = sum([len(y) for x,y in wordsbymonth.items()])
for month,words in wordsbymonth.items():
    filtered_words = [w.lower() for w in words if not w.lower() in stopwords.words() and not w.lower() in CUSTOM_STOPWORDS]
    frequency = nltk.FreqDist(filtered_words)
    with open("./output/monthly/freq/"+reddit+"_"+month+".csv","w",encoding="UTF-8") as outfile:
        outfile.writelines([word + ", " + str(count) + "\n" for word,count in frequency.most_common(20)])

for key in textbymonth.keys():    
    with open("./output/monthly/"+reddit+"_"+key+".txt","w",encoding="UTF-8") as outfile:
        outfile.write(textbymonth[key])
