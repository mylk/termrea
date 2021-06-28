from datetime import datetime
import os
import urwid

from adapters.database import DatabaseAdapter
from forms.source import add
from forms.source import delete
from forms.source import edit
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
        urwid.connect_signal(button, 'add', add.display, source)
        urwid.connect_signal(button, 'delete', delete.display, source)
        urwid.connect_signal(button, 'edit', edit.display, source)
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
            urwid.connect_signal(button, 'add', add.display, subsource)
            urwid.connect_signal(button, 'delete', delete.display, subsource)
            urwid.connect_signal(button, 'edit', edit.display, subsource)
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

