import sqlite3
import re
import os
import os.path
import urllib.parse
import configparser
import sys

from flask import g

class DBUpdater:
    def __init__(self):
        #print(os.path.expanduser("file.txt"))
    
        self.__read_config()
        
    def __read_config(self):
        config_path = None
        config = configparser.ConfigParser()

        user_path = os.path.expanduser("~/.config/mopidyimageprovider/config.ini")
        if os.path.isfile(user_path):
            config_path = user_path
        else:
            config_path = ("/etc/mopidyimageprovider/config.ini")
            
        if os.path.isfile(config_path) and os.access(config_path, os.R_OK):
            config.read(config_path)
        else:
            print("No configuration file found, aborting")
            sys.exit()
            
        self.db_file = config['general']['mopidy_database']
        self.music_base_dir = config['general']['media_basedir']
        
    def get_db_file(self):
        return self.db_file
        
    def get_music_base_dir(self):
        return self.music_base_dir

    def get_db(self, rows_mode):
        db_rows = getattr(g, '_db_rows', None)
        db_normal = getattr(g, '_db_normal', None)
        
        if rows_mode is True and db_rows is None:
            db_rows = g._db_rows = sqlite3.connect(self.db_file)
            db_rows.row_factory = sqlite3.Row
        elif rows_mode is False and db_normal is None:
            db_normal = g._db_normal = sqlite3.connect(self.db_file)
        
        if rows_mode is True:
            return db_rows
        else:
            return db_normal
        #return db

    def __find_file(self, album):
        #album = [item.encode("utf-8") for item in album]
        #print("Searching for cover in album: '" + album[0] + "'")
        cover_path = ""
        if self.pattern_local_file.match(album[2]):
            cover_path = self.pattern_local_file.search(album[2]).group(1)
            cover_path = urllib.parse.unquote(cover_path, encoding='utf-8', errors='replace')
            cover_path = os.path.join(self.music_base_dir, cover_path)
        else:
            print("Not a local file, aborting")
            return None
            #print("URI: '" + album[1] + "'")
    
        if os.path.isfile(cover_path) and os.access(cover_path, os.R_OK):
            x = 0
            #print("File exists and is accessible: " + cover_path)
        elif os.path.isfile(cover_path) is True and os.access(cover_path, os.R_OK) is not True:
            print("File exists but is not accessible: " + cover_path)
            return None
        else:
            print("File does not exist: " + cover_path)
            return None

        cover_path = os.path.dirname(cover_path)
    
        covers = ["cover.jpg", "Cover.jpg", "cover.png", "Cover.png", "folder.jpg", "Folder.jpg", "folder.png", "Folder.png"]
        if self.pattern_cd_folders.match(cover_path):
            cover_path = os.path.dirname(cover_path)
            tmpCovers = []
            for cover in covers:
                tmpCovers.append("CD01" + os.sep + cover)
                tmpCovers.append("CD02" + os.sep + cover)
            covers.extend(tmpCovers)


        found = False
        for cover in covers:
            possible_cover_path = os.path.join(cover_path, cover)
            #print(possible_cover_path)
            if os.path.isfile(possible_cover_path) and os.access(possible_cover_path, os.R_OK):
                return possible_cover_path
            if os.path.isfile(possible_cover_path) is True and os.access(possible_cover_path, os.R_OK) is False:
                print("File exists but is not accessible: " + possible_cover_path)
                return None
            else:
                #print("File does not exist: " + possible_cover_path)
                continue
    
        return None
                 

    def update_all(self):
        conn = self.get_db(False)
        c = conn.cursor()
                
        c.execute("CREATE TABLE IF NOT EXISTS album_cover(uri TEXT UNIQUE, name TEXT, cover_path TEXT, FOREIGN KEY (uri) REFERENCES album (uri))")
        conn.commit()

        album_list = c.execute("SELECT uri, name FROM album")
        c.executemany("INSERT OR IGNORE INTO album_cover(uri, name) VALUES (?, ?)", album_list.fetchall())
        conn.commit()
        
        album_no_cover = c.execute("SELECT album_cover.uri, album_cover.name, track.uri FROM album_cover INNER JOIN track ON track.album = album_cover.uri GROUP BY track.album")
        conn.commit()
        #album_no_cover = album_no_cover.fetchall()

        self.pattern_local_file = re.compile('^local:track:(.*)$')
        self.pattern_cd_folders = re.compile('^.*(CD)[0-9]{1,2}')
        values = list()
        #print(str(len(album_no_cover.fetchall())) + " albums without cover image")
        #print(album_no_cover)
        album_no_cover = album_no_cover.fetchall()
        for album in album_no_cover:
            cover_path = self.__find_file(album)
            if cover_path is not None:
                values.append([cover_path, album[0]])
            else:
                print("No cover found for '" + album[1] + "'")

        c.executemany("UPDATE album_cover SET cover_path = ? WHERE uri = ?", values)
        conn.commit()
        conn.close()
        
        return len(values)
        
    def update_missing(self):
        conn = self.get_db(False)
        c = conn.cursor()
                
        c.execute("CREATE TABLE IF NOT EXISTS album_cover(uri TEXT UNIQUE, name TEXT, cover_path TEXT, FOREIGN KEY (uri) REFERENCES album (uri))")
        conn.commit()

        album_list = c.execute("SELECT uri, name FROM album")
        c.executemany("INSERT OR IGNORE INTO album_cover(uri, name) VALUES (?, ?)", album_list.fetchall())
        conn.commit()
        
        album_no_cover = c.execute("SELECT album_cover.uri, album_cover.name, track.uri FROM album_cover INNER JOIN track ON track.album = album_cover.uri WHERE album_cover.cover_path IS NULL OR album_cover.cover_path = '' GROUP BY track.album")
        conn.commit()
        #album_no_cover = album_no_cover.fetchall()

        self.pattern_local_file = re.compile('^local:track:(.*)$')
        self.pattern_cd_folders = re.compile('^.*(CD)[0-9]{1,2}')
        values = list()
        #print(str(len(album_no_cover.fetchall())) + " albums without cover image")
        #print(album_no_cover)
        album_no_cover = album_no_cover.fetchall()
        for album in album_no_cover:
            cover_path = self.__find_file(album)
            if cover_path is not None:
                values.append([cover_path, album[0]])
            else:
                print("No cover found for '" + album[1] + "'")

        c.executemany("UPDATE album_cover SET cover_path = ? WHERE uri = ?", values)
        conn.commit()
        conn.close()
        
        return len(values)
