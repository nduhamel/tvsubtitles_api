# encoding: utf-8
#       tvsubtitles_api.py
#       
#       Copyright 2011 nicolas <nicolas@jombi.fr>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
import urllib2
import urllib
import logging
import datetime
import os

import lxml.html
from BeautifulSoup import UnicodeDammit

from tvsubtitles_exceptions import (tvsubtitles_error, tvsubtitles_shownotfound,
    tvsubtitles_seasonnotfound, tvsubtitles_episodenotfound, tvsubtitles_languagenotfound,
     tvsubtitles_attributenotfound)
from parsers import (TvShowSearchParser, TvSowParser, EpisodeParser)


__license__ = 'GPLv2'
__version__ = '0.1a'
__maintainer__ = 'Nicolas Duhamel'


lastTimeout = None

def log():
    return logging.getLogger("tvsubtitles_api")

def dice_coefficient(a, b):
    """ Used for sort search results
    From: http://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Dice%27s_coefficient#Python
    dice coefficient 2nt/na + nb."""
    if not len(a) or not len(b): return 0.0
    if len(a) == 1:  a=a+u'.'
    if len(b) == 1:  b=b+u'.'
 
    a_bigram_list=[]
    for i in range(len(a)-1):
      a_bigram_list.append(a[i:i+2])
    b_bigram_list=[]
    for i in range(len(b)-1):
      b_bigram_list.append(b[i:i+2])
 
    a_bigrams = set(a_bigram_list)
    b_bigrams = set(b_bigram_list)
    overlap = len(a_bigrams & b_bigrams)
    dice_coeff = overlap * 2.0/(len(a_bigrams) + len(b_bigrams))
    return dice_coeff

def decode_html(html_string):
    """ Used for correctly decode html"""
    converted = UnicodeDammit(html_string, isHTML=True)
    if not converted.unicode:
        raise UnicodeDecodeError(
            "Failed to detect encoding, tried [%s]",
            ', '.join(converted.triedEncodings))
    return converted.unicode

    
class BaseUI:
    """Default non-interactive UI, which auto-selects first results
    """
    def __init__(self, config):
        self.config = config

    def selectSeries(self, allSeries):
        return allSeries[0]

class ShowContainer(dict):
    """Simple dict that holds a series of Show instances
    """
    pass

class Show(dict):
    """Holds a dict of seasons, and show data.
    """
    def __init__(self):
        dict.__init__(self)
        self.data = {}

    def __repr__(self):
        return "<Show %s (containing %s seasons)>" % (
            self.data.get(u'seriesname', 'instance'),
            len(self)
        )

    def __getitem__(self, key):
        if key in self:
            # Key is an episode, return it
            return dict.__getitem__(self, key)

        if key in self.data:
            # Non-numeric request is for show-data
            return dict.__getitem__(self.data, key)

        # Data wasn't found, raise appropriate error
        if isinstance(key, int) or key.isdigit():
            # Episode number x was not found
            raise tvsubtitles_seasonnotfound("Could not find season %s" % (repr(key)))
        else:
            # If it's not numeric, it must be an attribute name, which
            # doesn't exist, so attribute error.
            raise tvsubtitles_attributenotfound("Cannot find attribute %s" % (repr(key)))

    def search(self, term = None, key = None):
        """
        Search all episodes in show. Can search all data, or a specific key (for
        example, episodename)

        Always returns an array (can be empty). First index contains the first
        match, and so on.

        Each array index is an Episode() instance, so doing
        search_results[0]['episodename'] will retrieve the episode name of the
        first match.

        Search terms are converted to lower case (unicode) strings.

        # Examples
        
        These examples assume t is an instance of TvSubtitles():
        
        >>> t = TvSubtitles()
        >>>

        To search for all episodes of Scrubs with a bit of data
        containing "my first day":

        >>> t['Scrubs'].search("my first day")
        [<Episode 01x01 - My First Day>]
        >>>

        Search for "My Name Is Earl" episode named "Faked His Own Death":

        >>> t['My Name Is Earl'].search('Faked His Own Death', key = 'episodename')
        [<Episode 01x04 - Faked His Own Death>]
        >>>

        To search Scrubs for all episodes with "mentor" in the episode name:

        >>> t['scrubs'].search('mentor', key = 'episodename')
        [<Episode 00x38 - Will You Ever Be My Mentor>, <Episode 01x02 - My Mentor>, <Episode 03x15 - My Tormented Mentor>]
        >>>

        # Using search results

        >>> results = t['Scrubs'].search("my first")
        >>> print results[0]['episodename']
        My First Day
        >>> for x in results: print x['episodename']
        My First Day
        My First Step
        My First Kill
        >>>
        """
        results = []
        for cur_season in self.values():
            searchresult = cur_season.search(term = term, key = key)
            if len(searchresult) != 0:
                results.extend(searchresult)
        return results

class Season(dict):
    def __init__(self, show = None):
        """The show attribute points to the parent show
        """
        self.show = show

    def __repr__(self):
        return "<Season instance (containing %s episodes)>" % (
            len(self.keys())
        )

    def __getitem__(self, episode_number):
        if episode_number not in self:
            raise tvsubtitles_episodenotfound("Could not find episode %s" % (repr(episode_number)))
        else:
            return dict.__getitem__(self, episode_number)

    def search(self, term = None, key = None):
        """Search all episodes in season, returns a list of matching Episode
        instances.

        >>> t = TvSubtitles()
        >>> t['scrubs'][1].search('first day')
        [<Episode 01x01 - My First Day>]
        >>>

        See Show.search documentation for further information on search
        """
        results = []
        for ep in self.values():
            searchresult = ep.search(term = term, key = key)
            if searchresult is not None:
                results.append(
                    searchresult
                )
        return results

class Episode(dict):
    def __init__(self, season = None):
        """The season attribute points to the parent season
        """
        self.season = season

    def __repr__(self):
        seasno = int(self.get(u'seasonnumber', 0))
        epno = int(self.get(u'episodenumber', 0))
        epname = self.get(u'episodename')
        if epname is not None:
            return "<Episode %02dx%02d - %s>" % (seasno, epno, epname)
        else:
            return "<Episode %02dx%02d>" % (seasno, epno)

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            raise tvsubtitles_attributenotfound("Cannot find attribute %s" % (repr(key)))

    def search(self, term = None, key = None):
        """Search episode data for term, if it matches, return the Episode (self).
        The key parameter can be used to limit the search to a specific element,
        for example, episodename.
        
        This primarily for use use by Show.search and Season.search. See
        Show.search for further information on search

        Simple example:

        >>> e = Episode()
        >>> e['episodename'] = "An Example"
        >>> e.search("examp")
        <Episode 00x00 - An Example>
        >>>

        Limiting by key:

        >>> e.search("examp", key = "episodename")
        <Episode 00x00 - An Example>
        >>>
        """
        if term == None:
            raise TypeError("must supply string to search for (contents)")

        term = unicode(term).lower()
        for cur_key, cur_value in self.items():
            cur_key, cur_value = unicode(cur_key).lower(), unicode(cur_value).lower()
            if key is not None and cur_key != key:
                # Do not search this key
                continue
            if cur_value.find( unicode(term).lower() ) > -1:
                return self

class LanguageGetter:
    def __init__(self, tvsubtitles, eid):
        self._tvsubtitles = tvsubtitles
        self.config = tvsubtitles.config 
        self._eid =eid
        self._data = False
        
    def __getitem__(self, key):
        if not self._data:
            log().debug('Getting all series language for %s' % (self._eid))
            self._load()
        return self._data[key]
    
    def _load(self):
        log().debug('Loading language for episode %s' % (self._eid ) )
        html = self._tvsubtitles._getetsrc(
            self.config['url_episode'] % (self._eid)
        )
        parser = EpisodeParser(html)
        self._data = parser.parse()
        
    

class TvSubtitles:
        
    def __init__(self, language = None, custom_ui= None, urlopener = None):
        """
        language (2 character language abbreviation):
            The language of the returned data. Is also the language search
            uses. Default is "en" (English).
        """
        self.shows = ShowContainer() # Holds all Show classes
        self.corrections = {} # Holds show-name to show_id mapping
        self.config = {}
        if language is None:
            self.config['language'] = None
        else:
            self.config['language'] = language
        
        if urlopener is None:
            self.config['cache_enabled'] = False
            self.urlopener = urllib2.build_opener() # default opener with no caching
        elif isinstance(urlopener, urllib2.OpenerDirector):
            # If passed something from urllib2.build_opener, use that
            log().debug("Using %r as urlopener" % cache)
            self.config['cache_enabled'] = True
            self.urlopener = cache
        else:
            raise ValueError("Invalid value for URLopener %r (type was %s)" % (cache, type(cache)))
        
        
        self.config['custom_ui'] =  custom_ui
        
        self.config['url_searchSeries'] = "http://www.tvsubtitles.net/search.php"
        self.config['url_serie_season'] = 'http://www.tvsubtitles.net/tvshow-%s-%s.html'
        self.config['url_episode'] = "http://www.tvsubtitles.net/episode-%s.html"
        
    def __getitem__(self, key):
        """Handles tvsubtitles_instance['seriesname'] calls.
        The dict index should be the show id
        """
        if isinstance(key, (int, long)):
            # Item is integer, treat as show id
            if key not in self.shows:
                self._getShowData(key, self.config['language'])
            return self.shows[key]
        
        key = key.lower() # make key lower case
        sid = self._nameToSid(key)
        log().debug('Got series id %s' % (sid))
        return self.shows[sid]
        
    def _nameToSid(self, name):
        """Takes show name, returns the correct series ID (if the show has
        already been grabbed), or grabs all episodes and returns
        the correct SID.
        """
        if name in self.corrections:
            log().debug('Correcting %s to %s' % (name, self.corrections[name]) )
            sid = self.corrections[name]
        else:
            log().debug('Getting show %s' % (name))
            selected_series = self._getSeries( name )
            sname, sid = selected_series['name'], selected_series['id']
            log().debug('Got %(name)s, id %(id)s' % selected_series)

            self.corrections[name] = sid
            self._getShowData(selected_series['id'])
        return sid
    
    def _getSeries(self, term):
        """This searches TVsubtitles.net for the series name,
        If a custom_ui UI is configured, it uses this to select the correct
        series. If not BaseUI is used to select the first result.
        """
        log().debug("Searching for show %s" % term)
        seriesHTML = self._getetsrc(self.config['url_searchSeries'] , urllib.urlencode({'q': term}))        
        parser = TvShowSearchParser(seriesHTML)
        allSeries = parser.parse()
        
        # Sort:
        for serie in allSeries:
            serie['dice_coef'] = dice_coefficient(term, serie['name'].lower())
        allSeries = sorted(allSeries, key=lambda serie: serie['dice_coef'], reverse=True)

        if len(allSeries) == 0:
            log().debug('Series result returned zero')
            raise tvsubtitle_shownotfound("Show-name search returned zero results (cannot find show on TVsubtitles.net)")

        if self.config['custom_ui'] is not None:
            log().debug("Using custom UI %s" % (repr(self.config['custom_ui'])))
            ui = self.config['custom_ui'](config = self.config)
        else:
            log().debug('Auto-selecting first search result using BaseUI')
            ui = BaseUI(config = self.config)
        return ui.selectSeries(allSeries)
        
    def _getetsrc(self, url, data = None):
        """Loads a URL using caching, returns an ElementTree of the source
        """
        src = self._loadUrl(url, data)
        return lxml.html.fromstring(decode_html(src))
        
    def _loadUrl(self, url, data, recache = False):
        global lastTimeout
        try:
            log().debug("Retrieving URL %s" % url)
            if not data:
                resp = self.urlopener.open(url)
            else:
                resp = self.urlopener.open(url, data)
        except (IOError, urllib2.URLError), errormsg:
            if not str(errormsg).startswith('HTTP Error'):
                lastTimeout = datetime.datetime.now()
            raise tvsubtitles_error("Could not connect to server: %s" % (errormsg))
        
        return resp.read()
    
    def _getShowData(self, sid):
        """Takes a series ID, gets the epInfo URL and parses the 
        TVsubtitles HTML into the shows dict in layout:
        shows[series_id][season_number][episode_number]
        """ 
        log().debug('Getting all series data for %s' % (sid))
        html = self._getetsrc(
            self.config['url_serie_season'] % (sid, 1)
        )
        parser = TvSowParser(html)
        serie = parser.parse()
        
        self._setShowData(sid, 'seriesname', serie['name'])
        
        for season in serie['other_seasons']:
            log().debug('Getting all season %s data ' % (season))
            html = self._getetsrc( 
                self.config['url_serie_season'] % (sid, season) 
            )
            parser = TvSowParser(html)
            tmp = parser.parse()
            serie['seasons'].update(tmp['seasons'])
        
        for season, episodes in serie['seasons'].items():
            for ep in episodes:
                self._setItem(sid, season, ep['num'], 'seasonnumber', season)
                self._setItem(sid, season, ep['num'], 'episodenumber', ep['num'])
                self._setItem(sid, season, ep['num'], 'id', ep['id'])
                self._setItem(sid, season, ep['num'], 'episodename', ep['name'])
                self._setItem(sid, season, ep['num'], 'available_languages', ep['lang'])
                self._setItem(sid, season, ep['num'], 'languages', 
                    LanguageGetter(self, ep['id'] ) 
                )

    def _setShowData(self, sid, key, value):
        """Sets self.shows[sid] to a new Show instance, or sets the data
        """
        if sid not in self.shows:
            self.shows[sid] = Show()
        self.shows[sid].data[key] = value
                
    def _setItem(self, sid, seas, ep, attrib, value):
        """Creates a new episode, creating Show(), Season() and
        Episode()s as required. Called by _getShowData to populate show

        Since the nice-to-use tvsubtitles[1][24]['name] interface
        makes it impossible to do tvsubtitles[1][24]['name] = "name"
        and still be capable of checking if an episode exists
        so we can raise tvsubtitles_shownotfound, we have a slightly
        less pretty method of setting items.. but since the API
        is supposed to be read-only, this is the best way to
        do it!
        The problem is that calling tvsubtitles[1][24]['episodename'] = "name"
        calls __getitem__ on tvsubtitles[1], there is no way to check if
        tvsubtitles.__dict__ should have a key "1" before we auto-create it
        """
        if sid not in self.shows:
            self.shows[sid] = Show()
        if seas not in self.shows[sid]:
            self.shows[sid][seas] = Season(show = self.shows[sid])
        if ep not in self.shows[sid][seas]:
            self.shows[sid][seas][ep] = Episode(season = self.shows[sid][seas])
        self.shows[sid][seas][ep][attrib] = value

if __name__ == '__main__':
    logging.basicConfig(level = logging.DEBUG)
    t= TvSubtitles()
    print t['The WALKING DEAD'][2][3]['available_languages']
    print "Trying to get languages"
    print t['The WALKING DEAD'][2][3]['languages']['fr']
