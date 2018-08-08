import sqlite3
import configparser

from scan_update_db import DBUpdater

from flask import Flask, jsonify, make_response, g, send_file
from flask_restful import Api

dbupdater = DBUpdater()

flask_app = Flask(__name__)
flask_api = Api(flask_app)

db_file = dbupdater.get_db_file()
music_base_dir = dbupdater.get_music_base_dir()

#conn = sqlite3.connect(db_file)
#c = conn.cursor()

@flask_app.route('/')
def index():
    return make_response(jsonify({"status": "success", "message": "Hello World!"}), 200)

@flask_app.route('/update_all/')
def update_all():
    #print("Updating all")
    result = dbupdater.update_all()
    
    json_string = {
        "status": "success", 
        "message": "Updated " + str(result) + " covers"
    }
    return make_response(jsonify(json_string), 200)

@flask_app.route('/update_missing/')
def update_missing():
    #print("Updating missing")
    result = dbupdater.update_missing()
    
    json_string = {
        "status": "success", 
        "message": "Updated " + str(result) + " covers"
    }
    return make_response(jsonify(json_string), 200)
    
@flask_app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_db', None)
    if db is not None:
        db.close()

result = None
@flask_app.route('/image/<string:album>/<string:artist>/')
def image_request(album, artist):
    variables = [artist, album]
    c = dbupdater.get_db(True).cursor()
    result = c.execute("SELECT artist.name, album.name, album_cover.cover_path FROM artist INNER JOIN album ON artist.uri = album.artists INNER JOIN album_cover ON album_cover.uri = album.uri WHERE artist.name = ? AND album.name = ? AND (album_cover.cover_path IS NOT NULL OR album_cover.cover_path != '')", variables)
    rows = result.fetchall()
    
    if len(rows) == 1:
        print(rows[0]["cover_path"])
        return send_file(rows[0]["cover_path"])
    
    if len(rows) > 1:
        json_string = {
            "status": "error", 
            "message": "Multiple possible covers found"
        }
        return make_response(jsonify(json_string), 200)
    
    json_string = {
        "status": "error",
        "message": "No cover found for '" + album + "' by '" + artist + "'"
    }
    return make_response(jsonify(json_string), 200)
