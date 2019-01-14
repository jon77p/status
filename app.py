from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from zerotierls import ztls
from flask_basicauth import BasicAuth
from os import path, environ
import pyspeedtest
from datetime import datetime
import subprocess
import pyfiglet
import requests
import time
import config

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['BASIC_AUTH_USERNAME'] = config.USERNAME
app.config['BASIC_AUTH_PASSWORD'] = config.PASSWORD
app.config['BASIC_AUTH_REALM'] = 'status page'

socketio = SocketIO(app)
basic_auth = BasicAuth(app)

@app.route('/')
@basic_auth.required
def index():
    return render_template('index.html')

@socketio.on('connect')
def connect():
    print('Client connected!')
    emit('enter', {'data': config.OS})

@socketio.on('welcome')
def welcome(message):
    emit('fromserver', {'data': 'Welcome ' + app.config['BASIC_AUTH_USERNAME'] + '!'})
    emit('fromserver', {'data': 'Detected OS: ' + ' '.join(message['data'].split(' ')[2:7])[:-1]})
    emit('fromserver', {'data': 'Current Browser: ' + message['data'].split(' ')[-1]})
    # test = speedtest()
    # emit('fromserver', {'data': 'Current Speed: ' + str(test[0]) + 'UP | ' + str(test[1]) + 'DOWN'})
    currenttime = datetime.now()
    emit('fromserver', {'data': 'Today is: ' + currenttime.strftime("%m/%d/%Y")})
    emit('fromserver', {'data': 'The current system time is: ' + currenttime.strftime("%I:%M %p")})

@socketio.on('disconnectme')
def disconnectme(message):
    print(message['data'])
    print('Client disconnected.')
    emit('disconnectme', {'data': 'Disconnected from server.'})

@socketio.on('jsonbutton')
def jsonbutton(message):
    print(message["data"])
    if message["data"] == "ztls":
        emit('fromserver', {'data': 'Sending ZeroTier Data...'})
        res = ztls()
        emit('send', {'data': {'msg': 'ztls', 'data': res}})
        emit('fromserver', {'data': 'Completed!'})
    elif message["data"] == "refreshpip":
        subprocess.run(["pip3", "install", "-r", "requirements.txt"])
        emit('fromserver', {'data': 'Completed!'})
        test = pyfiglet.figlet_format("test")
        emit('fromserver', {'data': test})
    elif message["data"] == "webstat":
        if (message["sites"]):
            emit('fromserver', {'data': 'Got command, checking website statuses...'})
            for site in message["sites"]:
                print("Querying site: " + site)
                try:
                    req = requests.get(site)
                    print(req)
                    code = str(req.status_code)
                except Exception as msg:
                    print(msg)
                    code = "400"
                emit('fromserver', {'data': '<a href=\'' + site + '\' target=\'__blank\'>' + site + '</a>' + ": " + code})
    elif message["data"].split("-")[0] == "spot":
        if message["data"].split("-")[1] == "np":
            np_data = getspotify_np()
            emit('send', {'data': {'msg': 'spot-np', 'data': np_data}})
            emit('fromserver', {'data': 'Completed!'})
            emit('fromserver', {'data': '<em>Now Playing: <a href="' + np_data["uri"] + '"><b>' + np_data["track"] + '</b> by <b>' + np_data["artist"] + '</b></a></em>'})
        elif message["data"].split("-")[1] == "control":
            command = message["data"].split("-")[2]
            emit('fromserver', {'data': "Executing control command '" + command + "'..."})
            spotify_control(command)
            emit('fromserver', {'data': "Completed!"})
            time.sleep(1)
            if command == "next" or command == "previous":
                emit('send', {'data': {'msg': 'spot-np', 'data': getspotify_np()}})
                emit('fromserver', {'data': 'Completed!'})
        elif message["data"].split("-")[1] == "search":
            query = message["query"]
            emit('fromserver', {'data': 'Received Query: ' + query})
            search_data = getspotify_search(query)
            emit('send', {'data': {'msg': 'spot-search', 'data': search_data}})
        elif message["data"].split("-")[1] == "track":
            nowplaying = getspotify_np()
            trackid = nowplaying["uri"].split(":")[2]
            trackdata = getspotify_trackdata(trackid)
            emit('fromserver', {'data': 'Completed!'})
            emit('send', {'data': {'msg': 'spot-track-data', 'data': trackdata}})
    else:
        emit('fromserver', {'data': "Uncaught json message received! Message was: " + message["data"]})
    
def tokenreauth():
    app_token = environ["SPOTAPPTOKEN"]
    refresh_token = environ["SPOTREFRESHTOKEN"]
    url = 'https://accounts.spotify.com/api/token'
    headers = {'Authorization': 'Basic ' + app_token}
    data = {'grant_type': 'refresh_token', 'refresh_token': refresh_token}
    req = requests.post(url, headers=headers, data=data)
    res = req.json()
    environ["SPOTAUTHTOKEN"] = res['access_token']
    return tokenreader()

def tokenreader():
    try:
        return environ["SPOTAUTHTOKEN"]
    except:
        return tokenreauth()

def getspotify_np():
    
    url = "https://api.spotify.com/v1/me/player/currently-playing"
    headers = {'Authorization': 'Bearer ' + tokenreader()}
    req = requests.get(url, headers=headers)

    try:
        if req.status_code == 200:
            req = req.json()
            if req["context"]["type"] == "playlist":
                req2 = requests.get(req["context"]["href"], headers=headers)
                # if req2.status_code == 200:
                req2 = req2.json()
                colors = getartworkcolors(req["item"]["album"]["images"][0]["url"])
                return {"context": {"data": req2, "np_type": req["currently_playing_type"], "href": req["context"]["href"], "type": req["context"]["type"]}, "track": req["item"]["name"], "artist": req["item"]["artists"][0]["name"], "uri": req["item"]["uri"], "img": req["item"]["album"]["images"][0]["url"], "time": req["item"]["duration_ms"] - req["progress_ms"], "source": {"type": req2["type"], "name": req2["name"], "uri": req2["uri"], "creator": req2["owner"]["display_name"]}, "colors": colors}
            else:
                colors = getartworkcolors(req["item"]["album"]["images"][0]["url"])
                return {"context": {"np_type": req["currently_playing_type"], "href": req["context"]["href"], "type": req["context"]["type"]}, "track": req["item"]["name"], "artist": req["item"]["artists"][0]["name"], "uri": req["item"]["uri"], "img": req["item"]["album"]["images"][0]["url"], "time": req["item"]["duration_ms"] - req["progress_ms"], "colors": colors}
        else:
            tokenreauth()
            return getspotify_np()
            # return {"track": "N/A", "artist": "N/A", "uri": "spotify://", "img": "null", "time": "-1"}
    except:
        tokenreauth()
        url = "https://api.spotify.com/v1/me/player/currently-playing"
        headers = {'Authorization': 'Bearer ' + tokenreader()}
        # headers = {'Authorization': 'Bearer ' + tokenreauth()}
        req = requests.get(url, headers=headers).json()
        try:
            colors = getartworkcolors(req["item"]["album"]["images"][0]["url"])
            return {"context": {"np_type": req["currently_playing_type"], "href": req["context"]["href"], "type": req["context"]["type"]}, "track": req["item"]["name"], "artist": req["item"]["artists"][0]["name"], "uri": req["item"]["uri"], "img": req["item"]["album"]["images"][0]["url"], "time": req["item"]["duration_ms"] - req["progress_ms"], "colors": colors}
        except:
            return {"track": "N/A", "artist": "N/A", "uri": "spotify:track:n/a", "img": "null", "time": "-1", "colors": "null"}

def getartworkcolors(image):
    url = "http://mkweb.bcgsc.ca/color-summarizer/?url="
    try:
        req = requests.get(url + image + "&precision=low&json=1").text
    except Exception as msg:
        req = str(msg)

    req = "coming soon"
    return req

def getspotify_search(query):
    fmt_query = query.replace(" ", "%20")
    url = "https://api.spotify.com/v1/search?q=" + fmt_query + "&type=track&limit=10"
    headers = {'Authorization': 'Bearer ' + tokenreader()}
    req = requests.get(url, headers=headers).json()
    try:
        req["tracks"]
        return req
    except:
        tokenreauth()
        url = "https://api.spotify.com/v1/search?q=" + fmt_query + "&type=track&limit=10"
        headers = {'Authorization': 'Bearer ' + tokenreader()}
        req = requests.get(url, headers=headers).json()
        return req

def getspotify_trackdata(trackid):
    url1 = "https://api.spotify.com/v1/audio-analysis/" + trackid
    url2 = "https://api.spotify.com/v1/audio-features/" + trackid
    headers = {'Authorization': 'Bearer ' + tokenreader()}
    req1 = requests.get(url1, headers=headers).json()
    req2 = requests.get(url2, headers=headers).json()
    try:
        return {"audio-analysis": req1, "audio-features": req2}
    except:
        tokenreauth()
        headers = {'Authorization': 'Bearer ' + tokenreader()}
        req1 = requests.get(url1, headers=headers).json()
        req2 = requests.get(url2, headers=headers).json()
        return {"audio-analysis": req1, "audio-features": req2}

def spotify_control(command):
    url = "https://api.spotify.com/v1/me/player/" + command
    headers = {'Authorization': 'Bearer ' + tokenreader()}
    if command == "pause" or command == "play":
        req = requests.put(url, headers=headers)
        return req
    else:
        req = requests.post(url, headers=headers)
        return req

def speedtest():
    return (1, 1)
    # st = pyspeedtest.SpeedTest()
    # return (st.download(), st.upload())

@app.context_processor
def utility_processor():
    def getos():
        return path.expandvars('${OS}')
    return dict(getos=getos)
if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)
