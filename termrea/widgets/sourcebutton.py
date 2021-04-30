import urwid


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

