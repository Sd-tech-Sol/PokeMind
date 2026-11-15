"""Capture the actual demo QWidget at intermediate animation times, never the desktop.

Uses existing FFmpeg, or existing Pillow for a GIF fallback; installs nothing.
No screen capture, account, network, production app or user data is involved.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from demo import DemoWindow, ROOT
from artwork import CARDS, render_card
from PySide6.QtCore import QPointF, QEvent, Qt
from PySide6.QtGui import QPainter, QColor, QPen, QEnterEvent
from PySide6.QtWidgets import QApplication


def seek(animation,time):
    """Sample the real Qt interpolation, preserving every intermediate state."""
    if animation.state()!=animation.State.Stopped:
        animation.pause()
        animation.setCurrentTime(min(time,animation.duration()))


def record(output, *, width=1280, height=880, fps=20, window_factory=DemoWindow,
           main_name='decklab-complete.png', small_height=None, export_art=True):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    frames_dir=output/'frames';frames_dir.mkdir(exist_ok=True)
    app=QApplication.instance() or QApplication([])
    window=window_factory();window.resize(width,height);window.show();app.processEvents()
    if hasattr(window,'reflow'):window.reflow();app.processEvents()
    if not window.grab().save(str(output/main_name)):raise RuntimeError('MAIN_CAPTURE_WRITE_FAILED')
    window.resize(1100,small_height or height);app.processEvents()
    if hasattr(window,'reflow'):window.reflow();app.processEvents()
    window.grab().save(str(output/'decklab-1100.png'))
    window.resize(width,height);app.processEvents()
    if hasattr(window,'reflow'):window.reflow();app.processEvents()
    if export_art:
        for i,card in enumerate(CARDS):
            render_card(i).save(str(output/('art-'+card['kind']+'.png')))
    actions=[];positions={}
    card=window.cards[1]
    hover_time,click_time,leave_time,tab_time,back_time=600,1400,2200,2900,4100
    try:
        for frame in range(120):
            t=round(frame*1000/fps)
            if t==hover_time:
                local=QPointF(card.rect().center())
                QApplication.sendEvent(card,QEnterEvent(local,local,local))
                actions.append('hover: Flamaris (real enterEvent, 220 ms)')
            if t==click_time:
                card.click();actions.append('select: Flamaris (real clicked signal)')
            if t in (1750, 2450) and hasattr(window, 'detail_toggle'):
                window.detail_toggle.click()
                actions.append('details: native toggle ' + str(window.detail_toggle.isChecked()))
            if t==leave_time:
                QApplication.sendEvent(card,QEvent(QEvent.Type.Leave));actions.append('leave: Flamaris')
            if t==tab_time:
                window.tabs.setCurrentIndex(2);actions.append('tab: Statistics (real AnimatedStack, 180 ms)')
            if t==back_time:
                window.tabs.setCurrentIndex(0);actions.append('tab: Gallery (real AnimatedStack, 180 ms)')
            if hover_time<=t<leave_time:seek(card.animation,t-hover_time)
            if t>=leave_time:seek(card.animation,t-leave_time)
            if click_time<=t<tab_time:seek(window.details.transition.animation,t-click_time)
            if tab_time<=t<back_time:seek(window.pages.transition.animation,t-tab_time)
            if t>=back_time:seek(window.pages.transition.animation,t-back_time)
            app.processEvents()
            picture=window.grab()
            # A cursor drawn only into the recording identifies the event target.
            # All scene pixels and movement come from the live QWidget above.
            if hover_time<=t<leave_time:
                position=card.mapTo(window,card.rect().center())
                painter=QPainter(picture);painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setPen(QPen(QColor('#FEFCFA'),2));painter.setBrush(QColor(7,20,47,150))
                painter.drawEllipse(position,7,7);painter.end()
            target=frames_dir/f'frame-{frame:04d}.png'
            if not picture.save(str(target)):raise RuntimeError('FRAME_WRITE_FAILED')
            positions[str(frame)]=round(card.hover,4)
        ffmpeg=shutil.which('ffmpeg')
        if ffmpeg:
            base=[ffmpeg,'-hide_banner','-loglevel','error','-y','-framerate',str(fps),'-i',str(frames_dir/'frame-%04d.png')]
            subprocess.run(base+['-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart','-an',str(output/'preview.mp4')],check=True,capture_output=True)
            subprocess.run(base+['-filter_complex','[0:v]split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=3',
                                 '-loop','0',str(output/'preview.gif')],check=True,capture_output=True)
        else:
            from PIL import Image
            frames=[Image.open(frames_dir/f'frame-{i:04d}.png').convert('RGB') for i in range(120)]
            frames[0].save(output/'preview.gif',save_all=True,append_images=frames[1:],duration=1000//fps,loop=0,optimize=False)
        report=dict(width=window.width(),height=window.height(),fps=fps,frames=120,seconds=120/fps,
                    renderer=app.platformName(),actions=actions,hover_samples=positions,
                    files=['preview.gif',main_name,'decklab-1100.png']+(['preview.mp4'] if ffmpeg else []),
                    original_art_count=len(CARDS),personal_data_access=False,network_used=False)
        (output/'recording.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({k:v for k,v in report.items() if k!='hover_samples'}))
        return report
    finally:
        window.close();window.deleteLater();app.processEvents()


def main():
    parser=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--output',type=Path,default=ROOT/'build/qa-premium-decklab-demo')
    args=parser.parse_args()
    record(args.output)


if __name__=='__main__':main()
