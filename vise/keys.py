#!/usr/bin/env python
# vim:fileencoding=utf-8
# License: GPL v3 Copyright: 2015, Kovid Goyal <kovid at kovidgoyal.net>

from PyQt5.Qt import (
    Qt, QObject, QEvent, QApplication, QMainWindow, QKeySequence, QOpenGLWidget
)

from . import actions

modifiers_mask = Qt.ShiftModifier | Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier


def key_from_event(ev):
    modifiers = ev.modifiers() & modifiers_mask
    return ev.key() | int(modifiers)


def key_to_string(key):
    return QKeySequence(key).toString().encode('utf-8', 'ignore').decode('utf-8')

normal_key_map, input_key_map = {}, {}


def read_key_map(which, raw):
    for line in raw.splitlines():
        line = line.strip()
        if line:
            key, action = (x.strip() for x in line.partition(' ')[::2])
            key = QKeySequence.fromString(key)[0]
            action = getattr(actions, action)
            which[key] = action


read_key_map(normal_key_map, '''\
Alt+Right                   forward
Alt+Left                    back
D                           close_tab
/                           search_forward
?                           search_back
N                           next_match
Shift+N                     prev_match
Ctrl+Z                      passthrough
G                           quickmark
Shift+G                     quickmark_newtab
''')


read_key_map(input_key_map, '''\
Escape                     exit_text_input
Ctrl+I                     edit_text
''')


class KeyFilter(QObject):

    def eventFilter(self, watched, event):
        etype = event.type()
        if etype == QEvent.KeyPress:
            app = QApplication.instance()
            window, fw = app.activeWindow(), app.focusWidget()
            if isinstance(window, QMainWindow) and (fw is None or isinstance(fw, QOpenGLWidget)):
                key = key_from_event(event)
                if window.quickmark_pending:
                    window.quickmark(key)
                    return True
                if window.current_tab is not None:
                    if window.current_tab.force_passthrough:
                        return False
                    if window.current_tab.text_input_focused:
                        action = input_key_map.get(key)
                        if action is not None:
                            swallow = action(window)
                            if swallow is True:
                                return True
                        return False
                action = normal_key_map.get(key)
                if action is not None:
                    swallow = action(window)
                    if swallow is True:
                        return True
                return True
        return False