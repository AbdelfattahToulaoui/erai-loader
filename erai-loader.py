#!/usr/bin/env python3

import curses
import feedparser
import time
from datetime import datetime
import re
import subprocess
import sys

def download_torrent(url):
    try:
        cp = subprocess.run(["deluge-console", "add", url],
            capture_output=True, encoding='utf8')
        if not 'Torrent added!' in cp.stdout:
            m = re.search('AddTorrentError: (.*)', cp.stdout)
            return m.group(1)
    except:
        return 1
    return 0

help = '↑: up, ↓: down, q: quit, r: refresh, ENTER: download'

def draw_borders(scr, lines, cols):
    for i in range(2, lines-2):
        scr.addstr(i, 1, '│')
        scr.addstr(i, cols-2, '│')
    for i in range(2, cols-2):
        scr.addstr(1, i, '═')
        scr.addstr(lines-2, i, '═')
        scr.addstr(lines-5, i, '═')
    scr.addstr(1, 1, '╒')
    scr.addstr(1, cols-2, '╕')
    scr.addstr(lines-2, 1, '╘')
    scr.addstr(lines-2, cols-2, '╛')
    scr.addstr(lines-5, 1, '╞')
    scr.addstr(lines-5, cols-2, '╡')

def loadfeed():
    if len(sys.argv)<2:
        r = 'all'
    else:
        r = sys.argv[1]
    if not r in ['480', '720', '1080', 'movies-480', 'movies-720', 'movies-1080',
            'batch-480', 'batch-720', 'batch-1080',
            'raws-720', 'raws-1080', 'encoded-720', 'encoded-1080', 'all']:
        raise Exception('Invalid resolution')
    url = 'https://www.erai-raws.info/rss-%s/'%r
    feed = feedparser.parse(url)
    return feed

def main(stdscr):
    pos = 0
    feed = loadfeed()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.curs_set(False)
    stdscr.bkgd(' ', curses.color_pair(1) | curses.A_BOLD)
    start = 0
    message = ''
    while True:
        curses.update_lines_cols()
        stdscr.noutrefresh()
        stdscr.erase()
        draw_borders(stdscr, curses.LINES, curses.COLS)
        timenow = datetime.utcnow().timestamp()
        full = (curses.LINES - 8)//2
        width = curses.COLS - 4
        if pos >= start+full:
            start = pos - full + 1
        elif pos < start:
            start = pos
        elements = feed["items"]
        tit = feed[ "channel" ][ "description" ]
        if len(tit) > width - 2:
            tit = tit[:width - 5] + '...'
        stdscr.addstr(1, 2, tit)
        for i, el in enumerate(elements[start:start+full]):
            if pos != i+start:
                mode = curses.A_NORMAL
            else:
                mode = curses.A_REVERSE
            title = el['title']
            if len(title)>width:
                t = title.rpartition('–')
                title = title[:width-len(t[-1])-4] + '...' + t[1] + t[2]
            else:
                title = title + ' '*(width-len(title))
            date = el['published_parsed']
            tm = timenow - time.mktime(date)
            if tm<60:
                date = 'Just now'
            elif tm<3600:
                date = '%d minute(s) ago'%(tm//60)
            elif tm<3600*24:
                date = '%d hour(s) ago'%(tm//3600)
            elif tm < 3600*48:
                date = datetime.fromtimestamp(
                        time.mktime(date)).strftime('Yesterday %H:%M:%S')
            else:
                date = datetime.fromtimestamp(
                        time.mktime(date)).strftime('%d/%m/%Y %H:%M:%S')
            date = date + ' '*(width-len(date))
            stdscr.addstr(2 + i*2, 2, title, mode)
            stdscr.addstr(3 + i*2, 2, date , mode)
        stdscr.addstr(curses.LINES-5, 3, 'Messages:')
        stdscr.addstr(curses.LINES-4, 2, message
                if len(message)<width
                else message[:width-3]+'...')
        stdscr.addstr(curses.LINES-1, 2, help
                if len(help)<width
                else help[:width-3] + '...')
        key = stdscr.getch()
        if key==curses.KEY_UP:
            pos -= 1
        elif key == curses.KEY_DOWN:
            pos += 1
        elif key == curses.KEY_PPAGE:
            pos -= full
        elif key == curses.KEY_NPAGE:
            pos += full
        elif key in [curses.KEY_ENTER, ord('\n')]:
            message = 'Adding Torrent...'
            message += ' '*(width-len(message))
            stdscr.addstr(curses.LINES-4, 2, message)
            stdscr.refresh()
            tor = download_torrent(elements[pos]['link'])
            if tor == 0:
                message = 'Torrent added!'
            elif tor == 1:
                message = 'Unknown error'
            else:
                message = str(tor)
        elif key == ord('q'):
            break
        elif key == ord('r'):
            message = 'Refreshing feed'
            message += ' '*(width-len(message))
            stdscr.addstr(curses.LINES-4, 2, message)
            stdscr.refresh()
            feed = loadfeed()
            pos = 0
            message=''
        if pos < 0:
            pos = 0
        elif pos >= len(elements):
            pos = len(elements) - 1

curses.wrapper(main)

