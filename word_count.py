#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 19 09:45:11 2018

@author: benjamin
"""
import dill as pickle
import os
import re
from collections import defaultdict as dd
from nltk import word_tokenize, pos_tag
from nltk.probability import FreqDist as fd
import time
#from nltk.corpus import stopwords

site_list=["atlantic", "breitbart", "motherjones", "thehill"]
#site_list=["test1", "test2"]
direc_prefix="/home/benjamin/sfi/project_stuff/SFI_Comments_REU/sample/"

def trim(word):
    return(re.sub(r'[^A-Za-z \']', '', word))
    
#this is a hack to get around the fact that multiprocessing uses pickle 
#(instead of dill) and pickle can't handle lambdas
def dd_of_fd():
    return dd(fd)

#the lowth through the hith files. eg 210, 365 would be the last four months of the year
def make_stats(low=0, hi="hi", pipe=None):
    start=time.time()
    word_counts=dd(fd)
    word_POS_counts=dd(dd_of_fd)
    for site in site_list:
        direc=direc_prefix+site+"/"
        #slightly hacky. please fix
        i=0
        for filename in os.listdir(direc):
            if filename.startswith("comment"):
                if hi=="hi" or i in range(low, hi):
                    with open(direc+filename, "rb") as comment_list_file:
                        comment_list=pickle.load(comment_list_file)
                        for comment in comment_list:
                            tagged_comment=pos_tag(word_tokenize(comment["raw_message"]))
                            for word_POS_pair in tagged_comment:
                                    #was trimming, but i think that will just mess up
                                    #the tagging
                                    #well, the stemmer was working less well that i hoped
                                    base_word=trim(word_POS_pair[0].lower())#stemmer.stem(word_POS_pair[0].lower())
                                    word_counts[site][base_word]+=1
                                    word_POS_counts[site][base_word][word_POS_pair[1]]+=1
                i+=1
    pickle.dump([word_counts, word_POS_counts], open("/home/benjamin/sfi/project_stuff/data/analysis_data"+str(low)+".pkl", "wb"))
    #if we called this as part of a multiprocess
    if pipe is not None:
        print("piping "+str(low)+" after time:")
        begin_piping=time.time()
        print(begin_piping-start)
        pipe.send([word_counts, word_POS_counts])
        #pipe.send(word_counts)
        #pipe.send(word_POS_counts)
        pipe.close()
        print("time to pipe "+str(low)+":")
        print(time.time()-begin_piping)
        return
    else:
        return [word_counts, word_POS_counts]

def proportional_diffs(word_counts, word_POS_counts):                                      
    word_diffs=dd(lambda : dd(int))
    #since i'm discarding words that don't get used at least a couple of time
    #across corpora "atlantic" could be any site (in fact, it should be the corpus with the least variety)
    for w in word_counts["atlantic"]:
        mi=min([word_counts[c].freq(w) for c in site_list])
        ma=max([word_counts[c].freq(w) for c in site_list])
        if abs(mi-ma)>0.005 and min([word_counts[c][w] for c in site_list])>3:
            word_diffs[w]=[{c: word_counts[c].freq(w)} for c in site_list]