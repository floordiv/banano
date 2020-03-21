import os
import sys
import json
from platform import system
from termcolor import colored
from pynput.keyboard import Controller, Key, Listener


cls = 'cls' if system().lower() == 'windows' else 'clear'   # cross-platform terminal clearing


class var:
    cursor_pos = [0, 0]   # abs pos and local (on the screen/page)
    filename = ''   # current editing file
    content = []    # list with strings, every element is a new line
    visible_content = []    # same var as content, but for highlighting and cursor drawing
    res = [100, 20]     # resolution: 100 symbols by x-coord, and 20 lines as a y-coord
    page_res = [0, 25]  # display file content from index1 to index2 (index2 - index1 lines are shown by time)
    header = 'baNano, version 0.0.1'  # editor name
    syntax_templates = {}   # should be loaded automatically
    tab_size = 4    # spaces in tab, using spaces, because of pep8
    
    edit_line_cursor = -1   # variables for one-lined input
    edit_line_temp = ''

    bad_letters = list('qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890')
    good_letters = list(' -=[{<.*/+:')

    arrows = {  # coords to move arrows
        Key.right:  [1,  0],
        Key.left:   [-1, 0],
        Key.up:     [0, -1],
        Key.down:   [0,  1],
    }


class editor:
    @staticmethod
    def edit_line(key):
        if key == Key.backspace:
            var.edit_line_temp = var.edit_line_temp[:var.edit_line_cursor - 1] + var.edit_line_temp[
                                                                                    var.edit_line_cursor:]
            var.edit_line_cursor -= 1
        elif key == Key.delete:
            var.edit_line_temp = var.edit_line_temp[:var.edit_line_cursor] + var.edit_line_temp[
                                                                                var.edit_line_cursor + 1:]
        elif key == Key.left and var.edit_line_cursor > 0:  # if left arrow pressed and current cursor pos is not 0
            var.edit_line_cursor -= 1
        elif key == Key.right and var.edit_line_cursor < len(var.edit_line_temp) - 1:  # if right_arrow and not line end
            var.edit_line_cursor += 1
        elif key == Key.enter:
            var.currently_finding = False
        elif key == Key.space:
            if var.edit_line_cursor == len(var.edit_line_temp):
                var.edit_line_temp = var.edit_line_temp[:var.edit_line_cursor + 1] + ' '
            else:
                var.edit_line_temp = var.edit_line_temp[:var.edit_line_cursor + 1] + ' ' + var.edit_line_temp[
                                                                                              var.edit_line_cursor + 1:]
            var.edit_line_cursor += 1
        else:
            if len(repr(key)[1:-1]) == 1:
                var.edit_line_cursor += 1
                if var.edit_line_cursor == len(var.edit_line_temp):
                    var.edit_line_temp = var.edit_line_temp[:var.edit_line_cursor] + str(key)[
                                                                                        1:-1] 
                else:
                    var.edit_line_temp = var.edit_line_temp[:var.edit_line_cursor - 1] + str(key)[
                                                                                            1:-1] + var.edit_line_temp[
                                                                                                    :var.edit_line_cursor + 1]
                    
    @staticmethod
    def find(find_text):
        var.pause_syntax_highlight = True
        positions = []
        for index, line in enumerate(var.content):
            if find_text in ''.join(line):
                position = [index, line.find(find_text), len(find_text)]
                if positions[0][0] == -1:
                    return False
                positions.append(position)
                recursion_answer = editor.find(find_text)
                if not recursion_answer:
                    continue
        for line, start, end in positions:
            var.content[line][start:end] = list(
                colored(''.join(var.content[line][start:end]), var.editor_highlight['find']))
        var.pause_syntax_highlight = False
                    
    @staticmethod
    def find_and_replace(text, replace_to):
        for index, line in enumerate(var.content):
            var.content[index] = list(''.join(line).replace(text, replace_to))
    
    @staticmethod
    def find_in_line(line, find_text):
        var.pause_syntax_highlight = True
        positions = []
        if find_text in line:
            position = [line.find(find_text), line.find(find_text) + len(find_text)]
            if positions != [] and positions[0][0] == -1:   # if there are no anymore words to find
                return False
            positions.append(position)
            recursion_answer = editor.find_in_line(line[:position[0]] + line[position[1]:], find_text)
            if not recursion_answer:
                return positions
        return []   # if template is even not in the line
    
    @staticmethod
    def check_syntax():
        start, end = var.page_res
        for index, line in enumerate(var.visible_content[start:end]):
            for template in var.syntax_templates:
                positions = editor.find_in_line(line, template)
                true_positions = []
                if len(positions) >= 1:
                    for position in positions:
                        if (line[position[0] - 1] in var.good_letters or position[0] == 0) and (position[1] == len(line) or line[position[1]] in var.good_letters):
                            true_positions.append(position)
                    for true_position in true_positions:
                        line = line[:true_position[0]] + colored(line[true_position[0]:true_position[1]],
                                                                 var.syntax_templates[template]) + \
                               line[true_position[1]:]
                    var.visible_content[index] = line

    @staticmethod
    def update_cursor():
        x, y = var.cursor_pos
        color, bg_color = var.settings['cursor_color']
        var.visible_content[y] = var.visible_content[y][:x] + colored(var.visible_content[y][x], color, bg_color) + var.visible_content[y][x:]
    
    @staticmethod
    def move_cursor(coords):
        start, end = var.page_res

        # start checking cursor move by y-coord
        if var.cursor_pos[1] + coords[1] < start and start > 0:  # move visible_content upper
            var.page_res = [var.page_res[0] - 1, var.page_res[1] - 1]
            var.cursor_pos[1] -= 1
        elif var.cursor_pos[1] + coords[1] > end and end < len(var.visible_content):   # move visible_content lower
            # len(var.visible_content) - lines counter
            var.page_res = [var.page_res[0] + 1, var.page_res[1] + 1]
            var.cursor_pos[1] += 1

        # start checking cursor by x-coord
        elif 0 > var.cursor_pos[0] + coords[0] and 0 < var.cursor_pos[0]:
            # move cursor to the end of the line, which is up to current cursor's pos
            var.cursor_pos = [len(var.content[var.cursor_pos[1]]) - 1, var.cursor_pos[1] - 1]
            return
        elif var.cursor_pos[0] + coords[0] == len(var.content[var.cursor_pos[1]]):  # move cursor to the lower line
            var.cursor_pos[1] += 1

        else:   # just move in the line
            var.cursor_pos = [var.cursor_pos[0] + coords[0], var.cursor_pos[1] + coords[1]]
        editor.update_cursor()


class display:
    @staticmethod
    def printinfo(text):
        display.draw(bottom_text=text)
    
    @staticmethod
    def draw(bottom_text=False):
        os.system(cls)
        print('=' * 3, var.header, '=' * (var.res[0] - len(var.header) - 5))    # x-res - len of the header and spaces
        start, end = var.page_res
        max_index_len = len(str(end))
        for index, element in enumerate(var.visible_content[start:end]):
            # 1   some text here
            index += 1
            line = str(index) + ' ' * (max_index_len - len(str(index))) + '  ' + element

            print(line)
        print('=' * var.res[0])
        print(colored('f1 - Find    f2 - Find and replace    f3 - rename current file    f4 - create custom '
                      'command\nf5 - save file'.title(), 'grey', 'on_white')) 
        if bottom_text:
            print(colored(bottom_text, 'grey', 'on_white'))

    @staticmethod
    def sync_visible_content_with_content():
        var.visible_content = var.content
        editor.check_syntax()
        

class File:
    @staticmethod
    def open(name):
        if not os.path.isfile(name):
            open(name, 'w').close()     # create file if it does not exists
        with open(name, 'r') as file:
            var.content = file.read().split('\n')   # because readlines returns lines with \n in the end
        display.sync_visible_content_with_content()

    @staticmethod
    def save():
        try:
            with open(var.filename, 'w') as file:
                file.write('\n'.join(var.content))
        except Exception as file_saving_failure:
            display.printinfo(f'Failed to save file: {file_saving_failure}. File will be saved as {var.filename + ".faildump"}')
            with open(var.filename + ".faildump", 'w') as file:
                file.write('\n'.join(var.content))
    
    @staticmethod
    def rename(rename_to):
        file = var.filename
        os.rename(file, rename_to)


def on_press(key):
    x, y = var.cursor_pos

    if key == Key.esc:
        deinit()
    if key in var.arrows:
        editor.move_cursor(var.arrows[key])
    elif key == Key.backspace:
        if x > 0:
            var.content[y] = var.content[y][:x - 1] + var.content[y][:x]
            var.cursor_pos = [x - 1, y]
    elif key == Key.space:
        var.content[y] = var.content[y][:x + 1] + ' ' + var.content[y][x + 1:]
    elif key == Key.delete:
        if x < len(var.content[y]):
            var.content[y] = var.content[y][:x] + var.content[y][:x + 1]
    elif key == Key.tab:
        var.content[y] = var.content[y][:x + 1] + ' ' * var.tab_size + var.content[y][x + 1:]
    else:
        key = str(key)[1:-1]
        if len(key) == 1:
            var.content[y] = var.content[y][:x - 1] + key + var.content[y][x + 1:]

    display.sync_visible_content_with_content()
    editor.check_syntax()
    display.draw()


def on_release(key):
    pass


def deinit(recall=False):
    # horrible peace of shit, but this is the problem of the library (no way)

    keyboard = Controller()

    keyboard.press(Key.enter)
    keyboard.release(Key.enter)

    keyboard.type('clear')

    keyboard.press(Key.enter)
    keyboard.release(Key.enter)

    if not recall:  # because this shit not always works in a first time
        deinit(recall=True)

    sys.exit()


if 'editor-actions.json' not in os.listdir('.'):
    # default editor settings

    var.editor_highlight = {"find": "red", "find-and-replace": "red", "cursor_enable": True,
                             "cursor_fg_color": "grey", "cursor_bg_color": "on_white", "bottom_text_color":
                             ['grey', 'on_white'], "top_text_color": ['grey', 'on_white']}
    var.settings = {"find": "red", "find-and-replace": "red", "cursor_enable": True, "cursor_color": ["grey", "on_white"]}
else:
    with open('editor-actions.json', 'r') as editor_actions:
        var.editor_highlight = json.load(editor_actions)[0]
        var.settings = var.editor_highlight

try:
    var.filename = sys.argv[1]
except IndexError:
    print('Please, run an editor in the format: python3 editor.py filename.txt')
    sys.exit()
filename_syntax_template = os.path.basename(var.filename).split('.')[-1] + '.json'
if filename_syntax_template in os.listdir('syntax'):
    with open('./syntax/' + filename_syntax_template, 'r') as file:
        var.syntax_templates = json.load(file)[0]

File.open(var.filename)

editor.check_syntax()
display.draw()

with Listener(
        on_press=on_press,
        on_release=on_release) as listener:
    listener.join()
