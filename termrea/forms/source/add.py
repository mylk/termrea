import random
import string
import urllib.request
import urwid
import xml.etree.ElementTree as xml

from adapters.config import ConfigAdapter
from adapters.database import DatabaseAdapter
from forms import main
import state
from widgets.sourcebutton import SourceButton


def display(sibling_node_id):
    if sibling_node_id == state.node_id_unreads:
        return

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
    submit_button = urwid.Button('Submit')
    urwid.connect_signal(submit_button, 'click', save, user_args=[sibling_node_id, name_edit, url_edit, update_interval_edit, mark_as_read_checkbox])
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


def save(sibling_node_id, name_edit, url_edit, update_interval_edit, mark_as_read_checkbox, button):
    url = url_edit.get_edit_text()
    feed_type = detect_feed_type(url)
    link = get_link(url, feed_type)

    config_adapter = ConfigAdapter()
    db = DatabaseAdapter()

    sibling_node = next(db.get_node(sibling_node_id))
    config_node = config_adapter.get_source(sibling_node_id)
    new_node_id = generate_node_id()
    parent_node_id = sibling_node['parent_id']

    new_node = db.add_source(new_node_id, parent_node_id, name_edit.get_edit_text(), feed_type, url, update_interval_edit.get_edit_text())
    db.close_connection()

    config_adapter.add_source(sibling_node_id, new_node_id, name_edit.get_edit_text(), feed_type, url, link, update_interval_edit.get_edit_text(), mark_as_read_checkbox.get_state())
    state.sources = config_adapter.get_sources()

    set_focused_item()
    rows = db.get_source_items(state.selected_node_id, state.node_id_unreads, state.selected_filter)
    main.display(state.loop, rows)


def close(button):
    state.loop.widget = state.body


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

