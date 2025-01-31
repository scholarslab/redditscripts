"""
A quick and dirty script to parse Reddit dumps
(written using the pushshift 40k top subreddit 2005-2023 archive)
Reads in submission and comment jsonl files, scans for keywords,
then outputs select fields in CSV format.

Outputs body and header as text blobs per month, based on the UTC
month that each submission and comment were posted. Also outputs
20 most frequent words every month, with counts and frequencies.
"""

REDDITS = ["breastcancer"]
KEYWORDS = [" aesthetic closure", " goldilock", " explant", " flat chest", " aesthetic flat", " be flat", " being flat", " is flat", " are flat", " i am flat", " i m flat", " am flat", " was flat", " go flat", " gone flat"," going flat", " went flat", " stay flat", " staying flat", " stayed flat", " flat ambassador", " flat closure", " flatties", " years flat", " year flat", " remove the implant"," removed the implant", " removing the implant", " remove my implant", " removed my implant", " removing my implant", " post-explant"]

SUBMISSION_COLUMNS = ["subreddit","type","title","author","score","selftext","url","id","permalink","created_utc","date"]
COMMENT_COLUMNS = ["subreddit","type","author","score","body","id","parent_id","submission_id","submission_title","permalink","created_utc","date"]

CUSTOM_STOPWORDS = KEYWORDS+["breast", "breasts", "cancer","chest","surgeon","surgery","closure","procedure", "reconstruction","mastectomy","boobs","boobies","boob","implant","implants"]

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

import json
import csv
from datetime import datetime 
from collections import defaultdict
from nltk.tokenize import word_tokenize
import nltk
from nltk.corpus import stopwords
import re, string

"""
Dedupe function, used to process stopwords.
"""
def process_stopwords(items):
    seen = set()
    result = []
    for item in items:
        if item not in seen and item not in stopwords.words():
            seen.add(item)
            result.append(item)
    return result
CUSTOM_STOPWORDS = process_stopwords(CUSTOM_STOPWORDS)
print("Stopwords:",CUSTOM_STOPWORDS)
STOPWORDS = set(stopwords.words() + CUSTOM_STOPWORDS)

cleanup_pattern = re.compile(r'[\W_]+')
submission_ids = {}
for reddit in REDDITS:
    with open("./output/"+reddit+"_submissions"+".json","r",encoding="UTF-8") as jsonfile:
        submissions = json.load(jsonfile)
    submission_ids[reddit] = [submission["id"] for submission in submissions.values()]

    with open("./output/"+reddit+"_comments"+".json","r",encoding="UTF-8") as jsonfile:
        comments = json.load(jsonfile)
    
    textbymonth = defaultdict(str)
    wordsbymonth = defaultdict(list)
    for id,submission in submissions.items():
        words = re.findall(r'\w+', submission["title"]+" "+submission["selftext"])
        # words = word_tokenize(submission["title"]+" "+submission["selftext"])
        wordsbymonth[submission["month"]].extend(words)
        words.append(" ")
        textbymonth[submission["month"]]+=" ".join(words)

    for id,comment in comments.items():
        words = re.findall(r'\w+', comment["body"])
        # Use the submission month to avoid sparse data
        month = submissions[comment["submission_id"]]["month"]
        wordsbymonth[month].extend(words)
        words.append(" ")
        textbymonth[month]+=" ".join(words)

wordcount = sum([len(y) for x,y in wordsbymonth.items()])
for month,words in wordsbymonth.items():
    filtered_words = [w.lower() for w in words if not w.lower() in stopwords.words() and not w.lower() in CUSTOM_STOPWORDS]
    # only filter out nltk basic stopwords and not custom stopwords for ngrams
    unfiltered_words = [w.lower() for w in words if not w.lower() in stopwords.words()]
    frequency = nltk.FreqDist(filtered_words)
    with open("./output/monthly/freq/"+reddit+"_"+month+".csv","w",encoding="UTF-8") as outfile:
        outfile.writelines([word + ", " + str(count) + "\n" for word,count in frequency.most_common(20)])
    bigrams = nltk.FreqDist(list(nltk.bigrams(unfiltered_words)))
    with open("./output/monthly/bigrams/"+reddit+"_"+month+"_bigrams.csv", "w", encoding="UTF-8") as outfile:
        outfile.writelines([" ".join(bigram) + ", " + str(count) + "\n" for bigram,count in bigrams.most_common(20)])
    trigrams = nltk.FreqDist(list(nltk.trigrams(unfiltered_words)))
    with open("./output/monthly/trigrams/"+reddit+"_"+month+"_trigrams.csv", "w", encoding="UTF-8") as outfile:
        outfile.writelines([" ".join(trigram) + ", " + str(count) + "\n" for trigram,count in trigrams.most_common(20)])
    

for key in textbymonth.keys():
    with open("./output/monthly/"+reddit+"_"+key+".txt","w",encoding="UTF-8") as outfile:
        outfile.write(textbymonth[key])
