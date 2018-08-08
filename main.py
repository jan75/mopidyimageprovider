import sqlite3
import re
import os
import os.path
import urllib.parse

db_file = '/var/lib/mopidy/local-sqlite/library.db'
music_base_dir = "/mnt/media01/Musik/"

conn = sqlite3.connect(db_file)
c = conn.cursor()

pattern_local_file = re.compile('^local:track:(.*)$')
pattern_cd_folders = re.compile('^.*(CD)[0-9]{1,2}')
def find_file(album):
    #album = [item.encode("utf-8") for item in album]
    #print("Searching for cover in album: '" + album[0] + "'")
    cover_path = ""
    if pattern_local_file.match(album[2]):
        cover_path = pattern_local_file.search(album[2]).group(1)
        cover_path = urllib.parse.unquote(cover_path, encoding='utf-8', errors='replace')
        cover_path = os.path.join(music_base_dir, cover_path)
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
    if pattern_cd_folders.match(cover_path):
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
                 

    
c.execute("CREATE TABLE IF NOT EXISTS album_cover(uri TEXT UNIQUE, name TEXT, cover_path TEXT, FOREIGN KEY (uri) REFERENCES album (uri))")
conn.commit()

album_list = c.execute("SELECT uri, name FROM album")
c.executemany("INSERT OR IGNORE INTO album_cover(uri, name) VALUES (?, ?)", album_list.fetchall())

album_no_cover = c.execute("SELECT album_cover.uri, album_cover.name, track.uri FROM album_cover INNER JOIN track ON track.album = album_cover.uri WHERE album_cover.cover_path IS NULL OR album_cover.cover_path = '' GROUP BY track.album")
conn.commit()

values = list()
for album in album_no_cover:
    cover_path = find_file(album)
    if cover_path is not None:
        values.append([cover_path, album[0]])
    '''
    if cover_path is not None:
        print("Found cover '" + cover_path + "' for album '" + album[1] + "'")
        values = [cover_path, album[0]]
        c.execute("UPDATE album_cover SET cover_path = ? WHERE uri = ?", values)
        conn.commit()
        '''

c.executemany("UPDATE album_cover SET cover_path = ? WHERE uri = ?", values)
conn.commit()
conn.close()
