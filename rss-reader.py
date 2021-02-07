#!/usr/bin/env python

from datetime import datetime
import os
import sqlite3
import urwid
import xml.etree.ElementTree as xml

UPDATE_INTERVAL = 60


class Config():
    CONFIG_PATH = '/home/mylk/.config/liferea/feedlist.opml'

    def get_sources(self):
        tree = xml.parse(self.CONFIG_PATH)
        root = tree.getroot()

        sources = {}
        for outline in root.findall('./body/'):
            sources[outline.attrib['id']] = {
                'title': outline.attrib['title'],
                'sources': {}
            }

            for source in outline.findall('./'):
                if source.attrib['type'] in ['rss', 'atom']:
                    sources[outline.attrib['id']]['sources'][source.attrib['id']] = {
                        'title': source.attrib['title']
                    }
        return sources


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
            i.source AS url,
            i.read
            FROM items AS i
            INNER JOIN node AS n ON n.node_id = i.node_id
            AND i.read = 0
            AND i.parent_item_id = 0
            ORDER BY date ASC
        ''')

    def get_node_unreads_count(self, node_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        return cursor.execute('''
            SELECT COUNT(*)
            FROM items AS i
            INNER JOIN node AS n
            ON i.node_id = n.node_id
            AND i.read = 0
            AND (
                n.node_id = ?
                OR n.parent_id = ?
            )
        ''', (node_id,))

    def get_node_items(self, node_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        return cursor.execute('''
            SELECT datetime(date, 'unixepoch') AS date,
            n.title AS source,
            i.item_id,
            IFNULL(i.title, '') AS title,
            i.source AS url,
            i.read
            FROM items AS i
            INNER JOIN node AS n ON i.node_id = n.node_id
            AND (
                n.node_id = ?
                OR n.parent_id = ?
            )
            ORDER BY date DESC
        ''', (node_id, node_id))

    def close_connection(self):
        self.get_connection().close()

    def set_item_read(self, item_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute('UPDATE items SET read = 1 WHERE item_id = ?', (item_id,))
        connection.commit()
        self.close_connection()

    def set_item_unread(self, item_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute('UPDATE items SET read = 0 WHERE item_id = ?', (item_id,))
        connection.commit()
        self.close_connection()


class ReadButton(urwid.Button):
    button_left = urwid.Text('')
    button_right = urwid.Text('')


class UnreadButton(urwid.Button):
    button_left = urwid.Text('.')
    button_right = urwid.Text('')


def generate_interface(loop, rows):
    config = Config()
    sources = config.get_sources()
    sources_list = urwid.SimpleListWalker([])
    for source in sources:
        button = ReadButton(sources[source]['title'])
        urwid.connect_signal(button, 'click', source_chosen, source)
        sources_list.append(urwid.AttrMap(button, None, focus_map='reversed'))

    global news_items
    global news_list
    global index_with_focus
    index_with_focus = news_list.get_focus()[1] if news_list.get_focus()[1] else 0
    news_items = rows

    last_update_txt = urwid.Text(datetime.now().strftime('%c'))

    news_list = urwid.SimpleListWalker([])
    for row in rows:
        if row[5] == 0:
            button = UnreadButton('{:<26} {:<103} {}'.format(row[1], row[3], row[0]))
        else:
            button = ReadButton('{:<26} {:<103} {}'.format(row[1], row[3], row[0]))

        urwid.connect_signal(button, 'click', item_chosen, row)
        news_list.append(urwid.AttrMap(button, None, focus_map='reversed'))

    # @TODO: handle case the item is the first and only
    if len(news_items) > index_with_focus:
        news_list.set_focus(index_with_focus)
    else:
        news_list.set_focus((index_with_focus - 1))

    elements_list = urwid.ListBox(news_list)
    
    sources_list = urwid.ListBox(sources_list)
    columns = urwid.Columns([(20, sources_list), (1, urwid.SolidFill(' ')), (200, elements_list)])
    columns.set_focus(elements_list)
    
    pile = urwid.Pile([last_update_txt, urwid.Divider(), (221, columns)])
    widget = urwid.Filler(pile, valign='top')

    loop.widget = widget


def source_chosen(button, the_node_id):
    global node_id
    node_id = the_node_id

    db = Database()
    rows = db.get_node_items(the_node_id).fetchall()
    db.close_connection()

    generate_interface(loop, rows)

def item_chosen(button, row):
    global index_with_focus
    global node_id
    
    node_id = None

    Database().set_item_read(row[2])

    index_with_focus = news_list.get_focus()[1]

    db = Database()
    rows = db.find_unread_news().fetchall()
    db.close_connection()

    generate_interface(loop, rows)

    # @TODO: blocks execution if firefox is closed
    os.system('/usr/bin/firefox --new-tab {}'.format(row[4]))


def exit_program(button):
    raise urwid.ExitMainLoop()


def handle_input(key):
    global news_items
    global index_with_focus
    global node_id
    
    if key in ['q', 'Q']:
        raise urwid.ExitMainLoop()
    elif key == 'h':
        # @TODO: show help with available keys
        pass
    elif key == 'r':
        index_with_focus = news_list.get_focus()[1]

        focused_item = news_items[int(index_with_focus)]
        Database().set_item_read(focused_item[2])

        if node_id:
            db = Database()
            rows = db.get_node_items(node_id).fetchall()
            db.close_connection()
        else:
            db = Database()
            rows = db.find_unread_news().fetchall()
            db.close_connection()

        generate_interface(loop, rows)
    elif key == 'u':
        index_with_focus = news_list.get_focus()[1]

        focused_item = news_items[int(index_with_focus)]
        Database().set_item_unread(focused_item[2])

        if node_id:
            db = Database()
            rows = db.get_node_items(node_id).fetchall()
            db.close_connection()
        else:
            db = Database()
            rows = db.find_unread_news().fetchall()
            db.close_connection()

        generate_interface(loop, rows)
    elif key == 'f':
        index_with_focus = news_list.get_focus()[1]

        db = Database()
        rows = db.find_unread_news().fetchall()
        db.close_connection()

        generate_interface(loop, rows)


def schedule_and_generate_interface(loop = None, data = None):
    db = Database()
    rows = db.find_unread_news().fetchall()
    db.close_connection()

    generate_interface(loop, rows)

    loop.set_alarm_in(UPDATE_INTERVAL, schedule_and_generate_interface)


node_id = None
news_items = []
news_list = urwid.SimpleListWalker([])

pile = urwid.Pile([])
widget = urwid.Filler(pile, valign='top')
loop = urwid.MainLoop(widget, palette=[('reversed', 'standout', '')], unhandled_input=handle_input)
loop.set_alarm_in(UPDATE_INTERVAL, schedule_and_generate_interface)

db = Database()
rows = db.find_unread_news().fetchall()
db.close_connection()

generate_interface(loop, rows)

loop.run()

