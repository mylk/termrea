from datetime import datetime
import os
import random
import string
import urllib.request
import urwid
import xml.etree.ElementTree as xml

from adapters.config import ConfigAdapter
from adapters.database import DatabaseAdapter
import config
import state
from widgets.readbutton import ReadButton
from widgets.sourcebutton import SourceButton
from widgets.unreadbutton import UnreadButton


urwid.register_signal(UnreadButton, ['click', 'read'])
urwid.register_signal(ReadButton, ['click', 'unread'])
urwid.register_signal(SourceButton, ['click', 'click_unread', 'read', 'edit', 'delete', 'add'])


def display(loop, news_items):
    terminal_size = os.get_terminal_size()

    unread_count = get_node_unread_count(state.selected_node_id)
    unread_count_txt = urwid.Text('Unread: {}'.format(unread_count))
    last_update_txt = urwid.Text('Updated: {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')), align='right')
    columns_info = urwid.Columns([(round(terminal_size.columns / 2), unread_count_txt), last_update_txt])

    sources_list = generate_sources_list()
    news_list = generate_news_list(news_items)

    elements_list = urwid.ListBox(news_list)
    sources_list = urwid.ListBox(sources_list)

    if state.list_with_focus == 'news_list':
        selected_list = elements_list
    else:
        selected_list = sources_list

    if len(selected_list.body) == 0:
        pass
    elif len(selected_list.body) > state.index_with_focus:
        selected_list.set_focus(state.index_with_focus)
    elif len(selected_list.body) == state.index_with_focus:
        selected_list.set_focus((state.index_with_focus - 1))

    columns_news = urwid.Columns([(28, sources_list), (1, urwid.SolidFill(' ')), ((terminal_size.columns - 29), elements_list)])
    columns_news.set_focus(selected_list)

    pile = urwid.Pile([columns_info, urwid.Divider(), (terminal_size.lines - 2, columns_news)])
    widget = urwid.Filler(pile, valign='top')

    state.loop.widget = widget


def generate_sources_list():
    db = DatabaseAdapter()
    unread_items = db.find_unread_news().fetchall()
    db.close_connection()

    sources_list = urwid.SimpleListWalker([])
    for source in state.sources:
        button = SourceButton(state.sources[source]['title'])
        urwid.connect_signal(button, 'click', SourceButton.show_all, source)
        urwid.connect_signal(button, 'click_unread', SourceButton.show_unread, source)
        urwid.connect_signal(button, 'read', SourceButton.mark_as_read, source)
        urwid.connect_signal(button, 'edit', edit_source, source)
        urwid.connect_signal(button, 'delete', delete_source, source)
        urwid.connect_signal(button, 'add', add_source, source)
        sources_list.append(urwid.AttrMap(button, None, focus_map='reversed'))

        for subsource in state.sources[source]['sources']:
            title_prefix = '  '
            for unread_item in unread_items:
                if unread_item['source_id'] == subsource and unread_item['read'] == 0:
                    title_prefix = '· '
                    break

            button = SourceButton(title_prefix + state.sources[source]['sources'][subsource]['title'])
            urwid.connect_signal(button, 'click', SourceButton.show_all, subsource)
            urwid.connect_signal(button, 'click_unread', SourceButton.show_unread, subsource)
            urwid.connect_signal(button, 'read', SourceButton.mark_as_read, subsource)
            urwid.connect_signal(button, 'edit', edit_source, subsource)
            urwid.connect_signal(button, 'delete', delete_source, subsource)
            urwid.connect_signal(button, 'add', add_source, subsource)
            sources_list.append(urwid.AttrMap(button, None, focus_map='reversed'))

    return sources_list


def generate_news_list(rows):
    terminal_size = os.get_terminal_size()

    news_list = urwid.SimpleListWalker([])

    section_width = terminal_size.columns - 82
    button_width = terminal_size.columns - 78

    for row in rows:
        title = row['title'][0:section_width] + '...' if len(row['title']) >= section_width else row['title']
        button_text = '{:<26} {:<{width}} {}'.format(row['source'], title, row['date'], width=(button_width))

        if not row['read']:
            button = UnreadButton(button_text)
            urwid.connect_signal(button, 'read', UnreadButton.mark_as_read, row['item_id'])
        else:
            button = ReadButton(button_text)
            urwid.connect_signal(button, 'unread', ReadButton.mark_as_unread, row['item_id'])

        urwid.connect_signal(button, 'click', UnreadButton.select, row)
        news_list.append(urwid.AttrMap(button, None, focus_map='reversed'))

    return news_list


def get_node_unread_count(node_id):
    db = DatabaseAdapter()

    if node_id and node_id == state.node_id_unreads:
        rows = db.get_unread_count().fetchall()
    else:
        rows = db.get_node_unread_count(node_id).fetchall()

    db.close_connection()

    return rows[0]['unread_count']


def set_focused_item():
    # if help overlay is being displayed, do nothing, the widget is the overlay now
    if type(state.loop.widget) == urwid.Overlay:
        return

    # get from the main loop the news items list, sources list, focused item
    columns = state.loop.widget.get_body()[2]
    news_list = columns.widget_list[2].body
    sources_list = columns.widget_list[0].body
    item_with_focus = columns.get_focus_widgets()[1].base_widget if len(columns.get_focus_widgets()) > 1 else None

    # retain the focused item after updating the list
    state.list_with_focus = 'news_list'
    selected_list = news_list
    if type(item_with_focus) == SourceButton:
        state.list_with_focus = 'sources_list'
        selected_list = sources_list

    state.index_with_focus = selected_list.get_focus()[1] if selected_list.get_focus()[1] else 0


def edit_source(node_id):
    if node_id == state.node_id_unreads:
        return

    config_adapter = ConfigAdapter()
    db = DatabaseAdapter()

    node = next(db.get_node_subscriptions(node_id))
    config_node = config_adapter.get_source(node_id)
    mark_as_read = False if config_node['mark_as_read'] == 'false' else True

    def save_source(button, node_id):
        config_adapter = ConfigAdapter()
        db = DatabaseAdapter()

        db.update_node(node_id, name_edit.get_edit_text(), url_edit.get_edit_text(), update_interval_edit.get_edit_text())
        db.close_connection()

        config_adapter.update_source(node_id, name_edit.get_edit_text(), url_edit.get_edit_text(), update_interval_edit.get_edit_text(), mark_as_read_checkbox.get_state())
        state.sources = config_adapter.get_sources()

        set_focused_item()
        rows = get_source_items(state.selected_node_id)
        display(state.loop, rows)

    name_txt = urwid.Text(u'Name', align='right')
    name_edit = urwid.Edit(u'', edit_text=node['title'], wrap='clip')
    name_column = urwid.Columns([(18, name_txt), (2, urwid.Divider()), name_edit])

    url_txt = urwid.Text(u'URL', align='right')
    url_edit = urwid.Edit(u'', edit_text=node['source'], wrap='clip')
    url_column = urwid.Columns([(18, url_txt), (2, urwid.Divider()), url_edit])

    update_interval_txt = urwid.Text(u'Update interval', align='right')
    update_interval_edit = urwid.Edit(u'', edit_text=str(node['update_interval']))
    update_interval_column = urwid.Columns([(18, update_interval_txt), (2, urwid.Divider()), update_interval_edit])

    mark_as_read_txt = urwid.Text(u'Mark as read', align='right')
    mark_as_read_checkbox = urwid.CheckBox(u'', mark_as_read)
    mark_as_read_column = urwid.Columns([(18, mark_as_read_txt), (2, urwid.Divider()), mark_as_read_checkbox])

    body_pile = urwid.Pile([
        urwid.Divider(),
        name_column,
        url_column,
        update_interval_column,
        mark_as_read_column,
        urwid.Divider()
    ])

    # body
    body_filler = urwid.Filler(body_pile, valign='top')
    body_padding = urwid.Padding(
        body_filler,
        left=1,
        right=1
    )
    state.body = urwid.LineBox(body_padding)

    # footer
    def close(button):
        state.loop.widget = state.body

    submit_button = urwid.Button('Submit')
    urwid.connect_signal(submit_button, 'click', save_source, node_id)
    cancel_button = urwid.Button('Cancel')
    urwid.connect_signal(cancel_button, 'click', close)
    footer = urwid.GridFlow([submit_button, cancel_button], 10, 1, 1, 'center')

    # layout
    layout = urwid.Frame(
        state.body,
        footer=footer,
        focus_part='footer'
    )

    state.body = state.loop.widget
    pile = urwid.Pile([layout])
    over = urwid.Overlay(
        pile,
        state.body,
        align='center',
        valign='middle',
        width=60,
        height=12
    )

    state.loop.widget = over

    db.close_connection()


def delete_source(node_id):
    if node_id == state.node_id_unreads:
        return

    db = DatabaseAdapter()
    node = next(db.get_node(node_id))
    db.close_connection()

    # body
    body_pile = urwid.Pile([
        urwid.Divider(),
        urwid.Text('Are you sure you want to delete source "{}"?'.format(node['title']), align='center')
    ])
    body_filler = urwid.Filler(body_pile, valign='top')
    body_padding = urwid.Padding(
        body_filler,
        left=1,
        right=1
    )
    state.body = urwid.LineBox(body_padding)

    # footer
    def delete(button, node):
        config_adapter = ConfigAdapter()
        db = DatabaseAdapter()

        node_ids = []
        if node['type'] == 'folder':
            folder_nodes = db.get_nodes_by_parent(node['node_id'])
            for folder_node in folder_nodes:
                node_ids.append(folder_node['node_id'])
        node_ids.append(node['node_id'])

        for node_id in node_ids:
            db.delete_node(node_id)
            config_adapter.delete_source(node_id)

        db.close_connection()

        state.sources = config_adapter.get_sources()
        set_focused_item()
        rows = get_source_items(state.selected_node_id)
        display(state.loop, rows)

    def close(button):
        state.loop.widget = state.body

    button_yes = urwid.Button('Yes')
    urwid.connect_signal(button_yes, 'click', delete, node)
    button_no = urwid.Button('No', close)
    footer = urwid.GridFlow([button_yes, button_no], 7, 1, 1, 'center')

    # layout
    layout = urwid.Frame(
        state.body,
        footer=footer,
        focus_part='footer'
    )

    state.body = state.loop.widget
    pile = urwid.Pile([layout])
    over = urwid.Overlay(
        pile,
        state.body,
        align='center',
        valign='middle',
        width=41,
        height=7
    )

    state.loop.widget = over


def add_source(sibling_node_id):
    if sibling_node_id == state.node_id_unreads:
        return

    config_adapter = ConfigAdapter()
    db = DatabaseAdapter()

    sibling_node = next(db.get_node(sibling_node_id))
    config_node = config_adapter.get_source(sibling_node_id)
    mark_as_read = False if config_node['mark_as_read'] == 'false' else True
    new_node_id = generate_node_id()
    parent_node_id = sibling_node['parent_id']
    db.close_connection()

    def save_source(button):
        url = url_edit.get_edit_text()
        feed_type = detect_feed_type(url)
        link = get_link(url, feed_type)

        config_adapter = ConfigAdapter()
        db = DatabaseAdapter()

        new_node = db.add_source(new_node_id, parent_node_id, name_edit.get_edit_text(), feed_type, url, update_interval_edit.get_edit_text())
        db.close_connection()

        config_adapter.add_source(sibling_node_id, new_node_id, name_edit.get_edit_text(), feed_type, url, link, update_interval_edit.get_edit_text(), mark_as_read_checkbox.get_state())
        state.sources = config_adapter.get_sources()

        set_focused_item()
        rows = get_source_items(state.selected_node_id)
        display(state.loop, rows)

    name_txt = urwid.Text(u'Name', align='right')
    name_edit = urwid.Edit(u'', wrap='clip')
    name_column = urwid.Columns([(18, name_txt), (2, urwid.Divider()), name_edit])

    url_txt = urwid.Text(u'URL', align='right')
    url_edit = urwid.Edit(u'', wrap='clip')
    url_column = urwid.Columns([(18, url_txt), (2, urwid.Divider()), url_edit])

    update_interval_txt = urwid.Text(u'Update interval', align='right')
    update_interval_edit = urwid.Edit(u'')
    update_interval_column = urwid.Columns([(18, update_interval_txt), (2, urwid.Divider()), update_interval_edit])

    mark_as_read_txt = urwid.Text(u'Mark as read', align='right')
    mark_as_read_checkbox = urwid.CheckBox(u'')
    mark_as_read_column = urwid.Columns([(18, mark_as_read_txt), (2, urwid.Divider()), mark_as_read_checkbox])

    body_pile = urwid.Pile([
        urwid.Divider(),
        name_column,
        url_column,
        update_interval_column,
        mark_as_read_column,
        urwid.Divider()
    ])

    # body
    body_filler = urwid.Filler(body_pile, valign='top')
    body_padding = urwid.Padding(
        body_filler,
        left=1,
        right=1
    )
    state.body = urwid.LineBox(body_padding)

    # footer
    def close(button):
        state.loop.widget = state.body

    submit_button = urwid.Button('Submit')
    urwid.connect_signal(submit_button, 'click', save_source)
    cancel_button = urwid.Button('Cancel')
    urwid.connect_signal(cancel_button, 'click', close)
    footer = urwid.GridFlow([submit_button, cancel_button], 10, 1, 1, 'center')

    # layout
    layout = urwid.Frame(
        state.body,
        footer=footer,
        focus_part='footer'
    )

    state.body = state.loop.widget
    pile = urwid.Pile([layout])
    over = urwid.Overlay(
        pile,
        state.body,
        align='center',
        valign='middle',
        width=60,
        height=12
    )

    state.loop.widget = over


def generate_node_id():
    db = DatabaseAdapter()

    node = ''
    while node is not None:
        new_node_id = ''.join(random.choices(string.ascii_lowercase, k=7))
        node = db.get_node(new_node_id).fetchone()

    db.close_connection()

    return new_node_id


def detect_feed_type(url):
    data = urllib.request.urlopen(url).read()
    root = xml.fromstring(data)

    source_type = 'atom'
    if root.tag == 'rss':
        source_type = 'rss'

    return source_type


def get_link(url, feed_type):
    data = urllib.request.urlopen(url).read()
    root = xml.fromstring(data)

    if feed_type == 'rss':
        link = root.find('./channel/link')

        return link.text
    elif feed_type == 'atom':
        links = root.findall('{http://www.w3.org/2005/Atom}link')
        for link in links:
            if not 'rel' in link.attrib or link.attrib['rel'] != 'self':
                return link.attrib['href']

    return None


def get_source_items(node_id):
    db = DatabaseAdapter()

    if node_id and node_id != state.node_id_unreads:
        if state.selected_filter == 'unread':
            rows = db.get_node_unread_items(node_id).fetchall()
        else:
            rows = db.get_node_all_items(node_id).fetchall()
    else:
        rows = db.find_unread_news().fetchall()

    db.close_connection()

    return rows

