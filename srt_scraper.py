"""
    1Channel XBMC Addon
    Copyright (C) 2014 tknorris

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import os
import time
import urllib2
import re
import HTMLParser
import socket
import xbmc
import xbmcvfs
from addon.common.addon import Addon
import utils

_1CH = Addon('plugin.video.1channel')
ADDON_PATH = _1CH.get_path()
ICON_PATH = os.path.join(ADDON_PATH, 'icon.png')
MAX_RETRIES=2
TEMP_ERRORS=[500, 502, 503, 504]
USER_AGENT = ("User-Agent:Mozilla/5.0 (Windows NT 6.2; WOW64)"
              "AppleWebKit/537.17 (KHTML, like Gecko)"
              "Chrome/24.0.1312.56")
BASE_URL='http://www.addic7ed.com'
BASE_PATH=_1CH.get_setting('subtitle-folder')

class SRT_Scraper():
    def __init__(self):
        pass
    
    def get_tvshow_id(self, title, year=None):
        match_title=title.lower()
        html=self.__get_cached_url(BASE_URL, 24)
        regex=re.compile('option\s+value="(\d+)"\s*>(.*?)</option')
        site_matches=[]
        for item in regex.finditer(html):
            tvshow_id,site_title = item.groups()
            site_year=None
            
            # strip year off title and assign it to year if it exists 
            r=re.search('(\s*\((\d{4})\))$', site_title)
            if r:
                site_title=site_title.replace(r.group(1),'')
                site_year=r.group(2)

            #print 'show: |%s|%s|%s|' % (tvshow_id, site_title, site_year)
            if match_title == site_title.lower():
                if year is None or year==site_year:
                    return tvshow_id
                
                site_matches.append((tvshow_id, site_title, site_year))
        
        if not site_matches:
            return None
        elif len(site_matches)==1:
            return site_matches[0][0]
        else:
            # there were multiple title matches and year was passed but no exact year matches found
            for match in site_matches:
                # return the match that has no year specified 
                if match[2] is None:
                    return match[0]
            
    def get_season_subtitles(self, language, tvshow_id, season):
        url = BASE_URL + '/ajax_loadShow.php?show=%s&season=%s&langs=&hd=%s&hi=%s' % (tvshow_id, season, 0, 0)
        html = self.__get_cached_url(url, .25)
        #print html.decode('ascii', 'ignore')
        req_hi = _1CH.get_setting('subtitle-hi')=='true'
        req_hd = _1CH.get_setting('subtitle-hd')=='true'
        items=[]
        regex=re.compile('<td>(\d+)</td><td>(\d+)</td><td>.*?</td><td>(.*?)</td><td.*?>(.+?)</td>.*?<td.*?>(.+?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?><a\s+href="(.*?)">.+?</td>',
                         re.DOTALL)
        for match in regex.finditer(html):
            season, episode, srt_lang, version, completed, hi, corrected, hd, srt_url = match.groups()
            if not language or language==srt_lang and (not req_hi or hi) and (not req_hd or hd):
                item={}
                item['season']=season
                item['episode']=episode
                item['language']=srt_lang
                item['version']=version

                if completed.lower()=='completed':
                    item['completed']=True
                    item['percent']='100'
                else:
                    item['completed']=False
                    r=re.search('([\d.]+)%',completed)
                    if r:
                        item['percent']=r.group(1)
                    else:
                        item['percent']='0'
                    
                item['hi']=True if hi else False
                item['corrected']=True if corrected else False
                item['hd']=True if hd else False
                item['url']=srt_url
                items.append(item)
        return items
            
    
    def get_episode_subtitles(self, language, tvshow_id, season, episode):
        subtitles=self.get_season_subtitles(language, tvshow_id, season)
        items=[]
        for subtitle in subtitles:
            if subtitle['episode']==str(episode):
                items.append(subtitle)
            
        return items

    def download_subtitle(self, url):
        url = BASE_URL + url
        (response, srt) = self.__get_url(url)
        cd=response.info()['Content-Disposition']
        r=re.search('filename="(.*)"', cd)
        if r:
            filename=r.group(1)
        else:
            filename='addic7ed_subtitle.srt'

        if not xbmcvfs.exists(os.path.dirname(BASE_PATH)):
            try:
                try: xbmcvfs.mkdirs(os.path.dirname(BASE_PATH))
                except: os.mkdir(os.path.dirname(BASE_PATH))
            except:
                _1CH.log('Failed to create directory %s' % BASE_PATH)
            else:
                final_path = os.path.join(BASE_PATH, filename)
                with open(final_path, 'w') as f:
                    f.write(srt)
                return final_path
    
    def __get_url(self, url):
        try:
            req = urllib2.Request(url)
            host = BASE_URL.replace('http://', '')
            req.add_header('User-Agent', USER_AGENT)
            req.add_header('Host', host)
            req.add_header('Referer', BASE_URL)
            response = urllib2.urlopen(req, timeout=10)
            body=response.read()
            body = body.encode('utf-8')
            parser = HTMLParser.HTMLParser()
            body = parser.unescape(body)
        except Exception as e:
            builtin = 'XBMC.Notification(PrimeWire, Failed to connect to URL: %s, 5000, %s)'
            xbmc.executebuiltin(builtin % (url, ICON_PATH))
            _1CH.log('Failed to connect to URL %s: (%s)' % (url, e))
            return ('', '')
            
        return (response, body)
        
    def __get_cached_url(self, url, cache=8):
        _1CH.log('Fetching Cached URL: %s' % url)
        before = time.time()
        
        html = utils.get_cached_url(url, cache)
        if html:
            _1CH.log_debug('Returning cached result for: %s' % (url))
            return html
        
        _1CH.log_debug('No cached url found for: %s' % url)
        req = urllib2.Request(url)
    
        host = BASE_URL.replace('http://', '')
        req.add_header('User-Agent', USER_AGENT)
        req.add_header('Host', host)
        req.add_header('Referer', BASE_URL)
        try:
            body = self.__http_get_with_retry(url, req)
            body = body.encode('utf-8')
            parser = HTMLParser.HTMLParser()
            body = parser.unescape(body)
        except Exception as e:
            builtin = 'XBMC.Notification(PrimeWire, Failed to connect to URL: %s, 5000, %s)'
            xbmc.executebuiltin(builtin % (url, ICON_PATH))
            _1CH.log('Failed to connect to URL %s: (%s)' % (url, e))
            return ''
        
        utils.cache_url(url, body)
        after = time.time()
        _1CH.log_debug('Cached Url Fetch took: %.2f secs' % (after - before))
        return body
    
    def __http_get_with_retry(self, url, request):
        _1CH.log('Fetching URL: %s' % request.get_full_url())
        retries=0
        html=None
        while retries<=MAX_RETRIES:
            try:
                response = urllib2.urlopen(request, timeout=10)
                html=response.read()
                # if no exception, jump out of the loop
                break
            except socket.timeout:
                retries += 1
                _1CH.log('Retry #%s for URL %s because of timeout' % (retries, url))
                continue
            except urllib2.HTTPError as e:
                # if it's a temporary code, retry
                if e.code in TEMP_ERRORS:
                    retries += 1
                    _1CH.log('Retry #%s for URL %s because of HTTP Error %s' % (retries, url, e.code))
                    continue
                # if it's not pass it back up the stack
                else:
                    raise
        else:
            raise
        
        response.close()
        return html
