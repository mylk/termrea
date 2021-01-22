#!/usr/bin/env python

from datetime import datetime
import os
import sqlite3
import urwid

UPDATE_INTERVAL = 60
news_items = []


class Database():
    DB_PATH = '/home/mylk/.local/share/liferea/liferea.db'
    connection = None

    def get_connection(self):
        if not self.connection:
            self.connection = sqlite3.connect(self.DB_PATH)

        return self.connection

    def find_unread_news(self):
        connection = self.get_connection()
        cursor = connection.cursor()

        return cursor.execute('''
            SELECT datetime(date, 'unixepoch') AS date,
            n.title AS source,
            i.item_id,
            i.title,
            i.source AS url
            FROM items i
            INNER JOIN node n ON n.node_id = i.node_id
            AND i.read = 0
            AND i.parent_item_id = 0
            ORDER BY date ASC
        ''')

    def close_connection(self):
        self.get_connection().close()

    def set_item_read(self, item_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute('UPDATE items SET read = 1 WHERE item_id = ?', (item_id,))
        connection.commit()
        self.close_connection()


def generate_news_list():
    db = Database()
    rows = db.find_unread_news().fetchall()
    db.close_connection()

    global news_items
    news_items = rows

    txt = urwid.Text(datetime.now().strftime('%c'))
    news_list = [txt, urwid.Divider()]

    for row in rows:
        button = urwid.Button('{:<26} {:<103} {}'.format(row[1], row[3], row[0]))
        urwid.connect_signal(button, 'click', item_chosen, row)
        news_list.append(urwid.AttrMap(button, None, focus_map='reversed'))

    return urwid.SimpleListWalker(news_list)


def item_chosen(button, row):
    Database().set_item_read(row[2])

    index_with_focus = news_list.get_focus()[1]
    update_news_list(loop)

    # @TODO: blocks execution if firefox is closed
    os.system('/usr/bin/firefox --new-tab {}'.format(row[4]))


def exit_program(button):
    raise urwid.ExitMainLoop()


def handle_input(key):
    global news_items

    if key in ['q', 'Q']:
        raise urwid.ExitMainLoop()
    elif key == 'm':
        index_with_focus = news_list.get_focus()[1]

        focused_item = news_items[int(index_with_focus) - 2]
        Database().set_item_read(focused_item[2])
        update_news_list(loop)


def update_news_list(loop = None, data = None):
    index_with_focus = news_list.get_focus()[1]

    news_list.clear()

    txt = urwid.Text(datetime.now().strftime('%c'))
    news_list.append(txt)
    news_list.append(urwid.Divider())

    db = Database()
    rows = db.find_unread_news().fetchall()
    db.close_connection()

    global news_items
    news_items = rows

    for row in rows:
        button = urwid.Button('{:<26} {:<103} {}'.format(row[1], row[3], row[0]))
        urwid.connect_signal(button, 'click', item_chosen, row)
        news_list.append(urwid.AttrMap(button, None, focus_map='reversed'))

    # @TODO: handle case the item is the first and only
    if len(news_list) > index_with_focus:
        news_list.set_focus(index_with_focus)
    else:
        news_list.set_focus((index_with_focus - 1))


def schedule_and_update_news_list(loop = None, data = None):
    update_news_list(loop)

    loop.set_alarm_in(UPDATE_INTERVAL, schedule_and_update_news_list)


news_list = generate_news_list()

main = urwid.Padding(urwid.ListBox(news_list), left=2, right=2)
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

loop = urwid.MainLoop(top, palette=[('reversed', 'standout', '')], unhandled_input=handle_input)
loop.set_alarm_in(UPDATE_INTERVAL, schedule_and_update_news_list)
loop.run()

