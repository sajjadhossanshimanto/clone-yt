import atexit
from functools import  partial
from dataclasses import dataclass, field, make_dataclass
from sqlalchemy import orm, Table, select, create_engine, MetaData
from sqlalchemy.sql.expression import false
from os.path import join, exists


video_folder='video'
thumbnail_folder='video/thumbnail'
table_name='DrZakirNaik'
db_file='Youtube.db'

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
        
        while 1:# do not raise Exception
            yield ''# receing empty string means end of line

#%%
@dataclass
class Row:
    index:int
    video_id:str
    title:str = field(repr=False)
    publish_at:str

#%%
class Db_table:
    def __init__(self, db_file, table_name) -> None:
        url=f'sqlite:///{db_file}'
        engine = create_engine(url)

        metadata = MetaData()
        session = orm.sessionmaker(bind=engine)
        self.session = session()
        self.table=Table(table_name, metadata, autoload_with=engine)

    def create_data_class(self, index_key):
        self.index_column=None
        instance=[]
        for column in self.table.columns:
            column_name=column.name
            column_type=column.type.python_type
            if not self.index_column and column_name==index_key:
                self.index_column=column
                repr=True
                instance.append((column_name, column_type, field(repr=True)))
                continue
                
            instance.append((column_name, column_type, field(repr=False)))

        if not self.index_column:
            raise ValueError(f'Index key("{index_key}") not found')
        
        self.row_data=make_dataclass("Row", instance)

    def read_inverse(self):
        stmt=select(self.table).order_by(self.table.c.index.desc())

        for row in self.session.execute(stmt):
            yield Row(*row)

    def nth_index(self, n):
        stmt=select(self.table).where(self.table.c.index==n).order_by(self.index_column.desc())

        row=self.session.execute(stmt).fetchone()
        return Row(*row)

    def __getitem__(self, n):
        return self.nth_index(n)

#%5
def read_secssion(db:Db_table, sec_file)-> Row:
    if exists(sec_file):
        # try:
        last_index=Inverse_IO(sec_file).inverse_read_line().__next__()
        try:
            last_index=int(last_index)
        except ValueError:
            row=next(db.read_inverse())
        else:
            row=db.nth_index(last_index)
    else:
        row=next(db.read_inverse())
    return row

def write_secssion(sec_file, n):
    n=str(n)
    with open(sec_file, 'a') as f:
        f.write(n)