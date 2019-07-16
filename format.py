import sublime
import sublime_plugin
import re

import re


class FormatError(ValueError):
    pass

RE_COMMENT = re.compile(r'^#')
RE_ENDS_IN_EMPTY_BLOCK = re.compile(r'\s+\{\s*\}$')
RE_ENDS_IN_NEW_BLOCK = re.compile(r'\{$')
RE_ENDS_IN_END_BLOCK = re.compile(r'\}$')
RE_BEGINS_WITH_END_BLOCK = re.compile(r'^\}')
RE_IS_ONLY_END_BLOCK = re.compile(r'^\}$')
RE_ENDS_IN_CONTINUATION = re.compile(r'\\$')
RE_ENDS_IN_NEW_BLOCK_CONT = re.compile(r'\{\s+\\$')
RE_ENDS_IN_NEW_COMMAND_CONT = re.compile(r'\[[^\t {\[["()\]}]+\s+\\$')
RE_IS_ONLY_END_ALL_CONT = re.compile(r'^\\?[\]})]\s*\\$')
RE_IS_ONLY_END_ALL_NOCONT = re.compile(r'^\\?[\]})"]$')
RE_ENDS_IN_END_ALL = re.compile(r'\\?[\]})"]$')

def format_irule(input_code, pre_indent='', tab_char=' ', tab_depth=4, debug=False):
    if debug:
        print('begin formatting...')
    tab_level = 0
    out = []
    continuation = False

    for in_line in input_code.splitlines():
        line = in_line.decode('utf8').strip()
        if debug:
            print(line)
        if line == '':
            if debug:
                print('empty')
            out.append('')
        elif RE_COMMENT.search(line) is not None:
            if debug:
                print('COMMENT')
            out.append(pre_indent + tab_char * tab_level + line)
        elif RE_ENDS_IN_EMPTY_BLOCK.search(line) is not None:
            if debug:
                print('ENDS_IN_EMPTY_BLOCK')
            out.append(pre_indent + tab_char * tab_level + line)
        elif RE_ENDS_IN_NEW_BLOCK.search(line) is not None:
            if debug:
                print('ENDS_IN_NEW_BLOCK')
            if RE_BEGINS_WITH_END_BLOCK.search(line) is not None:
                if debug:
                    print('  - and BEGINS_WITH_END_BLOCK')
                tab_level -= tab_depth
            out.append(pre_indent + tab_char * tab_level + line)
            tab_level += tab_depth
        elif RE_ENDS_IN_END_BLOCK.search(line) is not None:
            if debug:
                print('ENDS_IN_END_BLOCK')
            tab_level -= tab_depth
            if (tab_level < 0):
                tab_level = 0
                pre_indent = pre_indent[tab_depth:]
            out.append(pre_indent + tab_char * tab_level + line)
        elif not continuation and (RE_ENDS_IN_CONTINUATION.search(line) is not None):
            if debug:
                print('not continuation ENDS_IN_CONTINUATION')
            out.append(pre_indent + tab_char * tab_level + line)
            tab_level += tab_depth
            continuation = true
        elif continuation and (RE_ENDS_IN_NEW_BLOCK_CONT.search(line) is not None):
            if debug:
                print('continuation ENDS_IN_NEW_BLOCK_CONT')
            out.append(pre_indent + tab_char * tab_level + line)
            tab_level += tab_depth
        elif continuation and (RE_ENDS_IN_NEW_COMMAND_CONT.search(line) is not None):
            if debug:
                print('continuation ENDS_IN_NEW_COMMAND_CONT')
            out.append(pre_indent + tab_char * tab_level + line)
            tab_level += tab_depth
        elif continuation and (RE_IS_ONLY_END_ALL_CONT.search(line) is not None):
            if debug:
                print('continuation IS_ONLY_END_ALL_CONT')
            tab_level -= tab_depth
            if (tab_level < 0):
                tab_level = 0
                pre_indent = pre_indent[tab_depth:]
            out.append(pre_indent + tab_char * tab_level + line)
        elif continuation and (RE_IS_ONLY_END_ALL_NOCONT.search(line) is not None):
            if debug:
                print('continuation IS_ONLY_END_ALL_NOCONT')
            tab_level -= tab_depth
            if (tab_level < 0):
                tab_level = 0
                pre_indent = pre_indent[tab_depth:]
            out.append(pre_indent + tab_char * tab_level + line)
            tab_level -= tab_depth
            continuation = false
        elif continuation and (RE_ENDS_IN_END_ALL.search(line) is not None):
            if debug:
                print('continuation ENDS_IN_END_ALL')
            out.append(pre_indent + tab_char * tab_level + line)
            tab_level -= tab_depth
            continuation = false
        elif continuation and (RE_ENDS_IN_CONTINUATION.search(line) is not None):
            if debug:
                print('continuation ENDS_IN_CONTINUATION')
            out.append(pre_indent + tab_char * tab_level + line)
        elif continuation and (RE_ENDS_IN_CONTINUATION.search(line) is None):
            if debug:
                print('continuation and not ENDS_IN_CONTINUATION')
            out.append(pre_indent + tab_char * tab_level + line)
            tab_level -= tab_depth
            continuation = false
        else:
            if debug:
                print('default)')
            out.append(pre_indent + tab_char * tab_level + line)
        if (tab_level < 0):
            tab_level = 0
            pre_indent = pre_indent[tab_depth:]
    if debug:
        print('done formatting...')
    return '\n'.join(out)


def irule_formatter(view, edit, *args, **kwargs):
    if view.is_scratch():
        show_error('File is scratch')
        return

    # default parameters
    syntax = kwargs.get('syntax')
    saving = kwargs.get('saving', False)
    quiet = kwargs.get('quiet', False)

    # if (saving and not formatter.format_on_save_enabled()):
    #     return

    file_text = sublime.Region(0, view.size())
    file_text_utf = view.substr(file_text).encode('utf-8')
    if (len(file_text_utf) == 0):
        return

    try:
        stdout = format_irule(file_text_utf)
        view.replace(edit, file_text, stdout)
    except FormatError as e:
        show_error('Format error:\n' + stderr)



class FormatIruleCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        irule_formatter(self.view, edit)        
