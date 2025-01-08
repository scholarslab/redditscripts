"""
A quick and dirty script to parse Reddit dumps
(written using the pushshift 40k top subreddit 2005-2023 archive)
Reads in submission and comment jsonl files, scans for keywords,
then outputs select fields in CSV format.

Output 100 most frequent words for entire corpus, with counts and
frequencies. Output monthly frequency for those 100 words.
"""

REDDITS = ["breastcancer"]
KEYWORDS = [" aesthetic closure", " goldilock", " explant", " flat chest", " aesthetic flat", " be flat", " being flat", " is flat", " are flat", " i am flat", " i m flat", " am flat", " was flat", " go flat", " gone flat"," going flat", " went flat", " stay flat", " staying flat", " stayed flat", " flat ambassador", " flat closure", " flatties", " years flat", " year flat", " remove the implant"," removed the implant", " removing the implant", " remove my implant", " removed my implant", " removing my implant", " post-explant"]

SUBMISSION_COLUMNS = ["subreddit","type","title","author","score","selftext","url","id","permalink","created_utc","date"]
COMMENT_COLUMNS = ["subreddit","type","author","score","body","id","parent_id","submission_id","submission_title","permalink","created_utc","date"]

# CUSTOM_STOPWORDS = " ".join(KEYWORDS).split()+["breast", "breasts", "cancer","chest","surgeon","surgery","closure","procedure", "reconstruction","mastectomy","boobs","boobies","boob","implant","implants"]+[str(n) for n in range(0,11)]
CUSTOM_STOPWORDS = " ".join(KEYWORDS).split()+["breast", "breasts", "cancer"]+[str(n) for n in range(0,11)]

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

# figure out total corpus freqs
corpus_words = []
for month,words in wordsbymonth.items():
    filtered_words = [w.lower() for w in words if not w.lower() in STOPWORDS]
    corpus_words.extend(filtered_words)

corpus_frequency = nltk.FreqDist(corpus_words)
with open("./output/freq-over-time/"+reddit+"_corpus_freq.csv","w",encoding="UTF-8") as outfile:
    outfile.writelines([word + ", " + str(count) + ", " + str(round(count/len(corpus_words),7)) + "\n" for word,count in corpus_frequency.most_common(100)])

with open("./output/freq-over-time/"+reddit+"_monthly_freq.csv","w",encoding="UTF-8") as outfile:
    freq_words = [word for word,count in corpus_frequency.most_common(20)]
    outfile.write("month,"+",".join(freq_words)+"\n")
    for month,words in wordsbymonth.items():
        filtered_words = [w.lower() for w in words if not w.lower() in STOPWORDS]
        word_count = len(filtered_words)
        freqs = [month]
        freqs.extend([str(round(filtered_words.count(freq_word)/word_count,7)) for freq_word in freq_words])
        outfile.write(",".join(freqs)+"\n")

with open("./output/freq-over-time/"+reddit+"_monthly_count.csv","w",encoding="UTF-8") as outfile:
    freq_words = [word for word,count in corpus_frequency.most_common(20)]
    outfile.write("[month],[total words],"+",".join(freq_words)+"\n")
    for month,words in wordsbymonth.items():
        filtered_words = [w.lower() for w in words if not w.lower() in STOPWORDS]
        word_count = len(filtered_words)
        freqs = [month, str(word_count)]
        freqs.extend([str(filtered_words.count(freq_word)) for freq_word in freq_words])
        outfile.write(",".join(freqs)+"\n")

# for month,words in wordsbymonth.items():
#     filtered_words = [w.lower() for w in words if not w.lower() in stopwords.words() and not w.lower() in CUSTOM_STOPWORDS]
#     frequency = nltk.FreqDist(filtered_words)
#     with open("./output/monthly/freq/"+reddit+"_"+month+".csv","w",encoding="UTF-8") as outfile:
#         outfile.writelines([word + ", " + str(count) + ", " + str(round(count/len(filtered_words),5)) + "\n" for word,count in frequency.most_common(20)])

# for key, text in textbymonth.items():
#     with open("./output/monthly/"+reddit+"_"+key+".txt","w",encoding="UTF-8") as outfile:
#         outfile.write(text)
