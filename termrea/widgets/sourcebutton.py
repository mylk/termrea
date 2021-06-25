import urwid

from adapters.database import DatabaseAdapter
from forms import main
import state


class SourceButton(urwid.Button):

    def __init__(self, label, on_press=None, user_data=None):
        self._label = urwid.wimp.SelectableIcon(label)
        super(urwid.Button, self).__init__(self._label)

    def keypress(self, size, key):
        if key in ('up', 'down', 'left', 'right', 'page up', 'page down', 'home', 'end', 'q', 'h', 'f'):
            return super(urwid.Button, self).keypress(size, key)

        if key == 'enter':
            urwid.emit_signal(self, 'click')

        if key == ' ':
            urwid.emit_signal(self, 'click_unread')

        if key == 'r':
            urwid.emit_signal(self, 'read')

        if key == 'e':
            urwid.emit_signal(self, 'edit')

        if key == 'd':
            urwid.emit_signal(self, 'delete')

        if key == 'a':
            urwid.emit_signal(self, 'add')

    @staticmethod
    def mark_as_read(node_id):
        main.set_focused_item()

        db = DatabaseAdapter()

        if node_id == state.node_id_unreads:
            db.set_unreads_read()
        else:
            db.set_source_read(node_id)

        db.close_connection()

        rows = main.get_source_items(state.selected_node_id)

        main.display(state.loop, rows)

    @staticmethod
    def show_all(node_id):
        state.selected_filter = None
        state.selected_node_id = node_id

        main.set_focused_item()

        rows = main.get_source_items(node_id)

        main.display(state.loop, rows)

    @staticmethod
    def show_unread(node_id):
        state.selected_filter = 'unread'
        state.selected_node_id = node_id

        main.set_focused_item()

        rows = main.get_source_items(node_id)

        main.display(state.loop, rows)

