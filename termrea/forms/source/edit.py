import urwid

from adapters.config import ConfigAdapter
from adapters.database import DatabaseAdapter
from forms import main
from services import source as sourceservice
import state


def display(node_id):
    if node_id == state.node_id_unreads:
        return

    config_adapter = ConfigAdapter()
    db = DatabaseAdapter()

    node = next(db.get_node_subscriptions(node_id))
    config_node = config_adapter.get_source(node_id)
    mark_as_read = False if config_node['mark_as_read'] == 'false' else True

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
    submit_button = urwid.Button('Submit')
    urwid.connect_signal(submit_button, 'click', save, user_args=[node_id, name_edit, url_edit, update_interval_edit, mark_as_read_checkbox])
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


def save(node_id, name_edit, url_edit, update_interval_edit, mark_as_read_checkbox, button):
    url = url_edit.get_edit_text()
    feed_type = sourceservice.detect_feed_type(url)
    link = sourceservice.get_link(url, feed_type)

    config_adapter = ConfigAdapter()
    db = DatabaseAdapter()

    db.update_node(node_id, name_edit.get_edit_text(), feed_type, url, update_interval_edit.get_edit_text())
    db.close_connection()

    config_adapter.update_source(node_id, name_edit.get_edit_text(), feed_type, url, link, update_interval_edit.get_edit_text(), mark_as_read_checkbox.get_state())
    state.sources = config_adapter.get_sources()

    main.set_focused_item()
    rows = db.get_source_items(state.selected_node_id, state.node_id_unreads, state.selected_filter)
    main.display(state.loop, rows)


def close(button):
    state.loop.widget = state.body

