#!/usr/bin/env python
# -*- coding: utf8 -*-
"""A tool do download taboeba sentences and to put them into Anki

Usage:
    Taboeba_anki.py [--audio] [--tags] [--author] [--src-lang <lang>]... [--audio-lang <lang>]... [--target-lang <lang>] [--copy-media] [--anki-media-dir <dir>] [--all] <url>

Options:
    --audio                  Grab audio if sentences in a source language have it.
    --tags                   Copy the tags if they exist.
    --author                 Put author name as an extra tag.
    --src-lang <lang>        Languages of source sentences (may be 1 or more that will appear on the question field). This should be 2-letter code ISO 639-1  https://en.wikipedia.org/wiki/List_of_ISO_639-2_codes.
    --audio-lang <lang>      These codes are used in Tatoeba's url when you browse audio by language, e.g. cmn for Chinese in https://tatoeba.org/eng/sentences/with_audio/cmn.
    --target-lang <lang>     Target language code (will be on the answer's fiels).
    --copy-media             Copy media to Anki media folder.
    --anki-media-dir <dir>   This is "collection.media" folder which is normally located in your documents folder. [Default: ~/Documents/Anki/User\ 1/collection.media/].
    -a, --all                Combines --audio, --tags, --author, --copy-media.
"""

from future import standard_library
standard_library.install_aliases()
from builtins import input
from builtins import str
from builtins import range
from docopt import docopt
import csv
import os
import re
import shutil
import sys
import urllib.request, urllib.parse, urllib.error
import requests
import logging
logging.basicConfig(level=logging.INFO)

args = docopt(__doc__)


UrlListOfSentences = args['<url>']
output_dir = UrlListOfSentences.rpartition('/')[-1]
getAudio = args['--audio']
getTags = args['--tags']
getAuthor = args['--author']
srclang = args['--src-lang']
audio3letterslangcodes = args['--audio-lang']
targetlang = args['--target-lang']
copymediafilestoankifolder = args['--copy-media']
ankimediafolder = args['--anki-media-dir']
if args['--all']:
    getAudio = True
    getTags = True
    getAuthor = True
    copymediafilestoankifolder = True


if os.path.exists(output_dir):
    key = input(f"'{output_dir}' folder already exists. Press Enter to clean it or close this window")
    if not key:
        shutil.rmtree(output_dir)

try:
    os.mkdir(output_dir)
except:
    logging.error(f"The script couldn't create a temporary workdir {output_dir}.")
    sys.exit(1)

cfile = open(f"{output_dir}/exampledeck.csv", "w")

def procstring(string):
    res = string
    res = res.replace("&#039;","'")
    res = res.replace("&quot;",'"')
    return res

# process the link, open it and grab all we need
def proclink(num):
    taglist = []
    url = 'https://tatoeba.org/eng/sentences/show/' + num

    curaudio = ''
    resp = requests.get(url)
    if resp.status_code != 200:
        logging.error("Error response for search")
        sys.exit(1)
    if getTags:
        tagname = re.findall('class="tagName".+?\>(.+?)\<', resp.text, re.DOTALL)
        for i in tagname:
            taglist.append(i.strip().replace(" ", "_"))
    if getAuthor:
        authorname = re.findall('title="belongs\sto\s(.+?)"', resp.text)
        if len(authorname) > 0:
            taglist.append('by_' + authorname[0])
        else:
            taglist.append('orphan_sentence')
    srcsentence = ''
    mainlang = ''
    for i,item in enumerate(srclang):
        srcsentence = re.findall('mainSentence.+?<div lang="' + item + '" dir="\w{3}" ng-non-bindable="" class="text correctnessZero">(.+?)<\/div><\/div><\/div>', resp.text)

        if len(srcsentence) > 0:
            srcsentence = srcsentence[0]
            mainlang = audio3letterslangcodes[i]
            break
        else:
            srcsentence = ''
            continue
    if srcsentence == '':
        logging.error("Error while trying to get the source sentence")
        return

    audiourl = 'https://audio.tatoeba.org/sentences/' + mainlang + '/' + num + '.mp3'
    if getAudio:
        laudio = re.findall("https\:\/\/audio\.tatoeba\.org\/sentences\/(\w{3})\/" + num + ".mp3", resp.text)
        if laudio != []:
            # grab audio
            urllib.request.urlretrieve(audiourl, f"{output_dir}/" + num + ".mp3")
            curaudio = '[sound:' + num + '.mp3]'

    targetsentence = re.findall('directTranslation".+?<div lang="' + targetlang + '" dir="\w{3}"\s+class="text correctnessZero">(.+?)<\/div>', resp.text.replace('ng-non-bindable=""',''))
    if len(targetsentence) > 0:
        targetsentence = targetsentence[0]
    else:
        targetsentence = ''

    csv_writer = csv.writer(cfile, delimiter='\t', lineterminator='\n')
    logging.info(" ".join([srcsentence + curaudio, targetsentence, " ".join(taglist)]))
    csv_writer.writerow([procstring(srcsentence) + curaudio, procstring(targetsentence), " ".join(taglist)])


def mainproc():
    # 1. get the list of sentences from the first page
    global UrlListOfSentences
    UrlListOfSentences = UrlListOfSentences.replace('/page:1','').rstrip("/")
    resp = requests.get(UrlListOfSentences + '/page:1')
    if resp.status_code != 200:
        logging.error("Failed to open " + UrlListOfSentences)
        sys.exit(1)
    # how many pages there are in this list
    pagescount = re.findall('/page\:(\d+?)\D', resp.text)
    if pagescount != []:
        pagescount = max([int(x) for x in pagescount])
    else:
        pagescount = 0 # there is no pagination

    logging.debug(resp.text)

    links = re.findall('class="md-icon-button" href="/\w\w\w/sentences/show/(.+?)\"\>', resp.text, re.DOTALL)

    for i in range(len(links)):
        proclink(links[i])

    prCnt = 1 # this is a progress counter (not really necessary but kind of convenient feature)

    for pagescounter in range(2,pagescount + 1):
        urlloop = UrlListOfSentences.rstrip("/") + "/page:" + str(pagescounter)
        resp = requests.get(urlloop)
        if resp.status_code != 200:
            logging.error("Failed to open " + urlloop)
            sys.exit(1)
        links = re.findall('class="md-icon-button" href="/\w\w\w/sentences/show/(.+?)\"\>', resp.text, re.DOTALL)
        for i in range(len(links)):
            proclink(links[i])
        prCnt += 1
        curPrcnt = (100.0*prCnt) / pagescount
        current_percent_completed = str(round(curPrcnt, 3)) + '% completed'
        if shutil.which('title'):
            os.system('title ' + current_percent_completed)
        else:
            logging.info(current_percent_completed)

    # copy media files to anki media folder
    for root, dirs, files in os.walk(output_dir):
        for f in files:
            filename = os.path.join(root, f)
            if filename.endswith('.mp3'):
                if copymediafilestoankifolder:
                    shutil.copy2(filename, ankimediafolder)

mainproc()
cfile.close()
