# standard modules
from os.path import exists, join
import sys
import signal
from typing import Text
import atexit

from sqlalchemy.sql.coercions import StatementOptionImpl
from firedm.config import Status

from firedm.controller import Controller
from firedm.cmdview import CmdView
from firedm.setting import load_setting
from firedm import FireDM
from firedm.video import get_media_info, load_extractor_engines
from firedm.utils import download as direct_download, log, threaded
from util import load_secssion, thumbnail_folder, table_name, write_secssion
import time


# url='https://youtu.be/nkQz3X8pAAE'
# url='https://youtu.be/-muH9uOf5Jc'
# FireDM.main(['firedm', '--dlist', '--interactive', url])
# FireDM.main(['firedm', '--help'])
# FireDM.main(['firedm'])



# exit()

load_setting()
controller = Controller(view_class=CmdView)

def cleanup():
    controller.quit()
    time.sleep(2)  # give time to other threads to quit
atexit.register(cleanup)

def signal_handler(signum, frame):
    print('\n\nuser interrupt operation, cleanup ...')
    signal.signal(signum, signal.SIG_IGN)  # ignore additional signals
    cleanup()
    print('\n\ndone cleanup ...')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


def download_d(d, video_id=''):
    controller._download(d, threaded=False)
    # download thumblain
    video_id=video_id or d.url.rsplit('=', 1)[-1]
    video_id+='.jpg'
    direct_download(d.thumbnail_url, join(thumbnail_folder, video_id), decode=False)

    # delete from downloaded list
    controller.d_map.pop(d.uid, None)


sec_file='last_download'

paused=list(
    filter(
        lambda x:controller.d_map[x].status!=Status.completed,
        controller.d_map
    )
)
if paused:
    log('resuming previous download.')
    
    if len(paused)>1:
        log('Error: multiple paused video found')
    else:
        d=controller.d_map[paused.pop()]
        download_d(d)
else:
    secssion=load_secssion(sec_file)
    try:
        data=next(secssion)
    except StopIteration:
        log('whole database download completed')

    url=f'https://youtu.be/{data.video_id}'
    controller.process_url(url, threaded=False)
    loaded=controller.download(video_idx=0, threaded=False)
    
    write_secssion(sec_file, data.index-1)
    log(f'download later secssion saved for {data.index-1}')
    if loaded:
        # start downloading file
        d=controller.download_q.get_nowait()
        d.select_stream(quality='best')
        download_d(d, data.video_id)
    
