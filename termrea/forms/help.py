import urwid

import state


def display():
    # body
    body_text = urwid.Text('''
    The available controls:

    arrows  navigate
    r       mark as read
    u       mark as unread
    enter   open on browser,
            select source
    space   show unread of source
    f       fetch
    a       add source
    e       edit source
    d       delete source
    q       quit
    ''', align='left')
    body_filler = urwid.Filler(body_text, valign='top')
    body_padding = urwid.Padding(
        body_filler,
        left=1,
        right=1
    )
    state.body = urwid.LineBox(body_padding)

    # footer
    footer = urwid.Button('OK', close)
    footer = urwid.AttrWrap(footer, 'selectable', 'focus')
    footer = urwid.GridFlow([footer], 6, 1, 1, 'center')

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
        height=18
    )

    state.loop.widget = over


def close(button):
    state.loop.widget = state.body

