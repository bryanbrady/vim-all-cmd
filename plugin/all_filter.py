import os
import re
import vim
import tempfile

LAST_ALL_BNUM = "b:last_all_bnum"
ALL_ORIGINAL_BNUM = "b:all_original_bnum"

def new_search_buffer(search, grep_cmd, add_to_last=False, title=None):
    # if run from an All buffer, switch to the original first and override
    # "last" all buffer variable
    if var_exists(ALL_ORIGINAL_BNUM):
        bnum = vim.current.buffer.number
        vim.command("silent exec 'buffer' %s" % ALL_ORIGINAL_BNUM)
        vim.command("let %s=%d" % (LAST_ALL_BNUM, bnum))
    # create escaped title string
    if title is None:
        title = escape_title(search)
    else:
        title = escape_title(title)
    # modify title when appending a new search to an existing all buffer
    if add_to_last:
        bnum = last_all_buffer_num()
        if buffer_num_exists(bnum):
            old_title = escape_title(get_title(bnum))
            title = old_title+","+title
        else:
            echo("Last search buffer %d no longer exists!" % bnum)
            add_to_last = False
    # check that a buffer with the intended name doesn't already exist
    if buffer_name_exists(title):
        echo("buffer with name %r already exists!" % title)
        vim.command("silent exec 'buffer ' . '%s'" % title)
    else:
        # save state from the original buffer:
        #    row, col, filetype and buffer number
        source = get_current_state()
        with tempfile.NamedTemporaryFile() as fh:
            save_buffer_to_file(fh.name)
            if not add_to_last:
                bnum = new_scratch_buffer()
            else:
                bnum = last_all_buffer_num()
                vim.command("silent b %d" % bnum)
            success = read_search_output(grep_cmd, search, fh.name)
            if not success:
                if not add_to_last:
                    delete_buffer()
                echo("Pattern %r not found!" % search)
            else:
                sort_buffer()
                create_ctrl_q_maps(source, bnum)
                restore_state(source)
                set_title(title)
                minibuf_hack()


def sort_buffer():
    # reorder lines based on line number and remove duplicates
    vim.command("silent exec '0,$!sort -n|uniq'")


def echo(msg):
    vim.command("echom %r" % msg)


def throw(msg):
    vim.command("throw %r" % msg)


def escape_title(search):
    title = search.replace("|", "\|").replace(r'\b', '')
    title = title.replace("\"", "\\\"").replace(" ", "\ ")
    return title


def grep_opts():
    return vim.eval("g:all_filter_default_grep_opts")


def read_search_output(grep_cmd, search, fname):
    """Reads search output into current buffer.  Returns False if search
    contained no lines."""
    path = ""
    if var_exists("g:all_filter_grep_path"):
        path = vim.eval("g:all_filter_grep_path")
    # read grep/grin output into empty buffer
    vim.command("silent r ! %s%s -n %s %s %s" %
                (path, grep_cmd, grep_opts(), re.escape(search), fname))
    # hack to check if any lines found by cursor position
    row, col = vim.current.window.cursor
    return (row, col) != (1, 0)


def buffer_name_exists(title):
    #for (idx,b) in enumerate(vim.buffers):
    #  echo("idx:%s b:%s bname:%s fuck:%s title:%s"%(idx,b,b.name,get_title(idx),title))
    #  echo("wtf: %s"% (title == get_title(idx)))
    #  echo("abd: %s"% (buffer_num_exists(idx)))

    # ok = False
    # for bnum in range(len(vim.buffers)):
    #   x = title == get_title(bnum)
    #   y = buffer_num_exists(bnum)
    #   echo("bnum: %s x:%s y:%s"%(bnum,x,y))
    #   if x and y:
    #     ok = True
    #     break
    # return any((title == get_title(bnum)) & buffer_num_exists(bnum)
    #             for bnum in range(len(vim.buffers)))
    ok = any((title == get_title(bnum)) for bnum in range(len(vim.buffers)))
    #echo("OK:%s"%ok)
    return ok


def buffer_num_exists(bnum):
    return int(vim.eval("buflisted(%d)" % bnum))


def var_exists(name):
    return int(vim.eval("exists(%r)" % name))


def get_title(bnum):
    try:
        name = vim.buffers[bnum+1].name
        if name is not None:
            return name.rpartition("/")[2]
    except KeyError:
        pass

    return ''


def new_scratch_buffer():
    # new unnamed buffer
    vim.command("enew")
    # make it a scratch buffer
    vim.command("set buftype=nofile bufhidden=hide noswapfile")
    return vim.current.buffer.number


def get_current_state():
    row, col = vim.current.window.cursor
    ftype = vim.eval("&filetype")
    bnum = vim.current.buffer.number
    return dict(ftype=ftype, bnum=bnum, row=row, col=col)


def restore_state(state, delete_first_line=True):
    # set filetype
    if state['ftype'] != "":
        vim.command("setf "+state['ftype'])
    if delete_first_line:
        # hack to delete first line (blank)
        vim.command("normal ggdd")
    # jump to line in search buffer associated with line the search was
    # triggered from
    vim.command("exec search('^%d:')" % state['row'])
    # align current line at the bottom
    vim.command("normal zb")


def create_ctrl_q_maps(source, dest_bnum):
    # create map to the last search buffer from source buffer
    vim.command("silent b %d" % source['bnum'])
    vim.command("let %s=%s" % (LAST_ALL_BNUM, dest_bnum))
    vim.command('map <buffer> <C-q> :exec "buffer" %s<cr>' %
                    LAST_ALL_BNUM)
    #vim.command('map <buffer> <C-q> :exec "buffer" %s\|exec "normal j"<cr>' %
    #                LAST_ALL_BNUM)
    # create map to original buffer from search buffer
    vim.command("silent b %d" % dest_bnum)
    vim.command("let %s=%s" % (ALL_ORIGINAL_BNUM, source['bnum']))
    vim.command('map <buffer> <C-q> :let @z=GetFields(0,0,":")\|'
                'exec "buffer" %s\|'
                'exec "normal ".getreg("z")."Gzz"<CR>' % ALL_ORIGINAL_BNUM)


def last_all_buffer_num():
    return int(vim.eval(LAST_ALL_BNUM))


def all_original_buffer_num():
    return int(vim.eval(ALL_ORIGINAL_BNUM))


def set_title(title):
    # change name of buffer to search pattern
    vim.command("file "+title)


def minibuf_hack():
    # hack to make buffer show up in minibufexplorer
    vim.command("new")
    vim.command("bd")


def save_buffer_to_file(fname):
    vim.command("silent w! "+fname)


def delete_buffer(bnum=''):
    vim.command("bd "+bnum)


