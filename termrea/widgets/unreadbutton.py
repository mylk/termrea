import urwid
import webbrowser

from adapters.database import DatabaseAdapter
from forms import main
import state


class UnreadButton(urwid.Button):

    button_left = urwid.Text('· ')
    button_right = urwid.Text('')

    def __init__(self, label, on_press=None, user_data=None):
        self._label = urwid.wimp.SelectableIcon(label)
        super(urwid.Button, self).__init__(self._label)

        cols = urwid.Columns([
            ('fixed', 2, self.button_left),
            self._label,
            ('fixed', 0, self.button_right)
        ], dividechars=0)
        urwid.WidgetWrap.__init__(self, cols)

    def keypress(self, size, key):
        if key in ('up', 'down', 'left', 'right', 'page up', 'page down', 'home', 'end', 'q', 'h', 'f'):
            return super(urwid.Button, self).keypress(size, key)

        if key == 'enter':
            urwid.emit_signal(self, 'click')

        if key == 'r':
            urwid.emit_signal(self, 'read')

    def mark_as_read(item_id):
        db = DatabaseAdapter()

        main.set_focused_item()

        db.set_item_read(item_id)

        rows = db.get_source_items(state.selected_node_id, state.node_id_unreads, state.selected_filter)

        main.display(state.loop, rows)

    def select(row):
        db = DatabaseAdapter()

        main.set_focused_item()

        db.set_item_read(row['item_id'])

        rows = db.get_source_items(state.selected_node_id, state.node_id_unreads, state.selected_filter)

        main.display(state.loop, rows)

        webbrowser.open_new_tab(row['url'])

