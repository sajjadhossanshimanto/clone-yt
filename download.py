# standard modules
from os.path import exists, join, splitext
import sys
import signal
from typing import Text
import atexit


from firedm.config import Status

from firedm.controller import Controller
from firedm.cmdview import CmdView
from firedm.setting import load_setting
from firedm import FireDM
from firedm.utils import log
from util import list_video_folder, load_secssion, write_secssion, download_thumbnail
import time
import util


# url='https://youtu.be/nkQz3X8pAAE'
# url='https://youtu.be/-muH9uOf5Jc'
# FireDM.main(['firedm', '--dlist', '--interactive', url])
# FireDM.main(['firedm', '--help'])
# FireDM.main(['firedm'])
'''
/home/kali/.vscode/extensions/ms-python.python-2021.11.1422169775/pythonFiles/lib/jedilsp
jedi
parso
pydantic
pygls
typegrud
'''
# exit()


load_setting()
controller = Controller(view_class=CmdView)
controller.run()

def cleanup():
    controller.quit()
    time.sleep(2)  # give time to other threads to quit
atexit.register(cleanup)

def signal_handler(signum, frame):
    print('\n\nuser interrupt operation, cleanup ...')
    signal.signal(signum, signal.SIG_IGN)  # ignore additional signals
    util.run=False
    cleanup()
    print('\n\ndone cleanup ...')
    atexit.unregister(cleanup)
    sys.exit()
signal.signal(signal.SIGINT, signal_handler)


def download_d(d):
    controller._download(d, threaded=False)
    controller.view.progress=0
    
    # download thumblain
    download_thumbnail(d)

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
        sys.exit()
    else:
        d=controller.d_map[paused.pop()]
        download_d(d)

saved_video=list_video_folder()
secssion=load_secssion(sec_file)
while util.run:
    try:
        data=next(secssion)
    except StopIteration:
        log('whole database download completed')

    url=f'https://youtu.be/{data.video_id}'
    d=controller.process_url(url, threaded=False)[0]
    d.select_stream(quality='best')
    if d.title in saved_video:
        log(f'{d.title} is already exists. ')
        continue
        if d.extension!=saved_video[d.title]:
            log('video extention mismatched. re-downloading the best quality.')
            # os.remove
        elif 'check for incomplite':
            pass
        elif 'quality check by ffmpeg':
            pass
        else:
            continue
    
    loaded=controller.download(d=d, threaded=False)
    write_secssion(sec_file, data.index-1)
    log(f'download later secssion saved for {data.index-1}')
    if loaded:
        # start downloading file
        d=controller.download_q.get_nowait()
        download_d(d)
    else:
        log(f'error : {data.index} {data.title}')
    
    time.sleep(2)
