#!/usr/bin/env python

from datetime import datetime
import os
import sqlite3
import urwid

rows = []

current_item = 0

def menu():
    global rows
    
    conn = sqlite3.connect('/home/mylk/.local/share/liferea/liferea.db')
    c = conn.cursor()
    rows = c.execute("SELECT datetime(date, 'unixepoch') AS date, n.title AS source, i.item_id, i.title, i.source FROM items i INNER JOIN node n ON n.node_id = i.node_id AND i.read = 0 AND i.parent_item_id = 0 ORDER BY date ASC")

    txt = urwid.Text(datetime.now().strftime('%c'))
    body = [txt, urwid.Divider()]

    for row in rows:
        button = urwid.Button('{:<210} {}'.format(row[3], row[0]))
        urwid.connect_signal(button, 'click', item_chosen, row)
        body.append(urwid.AttrMap(button, None, focus_map='reversed'))
    
    conn.close()
    
    return urwid.SimpleListWalker(body)


def item_chosen(button, row):
    global current_item

    conn = sqlite3.connect('/home/mylk/.local/share/liferea/liferea.db')
    c = conn.cursor()
    c.execute('update items set read = 1 where item_id = ?', (row[2],))
    conn.commit()
    conn.close()
    
    refresh(None, None)

    os.system('/usr/bin/firefox --new-tab {}'.format(row[4]))


def exit_program(button):
    raise urwid.ExitMainLoop()


def exit_on_q(key):
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()


def refresh(_loop, _data):
    menuz.clear()

    txt = urwid.Text(datetime.now().strftime('%c'))
    
    menuz.append(txt)
    menuz.append(urwid.Divider())

    global rows
    conn = sqlite3.connect('/home/mylk/.local/share/liferea/liferea.db')
    c = conn.cursor()
    rows = c.execute("SELECT datetime(date, 'unixepoch') AS date, n.title AS source, i.item_id, i.title, i.source FROM items i INNER JOIN node n ON n.node_id = i.node_id AND i.read = 0 AND i.parent_item_id = 0 ORDER BY date ASC")

    for row in rows:
        button = urwid.Button('{:<210} {}'.format(row[3], row[0]))
        urwid.connect_signal(button, 'click', item_chosen, row)
        menuz.append(urwid.AttrMap(button, None, focus_map='reversed'))

    conn.close()

    loop.set_alarm_in(60, refresh)

def wtf(key, _loop):
    global current_item
    global menuz

    if 'up' in key:
        if current_item > 0:
            current_item -= 1
    elif 'down' in key:
        if current_item < (len(menuz) - 3):
            current_item += 1

    return key


menuz = menu()

main = urwid.Padding(urwid.ListBox(menuz), left=2, right=2)
top = urwid.Overlay(
    main,
    urwid.SolidFill(),
    align='left',
    width=('relative', 300),
    valign='top',
    height=('relative', 250),
    min_width=20,
    min_height=5
)

loop = urwid.MainLoop(top, palette=[('reversed', 'standout', '')], unhandled_input=exit_on_q, input_filter=wtf)
loop.set_alarm_in(60, refresh)
loop.run()

