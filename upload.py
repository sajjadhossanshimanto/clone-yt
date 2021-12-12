#%%
import datetime
import json
import pickle
import sys
from os.path import exists, isfile, join, splitext
from urllib.parse import quote

from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from oauth2client.client import OAuth2Credentials
from requests import post

from config import credential_file, thumbnail_folder, video_folder
from firedm.utils import log, validate_file_name
from firedm.video import get_media_info, load_extractor_engines
from secrect import client_id, client_secret, refresh_token
from util import (download_thumbnail, load_secssion, thumbnail_ext,
                  write_secssion, list_video_folder)
from youtube_upload.main import get_category_id, get_progress_info
from youtube_upload.upload_video import upload


scope = ["https://www.googleapis.com/auth/youtube"]
sec_file='last_upload'

#%%
def get_token():
    refresh_url = "https://oauth2.googleapis.com/token"

    data = {
        "grant_type":"refresh_token",
        "client_id":quote(client_id),
        "client_secret":quote(client_secret),
        "refresh_token":quote(refresh_token)
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    response = post(refresh_url, headers=headers, data=data)
    response = response.json()
    if 'error' in response:
        print('An error ocure while fatching access token')
        print(f'response: "{response}"')
        sys.exit()
    
    return response['access_token'], response['expires_in']

def generate_credential():
    access_token, expires_in = get_token()
    print('access token received.')

    token_data = {
        'access_token' : access_token,
        'token_uri': 'https://accounts.google.com/o/oauth2/token',
        'user_agent' : 'some Automation',
        'client_id' : client_id,
        'client_secret': client_secret,
        'refresh_token' : refresh_token,
        'token_expiry' : None,
        'invalid' : True,
        'scopes': scope
    }
    cred = OAuth2Credentials.from_json(json.dumps(token_data))

    delta = datetime.timedelta(seconds=int(expires_in))
    cred.token_expiry = delta + datetime.datetime.utcnow()
    return cred

def save_credential(cred):
    with open(credential_file, 'wb') as f:
        pickle.dump(cred, f)

def load_credential():
    if not isfile(credential_file):
        return
    
    with open(credential_file, 'rb') as f:
        try:
            cred:OAuth2Credentials = pickle.load(f)
        except:
            return

def get_youtube_handler():
    cred = load_credential()
    if cred and cred.access_token_expired:
        cred.refresh(Request())
        save_credential(cred)
    else:
        cred = generate_credential()
        save_credential(cred)

    print('builing youtube handler')
    return build("youtube", "v3", credentials=cred)


def upload_youtube_video(video_path, info):
    title=info['title']
    tags=info['tags']
    description=info['description']
    category_id = get_category_id(info['categories'][0])
    del info

    progress = get_progress_info()
    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": category_id,
            "tags": tags,
            "defaultLanguage": 'en',
            "defaultAudioLanguage": 'en',
        },
        "status": {
            "embeddable": True,
            "privacyStatus": "private",
            "license": 'youtube',
        }
    }

    print("Start upload: {0}".format(video_path))
    try:
        video_id = upload(youtube, video_path,
                        request_body, progress_callback=progress.callback)
    finally:
        progress.finish()
    
    return video_id

def set_thumb(video_id, path):
    youtube.thumbnails().set(videoId=video_id, media_body=path).execute()


video_list=list_video_folder()

if not video_list:
    print('no downloaded file exist')
    sys.exit()

secssion=load_secssion(sec_file)
try:
    data=next(secssion)
except StopIteration:
    log('whole database upload completed')


load_extractor_engines()
url=f'https://youtu.be/{data.video_id}'
info=get_media_info(url)

title=info['title']
title=validate_file_name(title)
if title not in video_list:
    print(f'file not exist to upload: "{title}"')
    sys.exit()

video_file=join(video_folder, title+video_list[title])
thumb_file=join(thumbnail_folder, data.video_id+thumbnail_ext)
if not exists(thumb_file):
    thumb_file=download_thumbnail(info=info)

youtube=get_youtube_handler()
my_video_id=upload_youtube_video(video_file, info)

write_secssion(sec_file, data.index-1)
set_thumb(my_video_id, thumb_file)

