import re


RE_COMMENT = re.compile(r'^#')
RE_ENDS_IN_EMPTY_BLOCK = re.compile(r'\b\{\s*\}$')
RE_ENDS_IN_NEW_BLOCK = re.compile(r'\{$')
RE_BEGINS_WITH_END_BLOCK = re.compile(r'^\}')
RE_IS_ONLY_END_BLOCK = re.compile(r'^\}$')
RE_ENDS_IN_CONTINUATION = re.compile(r'\\$')
RE_ENDS_IN_NEW_BLOCK_CONT = re.compile(r'\{\s+\\$')
RE_ENDS_IN_NEW_COMMAND_CONT = re.compile(r'\[[^\t {\[["()\]}]+\s+\\$')
RE_IS_ONLY_END_BLOCK_CONT = re.compile(r'^\\?[\]})]\s*\\$')
RE_IS_ONLY_END_BLOCK_NOCONT = re.compile(r'^\\?[\]})"]$')
RE_ENDS_IN_END_BLOCK = re.compile(r'\\?[\]})"]$')

def format_irule(input_code, pre_indent='', tab_char=' ', tab_depth=4):
    tab_level = 0
    out = []
    continuation = False

    for in_line in line.splitlines():
        line = in_line.strip()
        if line == '':
            out.append('')
        else if RE_COMMENT.matchfull(line):
            out.append(pre_indent + tab_char.repeat(tab_level) + line)
        else if RE_ENDS_IN_EMPTY_BLOCK.matchfull(line):
            out.append(pre_indent + tab_char.repeat(tab_level) + line)
        else if RE_ENDS_IN_NEW_BLOCK.matchfull(line) or RE_IS_ONLY_END_BLOCK.matchfull(line):
            if (RE_BEGINS_WITH_END_BLOCK.matchfull(line)):
                tab_level -= tabDepth
            out.append(pre_indent + tab_char.repeat(tab_level) + line)
            tab_level += tabDepth
        else if RE_IS_ONLY_END_BLOCK.matchfull(line):
            tab_level -= tabDepth
            if (tab_level < 0):
                tab_level = 0
                pre_indent = pre_indent.substr(tabDepth, pre_indent.length - tabDepth)
            out.append(pre_indent + tab_char.repeat(tab_level) + line)
        else if (not continuation and RE_ENDS_IN_CONTINUATION.matchfull(line)):
            out.append(pre_indent + tab_char.repeat(tab_level) + line)
            tab_level += tabDepth
            continuation = true
        else if (continuation and RE_ENDS_IN_NEW_BLOCK_CONT.matchfull(line)):
            out.append(pre_indent + tab_char.repeat(tab_level) + line)
            tab_level += tabDepth
        else if (continuation and RE_ENDS_IN_NEW_COMMAND_CONT.matchfull(line)):
            out.append(pre_indent + tab_char.repeat(tab_level) + line)
            tab_level += tabDepth
        else if (continuation and RE_IS_ONLY_END_BLOCK_CONT.matchfull(line)):
            tab_level -= tabDepth
            if (tab_level < 0):
                tab_level = 0
                pre_indent = pre_indent.substr(tabDepth, pre_indent.length - tabDepth)
            out.append(pre_indent + tab_char.repeat(tab_level) + line)
        else if (continuation and (RE_IS_ONLY_END_BLOCK_NOCONTmatchfull(line))):
            tab_level -= tabDepth
            if (tab_level < 0):
                tab_level = 0
                pre_indent = pre_indent.substr(tabDepth, pre_indent.length - tabDepth)
            out.append(pre_indent + tab_char.repeat(tab_level) + line)
            tab_level -= tabDepth
            continuation = false
        else if (continuation and RE_ENDS_IN_END_BLOCK.matchfull(line)):
            out.append(pre_indent + tab_char.repeat(tab_level) + line)
            tab_level -= tabDepth
            continuation = false
        else if (continuation and RE_ENDS_IN_CONTINUATION.matchfull(line)):
            out.append(pre_indent + tab_char.repeat(tab_level) + line)
        else if (continuation and not (RE_ENDS_IN_CONTINUATION.matchfull(line))):
            out.append(pre_indent + tab_char.repeat(tab_level) + line)
            tab_level -= tabDepth
            continuation = false
        else:
            out.append(pre_indent + tab_char.repeat(tab_level) + line)
        if (tab_level < 0):
            tab_level = 0
            pre_indent = pre_indent.substr(tabDepth, pre_indent.length - tabDepth)
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

