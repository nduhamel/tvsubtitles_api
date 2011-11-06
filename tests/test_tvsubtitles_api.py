#!/usr/bin/env python
#encoding:utf-8
# Adapted from
#author:dbr/Ben
#project:tvdb_api
#repository:http://github.com/dbr/tvdb_api
#license:unlicense (http://unlicense.org/)

"""Unittests for tvsubtiles_api
"""

import os
import sys
import datetime
import unittest

# Force parent directory onto path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tvsubtitles_api
from tvsubtitles_exceptions import (tvsubtitles_shownotfound, tvsubtitles_seasonnotfound,
tvsubtitles_episodenotfound, tvsubtitles_attributenotfound)

class test_tvsubtitles_basic(unittest.TestCase):
    # Used to store the cached instance of TvSubtitles()
    t = None
    
    def setUp(self):
        if self.t is None:
            self.__class__.t = tvsubtitles_api.TvSubtitles(cache = True)
     
    def test_different_case(self):
        """Checks the auto-correction of show names is working.
        It should correct the weirdly capitalised 'sCruBs' to 'Scrubs'
        """
        self.assertEquals(self.t['scrubs'][1][4]['episodename'], 'My Old Lady')
        self.assertEquals(self.t['sCruBs']['seriesname'], 'Scrubs')

    def test_spaces(self):
        """Checks shownames with spaces
        """
        self.assertEquals(self.t['My Name Is Earl']['seriesname'], 'My Name Is Earl')
        self.assertEquals(self.t['My Name Is Earl'][1][4]['episodename'], 'Faked His Own Death')

    def test_numeric(self):
        """Checks numeric show names
        """
        self.assertEquals(self.t['24'][2][20]['episodename'], 'Day 2: 3:00 A.M.-4:00 A.M.')
        self.assertEquals(self.t['24']['seriesname'], '24')

    def test_show_iter(self):
        """Iterating over a show returns each seasons
        """
        self.assertEquals(
            len(
                [season for season in self.t['Life on Mars']]
            ),
            2
        )
    
    def test_season_iter(self):
        """Iterating over a show returns episodes
        """
        self.assertEquals(
            len(
                [episode for episode in self.t['Life on Mars'][1]]
            ),
            8
        )


    def test_get_parent(self):
        """Check accessing series from episode instance
        """
        show = self.t['Battlestar Galactica (2003)']
        season = show[1]
        episode = show[1][1]

        self.assertEquals(
            season.show,
            show
        )

        self.assertEquals(
            episode.season,
            season
        )

        self.assertEquals(
            episode.season.show,
            show
        )


class test_tvsubtitles_errors(unittest.TestCase):
    # Used to store the cached instance of TvSubtitles()
    t = None
    
    def setUp(self):
        if self.t is None:
            self.__class__.t = tvsubtitles_api.TvSubtitles(cache = True)

    def test_seasonnotfound(self):
        """Checks exception is thrown when season doesn't exist.
        """
        self.assertRaises(tvsubtitles_seasonnotfound, lambda:self.t['CNNNN'][10][1])

    def test_shownotfound(self):
        """Checks exception is thrown when episode doesn't exist.
        """
        self.assertRaises(tvsubtitles_shownotfound, lambda:self.t['the fake show thingy'])
    
    def test_episodenotfound(self):
        """Checks exception is raised for non-existent episode
        """
        self.assertRaises(tvsubtitles_episodenotfound, lambda:self.t['Scrubs'][1][30])

    def test_attributenamenotfound(self):
        """Checks exception is thrown for if an attribute isn't found.
        """
        self.assertRaises(tvsubtitles_attributenotfound, lambda:self.t['CNNNN'][1][6]['afakeattributething'])
        self.assertRaises(tvsubtitles_attributenotfound, lambda:self.t['CNNNN']['afakeattributething'])

class test_tvsubtitles_search(unittest.TestCase):
    # Used to store the cached instance of TvSubtitles()
    t = None
    
    def setUp(self):
        if self.t is None:
            self.__class__.t = tvsubtitles_api.TvSubtitles(cache = True, banners = False)

    def test_search_len(self):
        """There should be only one result matching
        """
        self.assertEquals(len(self.t['My Name Is Earl'].search('Faked His Own Death')), 1)

    def test_search_checkname(self):
        """Checks you can get the episode name of a search result
        """
        self.assertEquals(self.t['Scrubs'].search('my first')[0]['episodename'], 'My First Day')
        self.assertEquals(self.t['My Name Is Earl'].search('Faked His Own Death')[0]['episodename'], 'Faked His Own Death')
    
    def test_search_multiresults(self):
        """Checks search can return multiple results
        """
        self.assertEquals(len(self.t['Scrubs'].search('my first')) >= 3, True)

    def test_search_no_params_error(self):
        """Checks not supplying search info raises TypeError"""
        self.assertRaises(
            TypeError,
            lambda: self.t['Scrubs'].search()
        )

    def test_search_season(self):
        """Checks the searching of a single season"""
        self.assertEquals(
            len(self.t['Scrubs'][1].search("First")),
            3
        )
    
    def test_search_show(self):
        """Checks the searching of an entire show"""
        self.assertEquals(
            len(self.t['CNNNN'].search('CNNNN', key='episodename')),
            2
        )

    def test_aired_on(self):
        """Tests airedOn show method"""
        sr = self.t['Scrubs'].airedOn(datetime.date(2001, 10, 2))
        self.assertEquals(len(sr), 1)
        self.assertEquals(sr[0]['episodename'], u'My First Day')

class test_tvsubtitles_misc(unittest.TestCase):
    # Used to store the cached instance of TvSubtitles()
    t = None
    
    def setUp(self):
        if self.t is None:
            self.__class__.t = tvsubtitles_api.TvSubtitles(cache = True, banners = False)

    def test_repr_show(self):
        """Check repr() of Season
        """
        self.assertEquals(
            repr(self.t['CNNNN']),
            "<Show Chaser Non-Stop News Network (CNNNN) (containing 2 seasons)>"
        )
    def test_repr_season(self):
        """Check repr() of Season
        """
        self.assertEquals(
            repr(self.t['CNNNN'][1]),
            "<Season instance (containing 9 episodes)>"
        )
    def test_repr_episode(self):
        """Check repr() of Episode
        """
        self.assertEquals(
            repr(self.t['CNNNN'][1][1]),
            "<Episode 01x01 - Terror Alert>"
        )

#~ class test_tvsubtitles_languages(unittest.TestCase):
    #~ def test_episode_name_french(self):
        #~ """Check episode data is in French (language="fr")
        #~ """
        #~ t = tvdb_api.Tvdb(cache = True, language = "fr")
        #~ self.assertEquals(
            #~ t['scrubs'][1][1]['episodename'],
            #~ "Mon premier jour"
        #~ )
        #~ self.assertTrue(
            #~ t['scrubs']['overview'].startswith(
                #~ u"J.D. est un jeune m\xe9decin qui d\xe9bute"
            #~ )
        #~ )
#~ 
    #~ def test_episode_name_spanish(self):
        #~ """Check episode data is in Spanish (language="es")
        #~ """
        #~ t = tvdb_api.Tvdb(cache = True, language = "es")
        #~ self.assertEquals(
            #~ t['scrubs'][1][1]['episodename'],
            #~ "Mi Primer Dia"
        #~ )
        #~ self.assertTrue(
            #~ t['scrubs']['overview'].startswith(
                #~ u'Scrubs es una divertida comedia'
            #~ )
        #~ )
#~ 
    #~ def test_multilanguage_selection(self):
        #~ """Check selected language is used
        #~ """
        #~ class SelectEnglishUI(tvdb_ui.BaseUI):
            #~ def selectSeries(self, allSeries):
                #~ return [x for x in allSeries if x['language'] == "en"][0]
#~ 
        #~ class SelectItalianUI(tvdb_ui.BaseUI):
            #~ def selectSeries(self, allSeries):
                #~ return [x for x in allSeries if x['language'] == "it"][0]
#~ 
        #~ t_en = tvdb_api.Tvdb(
            #~ cache=True,
            #~ custom_ui = SelectEnglishUI,
            #~ language = "en")
        #~ t_it = tvdb_api.Tvdb(
            #~ cache=True,
            #~ custom_ui = SelectItalianUI,
            #~ language = "it")
#~ 
        #~ self.assertEquals(
            #~ t_en['dexter'][1][2]['episodename'], "Crocodile"
        #~ )
        #~ self.assertEquals(
            #~ t_it['dexter'][1][2]['episodename'], "Lacrime di coccodrillo"
        #~ )


#~ class test_tvdb_unicode(unittest.TestCase):
    #~ def test_search_in_chinese(self):
        #~ """Check searching for show with language=zh returns Chinese seriesname
        #~ """
        #~ t = tvdb_api.Tvdb(cache = True, language = "zh")
        #~ show = t[u'T\xecnh Ng\u01b0\u1eddi Hi\u1ec7n \u0110\u1ea1i']
        #~ self.assertEquals(
            #~ type(show),
            #~ tvdb_api.Show
        #~ )
        #~ 
        #~ self.assertEquals(
            #~ show['seriesname'],
            #~ u'T\xecnh Ng\u01b0\u1eddi Hi\u1ec7n \u0110\u1ea1i'
        #~ )
#~ 
    #~ def test_search_in_all_languages(self):
        #~ """Check search_all_languages returns Chinese show, with language=en
        #~ """
        #~ t = tvdb_api.Tvdb(cache = True, search_all_languages = True, language="en")
        #~ show = t[u'T\xecnh Ng\u01b0\u1eddi Hi\u1ec7n \u0110\u1ea1i']
        #~ self.assertEquals(
            #~ type(show),
            #~ tvdb_api.Show
        #~ )
        #~ 
        #~ self.assertEquals(
            #~ show['seriesname'],
            #~ u'Virtues Of Harmony II'
        #~ )

#~ class test_tvdb_doctest(unittest.TestCase):
    #~ # Used to store the cached instance of Tvdb()
    #~ t = None
    #~ 
    #~ def setUp(self):
        #~ if self.t is None:
            #~ self.__class__.t = tvdb_api.Tvdb(cache = True, banners = False)
    #~ 
    #~ def test_doctest(self):
        #~ """Check docstring examples works"""
        #~ import doctest
        #~ doctest.testmod(tvdb_api)


class test_tvsubtitles_custom_caching(unittest.TestCase):
    def test_true_false_string(self):
        """Tests setting cache to True/False/string

        Basic tests, only checking for errors
        """

        tvsubtitles_api.TvSubtitles(cache = True)
        tvsubtitles_api.TvSubtitles(cache = False)
        tvsubtitles_api.TvSubtitles(cache = "/tmp")

    def test_invalid_cache_option(self):
        """Tests setting cache to invalid value
        """

        try:
            tvsubtitles_api.TvSubtitles(cache = 2.3)
        except ValueError:
            pass
        else:
            self.fail("Expected ValueError from setting cache to float")

    def test_custom_urlopener(self):
        class UsedCustomOpener(Exception):
            pass

        import urllib2
        class TestOpener(urllib2.BaseHandler):
            def default_open(self, request):
                print request.get_method()
                raise UsedCustomOpener("Something")

        custom_opener = urllib2.build_opener(TestOpener())
        t = tvsubtitles_api.TvSubtitles(cache = custom_opener)
        try:
            t['scrubs']
        except UsedCustomOpener:
            pass
        else:
            self.fail("Did not use custom opener")

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity = 2)
    unittest.main(testRunner = runner)
