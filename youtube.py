#%%
from os import remove
from secrect import api_key
import pyyoutube
import json
import atexit
import requests
from functools import cached_property
from os.path import exists
import csv
from pyyoutube.models.search_result import SearchListResponse


# %%
api = pyyoutube.Api(api_key=api_key)

#%%
class Video_id:
    def __init__(self, channel_id) -> None:
        self.channel_id=channel_id
        self.name=None
        self.total_video=0
        self.fetch_coint=0
        
        self.sec_file=f"{self.channel_id}_id.sec"
        self.token={
                'pre':'',
                'next':''
            }
        self.pre_load()
        atexit.register(self.save_secssion)
    
    def pre_load(self):
        info=api.get_channel_info(channel_id=self.channel_id).items[0]
        
        self.name=info.snippet.title
        self.total_video=int(info.statistics.videoCount)
    
    def search(self, date=None):
        # api.search(parts='id', channel_id=self.channel_id, order='date', count=self.total_video)
        url = f"https://www.googleapis.com/youtube/v3/search?key={self.api_key}&channelId={self.channel_id}&part=snippet,id&order=date&maxResults={self.total_video}"
        if date:
            url+=f'&publishedBefore={date}'
        
        res=requests.get(url).json()
        res=SearchListResponse.from_dict(res)

        while True:
            for i in res.items:
                yield (i.id.videoId, i.snippet.title, i.snippet.publishedAt)

            next_page=res.nextPageToken
            if not next_page:
                break

            res=requests.get(f'{url}&pageToken={next_page}').json()
            res=SearchListResponse.from_dict(res)


    def _content_id(self, skip_count=0)->str:
        result=api.search
        result=iter(result.items)

        for _ in range(skip_count):
            next(result)
            self.fetch_coint+=1

        for i in result:
            if i.id.kind.endswith('video'):
                self.fetch_coint+=1
                yield i.id.videoId
    
    def dump(self, from_=None):
        from_=from_ or self._content_id()
        with open(f"{self.name}.csv", 'a') as f:
            writer=csv.writer(f)
            for i in from_:
                writer.writerow(i)
                f.flush()
                # break
        
        atexit.unregister(self.save_secssion)

    def inverse_read(self):
        with open(f'{self.name}.csv', "a") as f:
            while f.tell()!=0:
                pos=f.tell()-1
                f.seek(pos)
                char=f.read(1)
                f.seek(pos)
                yield char

    def inverse_read_line(self):
        line=''
        for char in self.inverse_read():
            if char!='\n':
                line+=char
            elif line:
                yield line
                line=''

    def resume_dump(self):
        if exists(self.sec_file):
            with open(self.sec_file) as f:
                sec=json.load(f)
            total_video=sec['total_video']
            fetched=sec['fetched']
            self.token=sec['token']

            new_upload=self.total_video-total_video
            print(f'{new_upload} new videos uploaded ever since last fetch')
            
            _from=self._content_id(skip_count=fetched+new_upload)
            self.dump(_from)
            remove(self.sec_file)
            return

        last_id=next(self.inverse_read_line())
        _from=self._content_id()
        for id in _from:
            if id==last_id:
                break
        else:
            print('last video id find failed for unknown reason')
        
        self.dump(_from)

    def save_secssion(self):
        sec={
            'total_video':self.total_video,
            'fetched':self.fetch_coint,
            'token':self.token
        }
        with open(self.sec_file, 'w') as f:
            json.dump(sec, f)


# %%
# channel_name='Drzakirchannel'
channel_id='UC3YmP7nqf514I1zh1eVbzrA'
# Video_id(channel_id).dump()


#%%
def base(video_count=10):
    url = f"https://www.googleapis.com/youtube/v3/search?key={api_key}&channelId={channel_id}&part=snippet,id&order=date&maxResults={video_count}"
    
    return url

p=base()
print(p)
# %%
