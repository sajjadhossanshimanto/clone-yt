import atexit
from functools import  partial
from dataclasses import dataclass, field, make_dataclass
from sqlalchemy import orm, Table, select, create_engine, MetaData
from os.path import join, exists, isfile, splitext
import os
from requests import get
from config import thumbnail_folder, db_file, table_name, video_folder


run=True
thumbnail_ext='.webp'
video_ext=('mp4', 'webm')

def download_thumbnail(d=None, info=None):
    print('downloading thumbnail')
    # url=f"https://i.ytimg.com/vi_webp/{video_id}/maxresdefault.webp"
    if d:
        url=d.thumbnail_url
        video_id=d.url.rsplit('=', 1)[-1]
    else:
        url=info['thumbnail']
        video_id=info['webpage_url_basename']
    
    path=join(thumbnail_folder, video_id)
    path+=thumbnail_ext
    with open(path, 'wb') as fb:
        fb.write(get(url).content)
    
    return path

def list_video_folder():
    video_list={}
    for file in os.listdir(video_folder):
        video_file=join(video_folder, file)
        if isfile(video_file) and file.endswith(video_ext):
            file, ex = splitext(file)
            video_list[file]=ex
    return video_list

#%%
class Inverse_IO:
    def __init__(self, path) -> None:
        self.file=path

    def inverse_read(self):
        with open(self.file, "a") as f:
            pos=f.tell()# end of file

        with open(self.file, encoding='utf-8', errors='ignore') as f:
            f.seek(pos)
            while f.tell()!=0:
                pos=pos-1
                f.seek(pos)
                char=f.read(1)
                f.seek(pos)
                yield char

    def inverse_read_line(self):
        line=''
        reader = self.inverse_read()
        while True:
            try:
                char=next(reader)
            except StopIteration:
                yield line
                break

            if char!='\n':
                line=char+line
            elif line:
                yield line
                line=''

#%%
@dataclass
class Row:
    index:int
    video_id:str
    title:str = field(repr=False)
    publish_at:str

#%%
class load_secssion:
    def __init__(self, sec_file) -> None:
        url=f'sqlite:///{db_file}'
        engine = create_engine(url)

        metadata = MetaData()
        session = orm.sessionmaker(bind=engine)
        self.session = session()
        self.table=Table(table_name, metadata, autoload_with=engine)

        self.rows=self.read_inverse(self.stored_index(sec_file))

    def read_inverse(self, from_=None):
        stmt=select(self.table).order_by(self.table.c.index.desc())
        if isinstance(from_, int):
            # stored section indicates what needs to downloaded
            stmt=stmt.where(self.table.c.index<=from_)

        for row in self.session.execute(stmt):
            yield Row(*row)

    def stored_index(self, sec_file):
        if not exists(sec_file):
            return None

        try:
            last_index=Inverse_IO(sec_file).inverse_read_line().__next__()
        except StopIteration:
            return None

        try:
            last_index=int(last_index)
        except ValueError:
            return None
            
        return last_index
    
    def __iter__(self):
        return self

    def __next__(self):
        return next(self.rows)


def write_secssion(sec_file, n):
    try:
        last_char=next(Inverse_IO(sec_file).inverse_read())
    except StopIteration:
        last_char='\n'
    
    n=str(n)
    with open(sec_file, 'a') as f:
        if last_char!='\n':
            f.write('\n')
        f.write(n+'\n')
