#!/usr/bin/env python

from datetime import datetime
import os
import sqlite3
import urwid

UPDATE_INTERVAL = 60


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


class UnreadButton(urwid.Button):
    button_left = urwid.Text('.')
    button_right = urwid.Text('')


def generate_interface(loop):
    db = Database()
    rows = db.find_unread_news().fetchall()
    db.close_connection()

    global news_items
    global news_list
    global index_with_focus
    index_with_focus = news_list.get_focus()[1] if news_list.get_focus()[1] else 0
    news_items = rows

    last_update_txt = urwid.Text(datetime.now().strftime('%c'))

    news_list = urwid.SimpleListWalker([])
    for row in rows:
        button = UnreadButton('{:<26} {:<103} {}'.format(row[1], row[3], row[0]))
        urwid.connect_signal(button, 'click', item_chosen, row)
        news_list.append(urwid.AttrMap(button, None, focus_map='reversed'))

    # @TODO: handle case the item is the first and only
    if len(news_items) > index_with_focus:
        news_list.set_focus(index_with_focus)
    else:
        news_list.set_focus((index_with_focus - 1))

    elements_list = urwid.ListBox(news_list)
    pile = urwid.Pile([last_update_txt, urwid.Divider(), (100, elements_list)])
    widget = urwid.Filler(pile, valign='top')

    loop.widget = widget


def item_chosen(button, row):
    global index_with_focus

    Database().set_item_read(row[2])

    index_with_focus = news_list.get_focus()[1]
    generate_interface(loop)

    # @TODO: blocks execution if firefox is closed
    os.system('/usr/bin/firefox --new-tab {}'.format(row[4]))


def exit_program(button):
    raise urwid.ExitMainLoop()


def handle_input(key):
    global news_items
    global index_with_focus

    if key in ['q', 'Q']:
        raise urwid.ExitMainLoop()
    elif key == 'h':
        # @TODO: show help with available keys
        pass
    elif key == 'm':
        index_with_focus = news_list.get_focus()[1]

        focused_item = news_items[int(index_with_focus)]
        Database().set_item_read(focused_item[2])
        generate_interface(loop)
    elif key == 'u':
        index_with_focus = news_list.get_focus()[1]
        generate_interface(loop)


def schedule_and_generate_interface(loop = None, data = None):
    generate_interface(loop)

    loop.set_alarm_in(UPDATE_INTERVAL, schedule_and_generate_interface)


news_items = []
news_list = urwid.SimpleListWalker([])

pile = urwid.Pile([])
widget = urwid.Filler(pile, valign='top')
loop = urwid.MainLoop(widget, palette=[('reversed', 'standout', '')], unhandled_input=handle_input)
loop.set_alarm_in(UPDATE_INTERVAL, schedule_and_generate_interface)

generate_interface(loop)

loop.run()

