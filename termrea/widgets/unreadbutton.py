import urwid


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

