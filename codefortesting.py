from pynput.keyboard import Key, Listener, Controller
import core
import sys


core.init()
core.syntax.add_template('py.json')
try:
    core.File.open(sys.argv[1])
except IndexError:
    print('Error: please, enter a filename to edit')


class data:
    cls = 'clear'
    keyboard = Controller()
    file = sys.argv
    currently_finding = False
    edit_line_temp = ''
    edit_line_cursor = -1
    arrows = {
        Key.right: [-1, 0],
        Key.left: [1, 0],
        Key.up: [0, -1],
        Key.down: [0, 1],
    }


def on_press(key):
    check_key(key)


def on_release(key):
    if key == Key.esc:
        # Stop listener
        deinit()
        return False


def edit_line(key):
    if key == Key.backspace:
        data.edit_line_temp = data.edit_line_temp[:data.edit_line_cursor - 1] + data.edit_line_temp[data.edit_line_cursor:]
        data.edit_line_cursor -= 1
    elif key == Key.delete:
        data.edit_line_temp = data.edit_line_temp[:data.edit_line_cursor] + data.edit_line_temp[data.edit_line_cursor + 1:]
    elif key == Key.left and data.edit_line_cursor > 0:
        data.edit_line_cursor -= 1
    elif key == Key.right and data.edit_line_cursor < len(data.edit_line_temp) - 1:
        data.edit_line_cursor += 1
    elif key == Key.enter:
        data.currently_finding = False
    elif key == Key.space:
        if data.edit_line_cursor == len(data.edit_line_temp):
            data.edit_line_temp = data.edit_line_temp[:data.edit_line_cursor + 1] + ' '
        else:
            data.edit_line_temp = data.edit_line_temp[:data.edit_line_cursor + 1] + ' ' + data.edit_line_temp[data.edit_line_cursor + 1:]
        data.edit_line_cursor += 1
    else:
        if len(repr(key)[1:-1]) == 1:
            data.edit_line_cursor += 1
            if data.edit_line_cursor == len(data.edit_line_temp):
                data.edit_line_temp = data.edit_line_temp[:data.edit_line_cursor] + str(key)[1:-1]# + data.edit_line_temp[:data.edit_line_cursor]
            else:
                data.edit_line_temp = data.edit_line_temp[:data.edit_line_cursor - 1] + str(key)[1:-1] + data.edit_line_temp[:data.edit_line_cursor + 1]


def deinit():
    data.keyboard.press(Key.enter)
    data.keyboard.release(Key.enter)
    data.keyboard.type('clear')
    data.keyboard.press(Key.enter)
    data.keyboard.release(Key.enter)


def check_key(key):
    bottom_text = 'f1 - Find    f2 - Find and replace    f3 - rename current file    f4 - create custom command\nf5 - save file'.title()
    if key == Key.tab:
        core.editor.put_tab()
    elif key == Key.f1:
        data.currently_finding = not data.currently_finding
        data.edit_line_temp = ''
        data.edit_line_cursor = -1
    elif key == Key.f2:
        pass
    elif key == Key.f3:
        pass
    elif key == Key.f4:
        pass
    elif key == Key.f5:
        pass
    elif key in data.arrows:
        core.editor.move_cursor(data.arrows[key])
    if data.currently_finding:
        edit_line(key)
        if len(data.edit_line_temp) > 0:
            try:
                bottom_text += '\nFind> ' + data.edit_line_temp[:data.edit_line_cursor] + core.colored(
                    data.edit_line_temp[data.edit_line_cursor], 'grey', 'on_magenta') + core.colored(data.edit_line_temp[
                                                                                        data.edit_line_cursor + 1:] if data.edit_line_cursor <= len(data.edit_line_temp) - 2 else '', core.data.editor_highlight['bottom_text_color'][0], core.data.editor_highlight['bottom_text_color'][1])
            except IndexError:
                bottom_text += '\nFind> ' + data.edit_line_temp[:data.edit_line_cursor - 1] + core.colored(
                    data.edit_line_temp[data.edit_line_cursor - 1], 'grey', 'on_magenta')

        else:
            bottom_text += '\nFind> ' + core.colored('|', 'grey', 'on_magenta')

        if not data.currently_finding:
            core.editor.find(data.edit_line_temp)
    core.syntax.check()

    core.text.display(bottom_text=bottom_text)


core.init()
# Collect events until released
with Listener(
        on_press=on_press,
        on_release=on_release) as listener:
    listener.join()

