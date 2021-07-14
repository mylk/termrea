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
    node = next(db.get_source(node_id))
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
        folder_nodes = db.get_sources_by_parent(node['node_id'])
        for folder_node in folder_nodes:
            node_ids.append(folder_node['node_id'])
    node_ids.append(node['node_id'])

    for node_id in node_ids:
        db.delete_source(node_id)
        config_adapter.delete_source(node_id)

    db.close_connection()

    state.sources = config_adapter.get_sources()
    main.set_focused_item()
    rows = db.get_source_items(state.selected_node_id, state.node_id_unreads, state.selected_filter)
    main.display(state.loop, rows)


def close(button):
    state.loop.widget = state.body

