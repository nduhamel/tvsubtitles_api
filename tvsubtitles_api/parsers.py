# encoding: utf-8
#       parsers.py
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
import re
import datetime

__all__ = ['TvShowSearchParser','TvSowParser','EpisodeParser']
class TvShowSearchParser:
        
    def __init__(self, doc):
        self.doc = doc
    
    def parse(self):
        """
        Return search result:
        [ {'name': , 'link': ,  'id': , 'languages': , }, ...]
        """
        res_list = self.doc.xpath('/html/body/div/div[3]/div/ul')[0]
        data = []
        for li in res_list.iterchildren():
            data.append(self.parse_li(li.getchildren()[0]))
        return data
            
    def parse_li(self, li):
        """Parse the li of a ul results.
        
        *Returns*
            a dictionary with parsed data.
        """
        data = {}
        data["languages"] = []
        for ele in li.iterchildren():
            if ele.tag == 'a':
                data['id'] = re.findall(r"\d+", ele.get('href'))[0]
                data['name'] = ele.text_content()
            elif ele.tag == 'img':
                data['languages'].append(ele.get('alt'))
        return data

class TvSowParser:
        
    def __init__(self, doc):
        self.doc = doc
    
    def parse(self):
        """
        Return a dict that contain all serie's data:
        key:
            * name
            * season (num , epdict)
            * known_season  [1, 2, ...]
        """
        data = {}
        data['name'] = self.doc.xpath('/html/body/div/div[3]/div/h2')[0].text_content()
        p = self.doc.xpath('/html/body/div/div[3]/div/p')[0]
        cur, other_seasons = self.parse_seasons(p)
        table = self.doc.xpath('//table[@id="table5"]')[0]
        episodes = self.parse_ep(table)
        data['seasons'] = {cur: episodes}
        data['other_seasons'] = other_seasons
        return data

        
    def parse_seasons(self, p):
        """ return list of available seasons"""
        data = []
        for ele in p.iterchildren():
            if ele.tag == 'font':
                cur =  int(ele.text_content().split(' ')[1])
            elif ele.tag == 'a':
                b = ele.find('b')
                data.append( int(ele.text_content().split(' ')[1]) )
        return (cur, sorted(data))
    
    def parse_ep(self, table):
        """
        Return episode dict
        keys:
            * id int
            * num int
            * name
            * lan ['en', 'fr' ...]
        """
        episodes = []
        for ele in list(table)[1:-2]:
            td = list(ele)
            ep = {}
            ep['num'] = int(td[0].text_content().split('x')[1])
            a = td[1].find('a')
            ep['id'] = int(re.findall(r"\d+", a.get('href'))[0])
            ep['name'] = a.text_content()
            ep['lang'] = []
            for ele in td[3].find('nobr'):
                if ele.tag == 'a':
                    ep['lang'].append(ele.find('img').get('alt'))
            episodes.insert(0,ep)
        return episodes

class EpisodeParser:
    def __init__(self, doc):
        self.doc = doc
    
    def parse(self):
        """
        data form:
        { 'en': 
            [{ 'name':
              'rip':
              'release':
              'uploaded_date':
              'author':
              'downloaded':
              'good':
              'bad':
              }, ...],
        }
        """
        data = {}
        divs = self.doc.xpath('//div[@class="subtitlen"]')
        for div in divs:
            release = {}
            release['download_url']= 'http://www.tvsubtitles.net'+ div.getparent().get('href')
	    release['download_url'] = release['download_url'].replace('subtitle-','download-')
            for ele in div.iterchildren():
                if ele.tag == 'div':
                    ele = ele.find('span')
                    for span in ele.findall('span'):
                        if span.get('style') == 'color:red':
                            release['bad'] = int(span.text_content())
                        if span.get('style')== 'color:green':
                            release['good'] = int(span.text_content())
                if ele.tag == 'h5':
                    release['name'] = ele.text_content()
                    lang = ele.find('img').get('src').split('/')[-1].split('.')[0]
                if ele.tag == 'p':
                    if ele.get('title') == 'rip':
                        release['rip'] = ele.text_content().strip()
                    if ele.get('title') == 'release':
                        release['release'] = ele.text_content().strip()
                    if ele.get('title') == 'uploaded':
                        release['uploaded'] = datetime.datetime.strptime(ele.text_content().strip()
                                                    , '%d.%m.%y %H:%M:%S')
                    if ele.get('title') == 'author':
                        release['author'] = ele.text_content().strip()
                        if not release['author']:
                            release['author'] = "anonymous"
                    if ele.get('title') == 'downloaded':
                        release['downloaded'] = int(ele.text_content().strip())
            if lang not in data.keys():
                        data[lang] = []
            data[lang].append(release)
        return self.sort_by_rate(data)

    def sort_by_rate(self,data):
    	"""Sorting subtitles by rate"""
	for lang,list_sub in data.items():
		data[lang] = sorted(list_sub, key=lambda k: k['good'], reverse=True) 
    	return data
