#%%
from os.path import exists
from secrect import api_key, api3
import pyyoutube
import atexit
import requests
from functools import  partial
import csv
from pyyoutube.models.search_result import SearchListResponse


api_key=api3
# %%
api = pyyoutube.Api(api_key=api_key)

#%%
class Inverse_IO:
    def __init__(self, path) -> None:
        self.file=path

    def inverse_read(self):
        with open(self.file, "a") as f:
            end=f.tell()

        with open(self.file, encoding='utf-8', errors='ignore') as f:
            f.seek(end)
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
                line=char+line
            elif line:
                yield line
                line=''

#%%
class Video_id:
    def __init__(self, channel_id) -> None:
        self.channel_id=channel_id
        self.name=None
        self.total_video=0
        self.fetch_coint=0
        self.sec_file=f"{self.channel_id}_id.sec"
    
    def start(self):
        self.pre_load()
        if exists(self.name):
            self.resume_dump()
        else:
            self.dump()

    def pre_load(self):
        info=api.get_channel_info(channel_id=self.channel_id).items[0]
        
        self.name=info.snippet.title
        self.name=f'{self.name}.csv'
        self.total_video=int(info.statistics.videoCount)
    
    def search(self, date=None):
        # api.search(parts='id', channel_id=self.channel_id, order='date', count=self.total_video)
        url = f"https://www.googleapis.com/youtube/v3/search?key={api_key}&channelId={self.channel_id}&part=snippet,id&order=date&maxResults={self.total_video}"
        if date:
            url+=f'&publishedBefore={date}'
        
        res=requests.get(url).json()
        res=SearchListResponse.from_dict(res)

        while True:
            for i in res.items:
                if not i.id.kind.endswith('video'):
                    continue

                self.fetch_coint+=1
                print(self.fetch_coint, end='\r')
                yield (i.id.videoId, i.snippet.title, i.snippet.publishedAt)

            next_page=res.nextPageToken
            if not next_page:
                break

            res=requests.get(f'{url}&pageToken={next_page}').json()
            res=SearchListResponse.from_dict(res)
    
    def dump(self, from_=None):
        from_=from_ or self.search()
        with open(self.name, 'a') as f:
            writer=csv.writer(f)
            for i in from_:
                writer.writerow(i)
                f.flush()
                # break
        
    def resume_dump(self):
        last_date=next(Inverse_IO(self.name).inverse_read_line())
        last_date=last_date.rsplit(',', 1)[-1].strip()

        # print(last_date, self.fetch_coint)
        _from=self.search(last_date)
        self.dump(_from)



# %%
# channel_name='Drzakirchannel'
channel_id='UC3YmP7nqf514I1zh1eVbzrA'
# Video_id(channel_id)


#%%
##temp##
date='2012-08-05T03:38:51Z'
url = f"https://www.googleapis.com/youtube/v3/search?key={api_key}&channelId={channel_id}&part=snippet,id&order=date&maxResults=10&publishedBefore={date}"
# print(url)