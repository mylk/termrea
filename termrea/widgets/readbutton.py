import urwid


class ReadButton(urwid.Button):
    button_left = urwid.Text('')
    button_right = urwid.Text('')

    def __init__(self, label, on_press=None, user_data=None):
        self._label = urwid.wimp.SelectableIcon(label)
        super(urwid.Button, self).__init__(self._label)

        cols = urwid.Columns([
            ('fixed', 1, self.button_left),
            self._label,
            ('fixed', 0, self.button_right)
        ], dividechars=1)
        urwid.WidgetWrap.__init__(self, cols)

    def keypress(self, size, key):
        if key in ('up', 'down', 'left', 'right', 'page up', 'page down', 'home', 'end', 'q', 'f'):
            return super(urwid.Button, self).keypress(size, key)

        if key == 'enter':
            urwid.emit_signal(self, 'click')

        if key == 'u':
            urwid.emit_signal(self, 'unread')

