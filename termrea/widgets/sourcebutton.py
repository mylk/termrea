import urwid


class SourceButton(urwid.Button):
    button_left = urwid.Text('')
    button_right = urwid.Text('')

    def __init__(self, label, on_press=None, user_data=None):
        self._label = urwid.wimp.SelectableIcon('  ' + label)
        super(urwid.Button, self).__init__(self._label)

    def keypress(self, size, key):
        if key in ('up', 'down', 'left', 'right', 'page up', 'page down', 'q', 'Q'):
            return super(urwid.Button, self).keypress(size, key)

        if key in ('enter'):
            urwid.emit_signal(self, 'click')

        if key in ('r', 'R'):
            urwid.emit_signal(self, 'read')

