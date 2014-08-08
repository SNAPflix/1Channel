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
from addon.common.addon import Addon

_1CH = Addon('plugin.video.1channel')
ADDON_PATH = _1CH.get_path()
ICON_PATH = os.path.join(ADDON_PATH, 'icon.png')

class SRT_Scraper():
    def __init__(self):
        pass
    
    def get_tvshow_id(self, title, year):
        pass
    
    def get_subtitles(self, language, title, year, season, episode):
        pass
    
    def download_subtitle(self, url):
        pass
    
    def __get_url(self, url):
        pass
    
    def __get_cached_url(self, url):
        pass
    
    