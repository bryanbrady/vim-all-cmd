" all_filter.vim - A plug-in to filter lines of a buffer into a new search
" buffer
"
" Optional flags:
"     g:use_default_all_filter_mappings = 1 or 0
"


if !has('python3')
    " exit if python is not available.
    finish
endif


" Keep this disabled for debug
"if exists("b:did_all_filter_plugin")
"    finish " only load once
"endif
"let b:did_all_filter_plugin = 1


command! -nargs=+ All    :call NewAllBuffer("<args>", "grep")
command! -nargs=+ AllAdd :call NewAllBuffer("<args>", "grep", 'a')
command! -nargs=+ EAll    :call NewAllBuffer("<args>", "egrep")
command! -nargs=+ EAllAdd :call NewAllBuffer("<args>", "egrep", 'a')

" Default grep options:
"    -i = Perform case-insensitive searches
"    -a = force files to be treated as ASCII (to workaround malformed trace
"    files that look like binary format to grep).
let g:all_filter_default_grep_opts="-ia"


"-------------------------------------------------------------------------------
" Default Mappings
"-------------------------------------------------------------------------------
if !exists('g:use_default_all_filter_mappings') || (g:use_default_all_filter_mappings == 1)
    " Interactive filter
    nnoremap <silent> <Leader>af  :EAll <c-r>=input("Search for: ")<CR><CR>
    nnoremap <silent> <Leader>aaf :EAllAdd <c-r>=input("Search for: ")<CR><CR>
    " Last search term filter
    nnoremap <silent> <Leader>al  :exec "All" @/<CR>
    nnoremap <silent> <Leader>aal :exec "AllAdd" @/<CR>
    " Error filter
    nnoremap <silent> <Leader>ae  :exec "All error"<CR>
    nnoremap <silent> <Leader>aae :exec "AllAdd error"<CR>
    " Todo filter
    nnoremap <silent> <Leader>at  :exec "All todo"<CR>
    nnoremap <silent> <Leader>aat :exec "AllAdd todo"<CR>

    nnoremap <silent> <Leader>ac  :EAll <c-r>=expand("<cword>")<CR><CR>

endif

let s:plugin_path = escape(expand('<sfile>:p:h'), '\')
exe 'py3file ' . s:plugin_path . '/all_filter.py'

function! GetFields(start, stop, delim)
    " Return fields [start:stop] of the current line, split on *delim*
    let toks = split(getline('.'), a:delim)
    let start = a:start
    let stop = a:stop
    if len(toks) >= stop
        return join(toks[start : stop], a:delim)
    endif
    throw "Number of tokens on line less than the range requested"
endfunction


function! NewAllBuffer(search, grep_cmd, ...)
python3 <<PYTHON
e = vim.eval
flags = ''
if int(e("a:0")) > 0:
    flags = e("a:1")
add_to_last = 'a' in flags
new_search_buffer(e("a:search"), e("a:grep_cmd"), add_to_last=add_to_last)
PYTHON
endfunction


function! HideLines(pattern)
    exec "g/".a:pattern."/d"
endfunction


function! ShowLines(pattern)
    exec "g!/".a:pattern."/d"
endfunction

function! TestPy()
python3 <<PYTHON
toks=vim.current.line.split()
vim.command(r"return '%s'"%(",".join(toks)))
PYTHON
endfunction
