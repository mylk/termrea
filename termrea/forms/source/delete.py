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


def display(node_id):
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
    button_yes = urwid.Button('Yes')
    urwid.connect_signal(button_yes, 'click', delete, user_args=[node])
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


def delete(node, button):
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
    rows = db.get_source_items(state.selected_node_id)
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

