#!/usr/bin/python
# -*- coding: utf8 -*-

import urllib2
import urllib
import re
import sys
import csv
import os
import shutil

#######################################
# basic variables you can change
#######################################

UrlListOfSentences = 'https://tatoeba.org/eng/sentences_lists/show/4022/none/' # basic url with the list of the sentences (if there are many pages they will be processed page by page)
getAudio = True # True if we grab audio if sentences in a source language have it
getTags = True # True if we copy the tags if they exist
getAutor = True # True if we want to know who is the author (will appear as an extra tag)
srclang = ["en","es","ar"] # languages of source sentences (may be 1 or more that will appear on the question field). This should be 2-letter code ISO 639-1  https://en.wikipedia.org/wiki/List_of_ISO_639-2_codes
audio3letterslangcodes = ["eng","spa","ara"] # these codes are used in Tatoeba's url when you browse audio by language, e.g. cmn for Chinese in https://tatoeba.org/eng/sentences/with_audio/cmn
targetlang = "ru" # target language code (will be on the answer's fiels)
copymediafilestoankifolder = True # if true you should manually set your anki media folder
ankimediafolder = "C:\\Documents\\Anki\\1-й пользователь\\collection.media"  # this is "collection.media" folder which is normally located in your documents folder (in Windows)

########################################
# Here the main code begins
########################################

if os.path.exists('foranki'):
    key = raw_input("'foranki' folder already exists. Press Enter to clean it or close this window")
    if not key:
        shutil.rmtree('foranki')

try:
    os.mkdir('foranki')
except:
    print "The script couldn't create a temporary workdir foranki."
    sys.exit(1)
    
cfile = open("foranki/exampledeck.csv", "wb")

def procstring(string):
    res = string
    res=res.replace("&#039;","'")
    res=res.replace("&quot;",'"')
    return res

# process the link, open it and grab all we need
def proclink(num):
    taglist = []
    url = 'https://tatoeba.org/eng/sentences/show/' + num
    
    curaudio = ''
    resp = urllib2.urlopen(url)
    if resp.getcode() != 200:
        print "Error response for search"
        sys.exit(1)
    html = resp.read()
    if getTags:
        tagname=re.findall('class="tagName".+?\>(.+?)\<',html,re.DOTALL)
        for i in tagname:
            taglist.append(i.strip().replace(" ","_"))
    if getAutor:
        authorname=re.findall('title="belongs\sto\s(.+?)"',html)
        if len(authorname) > 0:
            taglist.append('by_' + authorname[0])
        else:
            taglist.append('orphan_sentence')
    srcsentence=''
    mainlang = ''
    for i,item in enumerate(srclang):
        srcsentence = re.findall('mainSentence.+?<div lang="' + item + '" dir="\w{3}" class="text correctnessZero">(.+?)<\/div><\/div><\/div>',html)
        if len(srcsentence) > 0:
            srcsentence = srcsentence[0]
            mainlang=audio3letterslangcodes[i]
            break
        else:
            srcsentence=''
            continue
    if srcsentence=='':
        print "Error while trying to get the source sentence"
        return

    audiourl = 'https://audio.tatoeba.org/sentences/' + mainlang + '/' + num + '.mp3'
    if getAudio:
        laudio = re.findall("https\:\/\/audio\.tatoeba\.org\/sentences\/(\w{3})\/" + num + ".mp3",html)
        if laudio != []:
            # grab audio
            urllib.urlretrieve(audiourl,"foranki/" + num + ".mp3")
            curaudio = '[sound:' + num + '.mp3]'

    
    targetsentence = re.findall('directTranslation".+?<div lang="' + targetlang + '" dir="\w{3}" class="text correctnessZero">(.+?)<\/div>',html)
    if len(targetsentence) > 0:
        targetsentence=targetsentence[0]
    else:
        targetsentence=''

    csv_writer = csv.writer(cfile, delimiter='\t', lineterminator='\n')
    print " ".join([srcsentence + curaudio, targetsentence, " ".join(taglist)])
    csv_writer.writerow([procstring(srcsentence) + curaudio, procstring(targetsentence), " ".join(taglist)])
   

def mainproc():
    # 1. get the list of sentences from the first page
    global UrlListOfSentences
    UrlListOfSentences=UrlListOfSentences.replace('/page:1','').rstrip("/")
    resp = urllib2.urlopen(UrlListOfSentences + '/page:1')
    if resp.getcode() != 200:
        print "Failed to open " + UrlListOfSentences
        sys.exit(1)
    html = resp.read()

    # how many pages there are in this list
    pagescount = re.findall('/page\:(\d+?)"\stitle="Last page"',html)
    if pagescount != []:
        pagescount = int(pagescount[0])
    else:
        pagescount = 0 # there is no pagination
    print pagescount
    links = re.findall("<div data-sentence-id=\"(.+?)\"\sclass",html,re.DOTALL)
    sentences = re.findall('<div lang="\w{2,}" dir=\".+\" class=\"text correctnessZero\"\>(.+?)</div>',html)
    resp.close()

    for i in range(len(links)):
        # print links[i] + " " + sentences[i]
        proclink(links[i])

    prCnt = 1 # this is a progress counter (not really necessary but kind of convenient feature)

    for pagescounter in xrange(2,pagescount + 1):
        urlloop = UrlListOfSentences.rstrip("/") + "/page:" + str(pagescounter)
        resp = urllib2.urlopen(urlloop)
        if resp.getcode() != 200:
            print "Failed to open " + urlloop
            sys.exit(1)
        html = resp.read()
        links = re.findall("<div data-sentence-id=\"(.+?)\"\sclass",html,re.DOTALL)
        sentences = re.findall('<div lang="\w{2,}" dir=\".+\" class=\"text correctnessZero\"\>(.+?)</div>',html)
        resp.close()
        for i in range(len(links)):
            proclink(links[i])
        prCnt += 1
        curPrcnt = (100.0*prCnt) / pagescount
        os.system('title ' + str(round(curPrcnt,3)) + '% completed')
        
    # copy media files to anki media folder
    for root, dirs, files in os.walk('foranki'):
        for f in files:
            filename = os.path.join(root, f)
            if filename.endswith('.mp3'):
                if copymediafilestoankifolder:
                    shutil.copy2(filename.decode('utf8'),ankimediafolder.decode('utf8'))
    
mainproc()
cfile.close()
