#!/usr/bin/env python
import sys
import pickle
import cluster
import numpy as np
import echonest.remix.audio as audio
from pyechonest import config
config.CALL_TIMEOUT=30
import threading

# This is the demo script.
# Feed it a pre-computed pickle file from analyseFeatures.py.  Make sure
# you run both in the same directory, because the pickle file contains
# (relative) filenames.

maxCacheSize = 15   # HM can we have in RAM at once
# This clock increments each time the cache is accessed
cacheTime = 0
# A dictionary from filename to CachedSong
songCache = {}

class CachedSong:
    def __init__(self,fn):
        global cacheTime
        self.m_fn = fn
        self.m_birthTime = cacheTime
        print 'Song Cache: loading song %s...' % fn
        self.m_adata = None#!!audio.LocalAudioFile(fn)

class CacheSongThread(threading.Thread):
    def __init__(self,fn):
        self.m_fn = fn
        threading.Thread.__init__(self)
    def run (self):
        global songCache
        print '** Song fetch thread - begin **'
        newsong = CachedSong(self.m_fn)
        while len(songCache)>=maxCacheSize:
            # find oldest and remove
            ages = [cs.m_birthTime for cs in songCache.values()]
            minAge = np.min(ages)
            for k,v in songCache.iteritems():
                if v.m_birthTime == minAge:
                    # found it
                    del songCache[k]
                    break
        assert len(songCache) < maxCacheSize
        # can add our new one now
        songCache[self.m_fn] = newsong
        print '** Song fetch thread - end **'
        

def getSongFromCache( fn, loadBlocking=False ):
    # If the song is in the cache already - simple
    global cacheTime
    global songCache
    cacheTime += 1
    if fn in songCache:
        # simply return it
        return songCache[fn]
    else:
        if loadBlocking:
            # load this one, wait to finish, add and return it.
            assert len(songCache) < maxCacheSize
            newsong = CachedSong( fn )
            songCache[fn] = newsong
            return newsong
        else:
            # The song was not there so we return None.  But, start loading
            # the song in  a separate thread.
            # To stop a quick second call restarting a retrieve, store None
            # there fore now.
            songCache[fn] = None
            CacheSongThread(fn).start()
            return None
            

def playRegion( adata, rtype, rgnIdx ):
    # Get this region quantum
    #!!q = cluster.getRegionsOfType( adata.analysis, rtype )[rgnIdx]
    # Don't know what to do right now.  Write to wav file and do a system call.
    pass

def docheck( clsec, clSection, currSec ):
    assert clSection in range( clsec.nbClusters() ), 'clSection=%d out of range [0,%d)' % (clSection,clsec.nbClusters())
    assert currSec in range( clsec.nbRegions() ), 'currSec=%d out of range [0,%d)' % (currSec, clsec.nbRegions())


# this loads a dict from rtype to clinfo
f = open(sys.argv[1],'rb');
clinfo = pickle.load(f)
f.close()
# makes code briefer
clsec = clinfo['sections']

# Some technical issues:
#  - can't fit all songs into RAM
#  - loading takes a bit of time
# Here's an easy heuristic solution that should sound alright:
#  - set up a cache with some max nb songs to load in ram
#  - replace LRU
#  - every time it tries to change and can't because file isn't there, start
#    loading it.

nsame = 5
nrep  = 3

print 'INITIALIZING...'
# The main tune is the 'sections' of the songs.  Randomly pick an initial
# cluster.

# current section cluster
clSection = np.random.choice( range( clsec.nbClusters() ) )  
# current section, integer index into ALL regions of this type
currSec = clsec.nextRegion( clSection, None )
getSongFromCache( clsec.getFilenameOfRegion(currSec), True )

# keep doing this check every time these vars change, for consistency.
docheck( clsec, clSection, currSec )

print 'MASHING...'
while True:
    # single cluster loop:
    for i in range( nsame ):
        # single section loop
        for j in range( nrep ):
            print 'Playing cluster %d (of %d), section %d (of %d)' % \
                (clSection, clsec.nbClusters(), currSec, \
                      clsec.sizeOfCluster(clSection) )

            currFn = clsec.getFilenameOfRegion(currSec)
            csong = getSongFromCache(currFn)
            # must be in the cache
            assert csong != None
            playRegion( csong.m_adata, 'sections', \
                            clsec.getSongRegionIdx(currSec) )
        # todo: keep a history and don't go back too early?
        # todo: pick same key?

        # pick a new section in this cluster
        currSecCand = clsec.nextRegion( clSection, currSec )
        if getSongFromCache(clsec.getFilenameOfRegion(currSecCand)) != None:
            # The song is there, we can move to this region.  Otherwise
            # we've prompted it to load, but don't go there right now.
            currSec = currSecCand
            docheck( clsec, clSection, currSec )

    # pick a new cluster
    clSectionCand = clsec.nextCluster( clSection )
    currSecCand = clsec.nextRegion( clSectionCand, None )
    if getSongFromCache(clsec.getFilenameOfRegion(currSecCand)) != None:
        # The song is there, we can move to this cluster.  Otherwise
        # we've prompted it to load, but don't go there right now.
        clSection = clSectionCand
        currSec = currSecCand
        docheck( clsec, clSection, currSec )
