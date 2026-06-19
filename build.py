#!/usr/bin/env python3
"""Builds index.html (the rendered specification) from protocol.md.

protocol.md is the single source of truth: this script parses it and renders
the styled page. Diagrams are the rendered D2 SVGs in diagrams/, inlined (white
background stripped) into figure boxes. If a diagram changed, re-render first
with `diagrams/render.sh diagrams/*.d2`, then run `python3 build.py`.

A few GitHub-friendly conventions in protocol.md drive the design-only bits:
  - ```mermaid``` block + `<!-- fig: name | caption -->`  -> themed D2 figure
  - `## N. Title <!-- nav: Short -->`  -> section pill + sidebar entry (label override)
  - > [!NOTE|TIP|IMPORTANT|WARNING|CAUTION]  -> callouts (GitHub alert syntax)
  - ```lang a title here```  -> the words after the language become the card label
Everything else (sections, tables, lists, code, inline formatting, RFC 2119
keywords, cross-references) is parsed straight from standard markdown.
See CLAUDE.md for the full set of conventions.
"""
import re, html as _html, pathlib

HERE = pathlib.Path(__file__).parent
DIAG = HERE / "diagrams"
SRC = HERE / "protocol.md"
OUT = HERE / "index.html"

# ---------------------------------------------------------------- diagrams
def svg(name):
    s = (DIAG / (name + ".svg")).read_text()
    s = re.sub(r'^<\?xml[^>]*\?>', '', s).strip()
    s = s.replace('fill="#FFFFFF"', 'fill="transparent"', 1)  # the bg rect
    return s

def fig(cap, name):
    return ('<figure class="fig"><figcaption class="cap">' + cap +
            '</figcaption><div class="d">' + svg(name) + '</div>'
            '<div class="hint">click to enlarge</div></figure>')

def sec(roman, anchor, title):
    return ('<div class="sec" id="' + anchor + '"><span class="pill">'
            '<span class="sq"></span>' + roman + '&nbsp;&nbsp;' + title +
            '</span><span class="rule"></span></div>')

def code(name, lang, pre_html):
    return ('<div class="codecard"><div class="bar"><span>' + name +
            '</span><span>' + lang + '</span></div><pre>' + pre_html +
            '</pre></div>')

def ref(n, suf=''):
    return '<a class="ref" href="#sec-' + str(n) + '">#' + str(n) + (suf or '') + '</a>'

# ---------------------------------------------------------------- syntax highlight
def hl_jsonc(src):
    out = []
    for line in src.split('\n'):
        ci = line.find('//')
        body, com = (line[:ci], line[ci:]) if ci != -1 else (line, '')
        res, i, s = '', 0, body
        while i < len(s):
            if s[i] == '"':
                j = i + 1
                while j < len(s) and s[j] != '"':
                    j += 1
                tok = s[i:j + 1]
                k = j + 1
                while k < len(s) and s[k] == ' ':
                    k += 1
                cls = 'tok-key' if (k < len(s) and s[k] == ':') else 'tok-str'
                res += '<span class="' + cls + '">' + _html.escape(tok) + '</span>'
                i = j + 1
            else:
                j = i
                while j < len(s) and s[j] != '"':
                    j += 1
                seg = _html.escape(s[i:j])
                seg = re.sub(r'\b(true|false|null)\b',
                             r'<span class="tok-bool">\1</span>', seg)
                res += seg
                i = j
        if com:
            res += '<span class="tok-com">' + _html.escape(com) + '</span>'
        out.append(res)
    return '\n'.join(out)

def hl_html(src):
    e = _html.escape(src)
    e = re.sub(r'(&lt;!--.*?--&gt;)', r'<span class="tok-com">\1</span>', e, flags=re.S)
    e = re.sub(r'(&quot;.*?&quot;)', r'<span class="tok-str">\1</span>', e)
    return e

def hl_text(src):
    return _html.escape(src)

# ---------------------------------------------------------------- inline markdown
def emph(s):
    return re.sub(r'\b(MUST NOT|SHOULD NOT|MUST|SHOULD|MAY)\b',
                  r'<b class="req">\1</b>', s)

def _typography(s):
    """Raw-text typographic substitutions (run before HTML-escaping)."""
    s = s.replace(' -> ', ' → ')          # arrow
    s = re.sub(r'(?<= )-(?= )', '—', s)    # space-hyphen-space -> em dash
    return s

def inline(s):
    """Render inline markdown to HTML: code, bold, italic, links, RFC keywords,
    cross-references, and typography."""
    codes = []
    def stash(m):
        codes.append(m.group(1))
        return '\x00%d\x00' % (len(codes) - 1)
    s = re.sub(r'`([^`]+)`', stash, s)
    s = _typography(s)
    s = _html.escape(s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a class="ref" href="\2">\1</a>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<![*\w])\*([^*\n]+?)\*(?!\*)', r'<em>\1</em>', s)
    s = re.sub(r'\bsections\s+(\d+)\s*(?:-|—)\s*(\d+)',
               lambda m: ref(int(m.group(1))) + '&ndash;' + ref(int(m.group(2))), s)
    s = re.sub(r'\bsection\s+(\d+)([ab])?',
               lambda m: ref(int(m.group(1)), m.group(2) or ''), s)
    s = emph(s)
    s = re.sub('\x00(\\d+)\x00',
               lambda m: '<code>' + _html.escape(codes[int(m.group(1))]) + '</code>', s)
    return s

def heading_inline(s):
    """For section pills and subheads: typography + 'Na.' -> 'Na ·', no keyword
    styling or cross-ref linking."""
    m = re.match(r'^(\d+[a-z])\.\s*(.*)$', s)
    if m:
        s = m.group(1) + ' · ' + m.group(2)
    s = _typography(s)
    s = _html.escape(s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    return s

# ---------------------------------------------------------------- figures map
ROMANS = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
          'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX']

ALERT_VARIANT = {'NOTE': '', 'TIP': 'tip', 'IMPORTANT': '',
                 'WARNING': 'warn', 'CAUTION': 'warn'}

# Each ```mermaid``` block in protocol.md is followed by a marker comment naming
# its themed D2 SVG and caption: <!-- fig: <svg-name> | <caption> -->

def auto_nav(title):
    """Shorten a section heading into a sidebar nav label: drop a trailing
    parenthetical and anything after an em/hyphen separator. A heading MAY
    override this with a trailing `<!-- nav: ... -->` comment."""
    t = re.sub(r'\s*\([^)]*\)\s*$', '', title)
    t = re.split(r'\s+[-—]\s+', t)[0]
    return t.strip()

def parse_h2(line):
    """A '## N. Title <!-- nav: Label -->' heading -> (num, clean_title, nav)."""
    m = re.match(r'^##\s+(\d+)\.\s+(.*)$', line.strip())
    if not m:
        return None
    num, raw = int(m.group(1)), m.group(2).strip()
    nm = re.search(r'<!--\s*nav:\s*(.+?)\s*-->', raw)
    title = re.sub(r'\s*<!--.*?-->\s*$', '', raw).strip()
    return num, title, (nm.group(1).strip() if nm else auto_nav(title))

def scan_toc(md):
    """Build the sidebar table of contents from the markdown's ## headings."""
    toc = []
    for line in md.split('\n'):
        r = parse_h2(line)
        if r:
            num, _title, nav = r
            toc.append((ROMANS[num], num, nav))
    return toc

# ---------------------------------------------------------------- block renderers
def render_defgrid(items):
    rows = ''
    for it in items:
        it = re.sub(r'^[-*]\s+', '', it)
        m = re.match(r'^\*\*(.+?)\*\*\s*-\s*(.*)$', it)
        k, v = (m.group(1), m.group(2)) if m else ('', it)
        rows += ('<span class="k">' + _html.escape(k) + '</span>'
                 '<span class="vv">' + inline(v) + '</span>')
    return '<div class="defgrid">' + rows + '</div>'

def render_list(items):
    parsed = []
    check = False
    for it in items:
        m = re.match(r'^[-*]\s+\[[ xX]\]\s+(.*)$', it)
        if m:
            check = True; parsed.append(m.group(1)); continue
        m = re.match(r'^[-*]\s+(.*)$', it)
        if m:
            parsed.append(m.group(1)); continue
        m = re.match(r'^(\d+)\.\s+(.*)$', it)
        if m:
            parsed.append(('ol', m.group(2)))
    if check:
        lis = ''.join('<li><span class="box"></span><span>' + inline(t) +
                      '</span></li>' for t in parsed)
        return '<ul class="check">' + lis + '</ul>'
    if parsed and isinstance(parsed[0], tuple):
        lis = ''.join('<li><span class="m">' + str(k + 1) + '</span><span>' +
                      inline(t) + '</span></li>' for k, (_, t) in enumerate(parsed))
        return '<ul class="list">' + lis + '</ul>'
    lis = ''.join('<li><span class="m">&mdash;</span><span>' + inline(t) +
                  '</span></li>' for t in parsed)
    return '<ul class="list">' + lis + '</ul>'

def _cells(row):
    row = row.strip()
    if row.startswith('|'):
        row = row[1:]
    if row.endswith('|'):
        row = row[:-1]
    return [c.strip() for c in row.split('|')]

def _is_placeholder(plain):
    return plain.lower() in ('no', '-', '—', '') or plain.lower().startswith('always empty')

def render_table(rows):
    head = _cells(rows[0])
    body = [_cells(r) for r in rows[2:]]
    ncol = len(head)
    # A non-key column renders as dark mono when every non-placeholder cell in it
    # is an identifier (i.e. backticked in the source) — e.g. the "metadata" column.
    mono_col = [False] * ncol
    for ci in range(1, ncol):
        cells = [r[ci] for r in body if ci < len(r)]
        real = [c for c in cells if not _is_placeholder(re.sub(r'[`*]', '', c).strip())]
        mono_col[ci] = bool(real) and all('`' in c for c in real)
    ths = ''.join('<th>' + inline(h) + '</th>' for h in head)
    trs = ''
    for r in body:
        tds = ''
        for ci, c in enumerate(r):
            plain = re.sub(r'[`*]', '', c).strip()
            if ci == 0 or mono_col[ci]:                   # key / identifier column
                tds += '<td class="mono">' + _html.escape(_typography(plain)) + '</td>'
            elif _is_placeholder(plain):
                tds += '<td class="muted">' + inline(c) + '</td>'
            else:
                tds += '<td>' + inline(c) + '</td>'
        trs += '<tr>' + tds + '</tr>'
    return ('<div class="tablewrap"><table><thead><tr>' + ths +
            '</tr></thead><tbody>' + trs + '</tbody></table></div>')

def render_callout(buf):
    txt = ' '.join(b for b in buf).strip()
    m = re.match(r'^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*(.*)$', txt, re.S)
    typ, rest = (m.group(1), m.group(2).strip()) if m else ('NOTE', txt)
    variant = ALERT_VARIANT.get(typ, '')
    m = re.match(r'^\*\*(.+?)\.?\*\*\s*(.*)$', rest, re.S)
    if m:
        label = typ.capitalize() + ' &middot; ' + _html.escape(m.group(1).strip())
        body = m.group(2).strip()
    else:
        label = typ.capitalize()
        body = rest
    cls = 'note' + ((' ' + variant) if variant else '')
    return ('<div class="' + cls + '"><div class="lbl">' + label +
            '</div><div class="txt">' + inline(body) + '</div></div>')

def render_preamble(lines):
    out = []
    h1 = next(l for l in lines if l.startswith('# '))
    m = re.match(r'^(.*?)\s*\((v\d+)\)\s*$', h1[2:].strip())
    title, badge = (m.group(1), m.group(2)) if m else (h1[2:].strip(), '')
    out.append('<div class="eyebrow">RFC-style specification &middot; server adapter</div>')
    out.append('<h1 class="title">' + _html.escape(title) +
               (' <span class="v">' + badge + '</span>' if badge else '') + '</h1>')
    rest = lines[lines.index(h1) + 1:]
    i = 0
    while i < len(rest):
        l = rest[i].strip()
        if not l or l == '---':
            i += 1; continue
        if l.lower().startswith('terminology'):
            i += 1; items = []
            while i < len(rest):
                t = rest[i].strip()
                if t.startswith('- '):
                    items.append(t); i += 1
                elif not t:
                    i += 1
                    if i < len(rest) and not rest[i].strip().startswith('- '):
                        break
                else:
                    break
            out.append(render_defgrid(items))
        else:
            buf = [l]; i += 1
            while i < len(rest) and rest[i].strip() and not rest[i].strip().startswith('- ') \
                    and not rest[i].strip().lower().startswith('terminology'):
                buf.append(rest[i].strip()); i += 1
            out.append('<p class="lede">' + inline(' '.join(buf)) + '</p>')
    return '\n'.join(out)

def _is_list(l):
    return bool(re.match(r'^[-*]\s+', l) or re.match(r'^\d+\.\s+', l))

def render_blocks(lines):
    out, i, n, fig_i = [], 0, len(lines), 0
    while i < n:
        raw = lines[i]; l = raw.strip()
        if not l or l == '---':
            i += 1; continue
        r = parse_h2(l)                                  # section heading
        if r:
            num, title, _nav = r
            out.append(sec(ROMANS[num], 'sec-' + str(num), heading_inline(title)))
            i += 1; continue
        if l.startswith('<!--'):                          # stray HTML comment
            while i < n and '-->' not in lines[i]:
                i += 1
            i += 1; continue
        m = re.match(r'^###\s+(.*)$', l)                 # subhead
        if m:
            out.append('<div class="subhead">' + heading_inline(m.group(1).strip()) + '</div>')
            i += 1; continue
        m = re.match(r'^```(.*)$', raw)                  # fenced code / diagram
        if m:
            info = m.group(1).strip().split(None, 1)
            lang = info[0] if info else ''
            title = info[1] if len(info) > 1 else ''
            j = i + 1; buf = []
            while j < n and not lines[j].lstrip().startswith('```'):
                buf.append(lines[j]); j += 1
            content = '\n'.join(buf)
            i = j + 1
            if lang == 'mermaid':
                while i < n and not lines[i].strip():     # find the fig marker
                    i += 1
                fm = re.match(r'<!--\s*fig:\s*([\w.\-]+)\s*\|\s*(.+?)\s*-->',
                              lines[i].strip()) if i < n else None
                if not fm:
                    raise SystemExit('build error: a ```mermaid``` block is missing '
                                     'its "<!-- fig: name | caption -->" marker')
                fig_i += 1
                out.append(fig('Fig. ' + str(fig_i) + ' &mdash; ' + fm.group(2).strip(),
                               fm.group(1)))
                i += 1
            else:
                pre = hl_jsonc(content) if lang == 'jsonc' else \
                      hl_html(content) if lang == 'html' else hl_text(content)
                out.append(code(title or (lang or 'text'), lang or 'text', pre))
            continue
        if l.startswith('>'):                            # blockquote / alert
            buf = []
            while i < n and lines[i].strip().startswith('>'):
                buf.append(lines[i].strip()[1:].lstrip()); i += 1
            out.append(render_callout(buf)); continue
        if l.startswith('|'):                            # table
            buf = []
            while i < n and lines[i].strip().startswith('|'):
                buf.append(lines[i].strip()); i += 1
            out.append(render_table(buf)); continue
        if _is_list(l):                                  # list / checklist
            buf = []
            while i < n:
                t = lines[i].strip()
                if _is_list(t):
                    buf.append(t); i += 1
                elif not t:                              # blank: tight list -> skip, else end
                    if i + 1 < n and _is_list(lines[i + 1].strip()):
                        i += 1; continue
                    break
                elif buf:                                # wrapped continuation of the item
                    buf[-1] += ' ' + t; i += 1
                else:
                    break
            out.append(render_list(buf)); continue
        buf = [l]; i += 1                                # paragraph
        while i < n:
            t = lines[i].strip()
            if not t or t == '---' or t.startswith('#') or t.startswith('```') \
                    or t.startswith('>') or t.startswith('|') or _is_list(t):
                break
            buf.append(t); i += 1
        out.append('<p class="body">' + inline(' '.join(buf)) + '</p>')
    return out

def parse_spec(md):
    lines = md.split('\n')
    h2 = next(i for i, l in enumerate(lines) if l.startswith('## '))
    out = [render_preamble(lines[:h2])]
    out += render_blocks(lines[h2:])
    out.append('<div class="endmark">End of specification &middot; Inertia v3 &middot; server adapter</div>')
    return out

# ================================================================ CSS
CSS = r"""
*{box-sizing:border-box}
body{margin:0;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
::selection{background:#1F7A4D;color:#fff}
.page{position:relative;min-height:100vh;background:#F1EEE7;color:#23201A;font-family:'Newsreader',Georgia,serif}

.shell{max-width:1400px;margin:0 auto;display:flex;align-items:flex-start;position:relative}
.rail{flex:none;width:290px;position:sticky;top:0;height:100vh;z-index:10}

.binder{position:absolute;left:18px;top:0;bottom:0;width:16px;display:flex;flex-direction:column;justify-content:space-around;padding:24px 0;z-index:20;pointer-events:none}
.binder i{width:13px;height:13px;border-radius:50%;background:#E2DFD6;box-shadow:inset 0 1px 2px rgba(0,0,0,.22),0 1px 0 rgba(255,255,255,.6);display:block}

.sidebar{height:100%;width:100%;padding:42px 26px 30px 58px;border-right:1px solid #E0DDD1;overflow-y:auto}
.brand{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:14px;letter-spacing:.02em;color:#1F7A4D}
.brand-sub{font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.13em;color:#a3a299;text-transform:uppercase;margin-top:7px}
.toc{margin-top:30px;border-top:1px solid #DCD9CD}
.toc a{display:flex;align-items:flex-end;gap:12px;min-height:42px;padding:11px 0 9px;border-bottom:1px solid #DCD9CD;text-decoration:none;cursor:pointer}
.toc a .n{font-family:'JetBrains Mono',monospace;font-size:10.5px;color:#b2b1a7;width:30px;flex:none;letter-spacing:.04em}
.toc a .t{font-family:'Newsreader',serif;font-size:15px;color:#5a5952;line-height:1.24}
.toc a.active .n{color:#1F7A4D}
.toc a.active .t{color:#1F7A4D;font-weight:600}
.mobnav{display:none}

.badge{position:fixed;left:16px;bottom:26px;width:62px;height:62px;border-radius:3px;background:#23201A;color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:0 8px 22px -6px rgba(0,0,0,.42);z-index:30}
.badge .s{font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:.1em;color:#9C9285}
.badge .num{font-family:'JetBrains Mono',monospace;font-size:18px;font-weight:700;line-height:1;color:#fff}
.badge .lbl{font-family:'JetBrains Mono',monospace;font-size:7.5px;letter-spacing:.08em;color:#7FC79A;margin-top:2px}

.content{flex:1;min-width:0;padding:48px 56px 110px}
.article{max-width:840px;margin:0 auto;background:#FCFBF8;border:1px solid #EAE7DE;border-radius:5px;box-shadow:0 1px 3px rgba(0,0,0,.05),0 28px 64px -34px rgba(0,0,0,.22);padding:62px 70px 76px;position:relative}

.eyebrow{font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:#9a998f}
h1.title{font-family:'Newsreader',serif;font-size:46px;line-height:1.06;font-weight:600;letter-spacing:-.016em;color:#23201A;margin:10px 0 0}
.title .v{font-family:'JetBrains Mono',monospace;font-size:.4em;vertical-align:middle;letter-spacing:0;color:#1F7A4D;font-weight:600}
.lede{font-family:'Newsreader',serif;font-size:18px;line-height:1.6;color:#56554d;margin:16px 0 0;max-width:64ch}
.defgrid{margin:24px 0 0;display:grid;grid-template-columns:auto 1fr;gap:7px 16px;align-items:baseline}
.defgrid .k{font-family:'JetBrains Mono',monospace;font-size:11.5px;color:#1F7A4D}
.defgrid .vv{font-family:'Newsreader',serif;font-size:15.5px;color:#3a3a36}

.sec{display:flex;align-items:center;gap:12px;margin-top:50px;scroll-margin-top:24px}
.sec .pill{display:inline-flex;align-items:center;gap:8px;font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.13em;text-transform:uppercase;color:#23201A;border:1px solid #cfcec4;border-radius:2px;padding:5px 12px;background:#fff}
.sec .pill .sq{width:7px;height:7px;background:#1F7A4D;display:inline-block}
.sec .rule{flex:1;height:1px;background:#E4E3DA}

p.body{font-family:'Newsreader',serif;font-size:17px;line-height:1.72;color:#34302A;margin:18px 0 14px;max-width:66ch;text-wrap:pretty}
.body strong,.txt strong,.list strong,td strong{font-weight:600;color:#33322c}
.subhead{font-family:'Newsreader',serif;font-size:22px;font-weight:600;color:#23201A;margin:30px 0 2px}
code{font-family:'JetBrains Mono',monospace;font-size:.82em;color:#1F7A4D;background:rgba(31,122,77,.09);padding:1px 4px;border-radius:2px;overflow-wrap:break-word}
p.body,.lede,.txt,ul.list li,ul.check li,td,.defgrid .vv{overflow-wrap:break-word}
.req{font-family:'JetBrains Mono',monospace;font-size:.78em;letter-spacing:.04em;color:#1F7A4D;font-weight:700}
a.ref{color:#1F7A4D;text-decoration:none;border-bottom:1px solid rgba(31,122,77,.32)}
a.ref:hover{border-bottom-color:#1F7A4D}

ul.list{list-style:none;padding:0;margin:8px 0 16px}
ul.list li{display:flex;gap:12px;align-items:baseline;margin-bottom:11px;font-family:'Newsreader',serif;font-size:16.5px;line-height:1.66;color:#34302A;max-width:66ch}
ul.list li .m{font-family:'JetBrains Mono',monospace;color:#1F7A4D;flex:none;font-size:.9em}
ul.list li>span:last-child,ul.check li>span:last-child{min-width:0}

ul.check{list-style:none;padding:0;margin:12px 0}
ul.check li{display:flex;gap:13px;align-items:flex-start;margin-bottom:11px;font-family:'Newsreader',serif;font-size:16px;line-height:1.6;color:#34302A;max-width:70ch}
ul.check li .box{width:15px;height:15px;border:1.5px solid #1F7A4D;border-radius:3px;flex:none;margin-top:4px}

.tablewrap{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:14px 0 24px}
table{width:100%;border-collapse:collapse;border:1px solid #E4E3DA}
th{text-align:left;font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.09em;text-transform:uppercase;color:#fff;background:#23201A;font-weight:600;padding:8px 14px}
td{padding:10px 14px;border:1px solid #E4E3DA;font-family:'Newsreader',serif;font-size:14.5px;color:#3a3a36;vertical-align:top}
td.mono{font-family:'JetBrains Mono',monospace;font-size:12px;color:#23201A}
td.muted{font-family:'JetBrains Mono',monospace;font-size:11.5px;color:#9a998f}
td code{font-size:.92em}

.codecard{margin:14px 0 22px;border:1px solid #322A20;border-radius:4px;overflow:hidden;background:#211C16}
.codecard .bar{display:flex;justify-content:space-between;padding:9px 16px;border-bottom:1px solid #322A20;background:#2A241C;font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:#9C9285}
.codecard pre{margin:0;padding:16px 18px;font-family:'JetBrains Mono',monospace;font-size:12.5px;line-height:1.75;color:#D8CFC1;overflow-x:auto;white-space:pre}
.tok-key{color:#7FC79A}.tok-str{color:#C7B79A}.tok-com{color:#8A8075;font-style:italic}.tok-bool{color:#D9A86A}

.note{margin:16px 0;border:1px solid #C2D8C9;border-radius:4px;background:#EFF5F0;padding:14px 18px}
.note .lbl{font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:#1F7A4D;margin-bottom:6px}
.note .txt{font-family:'Newsreader',serif;font-size:15.5px;line-height:1.62;color:#3a3a36}
.note.warn{border-color:#E2C6A3;background:#F7F0E6}
.note.warn .lbl{color:#B0712B}
.note.tip{border-color:#BBD9C4;background:#EDF6F0}

.fig{margin:18px 0 24px;border:1px solid #E4E3DA;border-radius:4px;background:#FBFAF5;padding:16px 18px 16px}
.fig .cap{font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:#9a998f;margin-bottom:12px}
.fig .d{display:flex;justify-content:center;cursor:zoom-in}
.fig .d svg{max-width:100%;height:auto}
.fig .hint{font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:.12em;text-transform:uppercase;color:#bdbcb2;margin-top:10px;text-align:right}

.lightbox{position:fixed;inset:0;background:rgba(33,28,22,.80);display:none;align-items:center;justify-content:center;z-index:100;padding:30px}
.lightbox.open{display:flex}
.lightbox .frame{background:#FBFAF5;border:1px solid #E4E3DA;border-radius:6px;box-shadow:0 30px 80px -20px rgba(0,0,0,.55);max-width:96vw;max-height:92vh;overflow:auto;padding:30px 34px}
.lightbox .frame svg{display:block}
.lightbox .close{position:fixed;top:20px;right:24px;font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:#F1EEE7;background:rgba(0,0,0,.30);border:1px solid rgba(255,255,255,.28);border-radius:4px;padding:8px 13px;cursor:pointer}

.endmark{margin-top:46px;padding-top:18px;border-top:1px solid #E4E3DA;font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:#b2b1a7}

/* ---- responsive ---- */
@media (max-width:1180px){
  .rail{width:248px}
  .sidebar{padding:38px 20px 26px 46px}
  .binder{left:14px}
  .content{padding:42px 38px 96px}
  .article{padding:54px 48px 64px}
}
@media (max-width:880px){
  .shell{display:block}
  .rail{display:contents}
  .binder{display:none}
  .sidebar{position:sticky;top:0;z-index:40;height:auto;overflow:visible;border-right:none;border-bottom:1px solid #E0DDD1;background:#F1EEE7;padding:12px 22px;display:flex;align-items:center;gap:12px}
  .brandbar{display:flex;align-items:baseline;gap:11px;flex:none}
  .brand-sub{margin-top:0}
  .toc{display:none}
  .mobnav{display:block;margin-left:auto;max-width:58%;font-family:'JetBrains Mono',monospace;font-size:12px;letter-spacing:.02em;color:#1F7A4D;background:#FCFBF8;border:1px solid #cfcec4;border-radius:3px;padding:7px 26px 7px 10px;cursor:pointer;-webkit-appearance:none;appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'%3E%3Cpath d='M1 1l4 4 4-4' fill='none' stroke='%231F7A4D' stroke-width='1.5'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 10px center}
  .sec{scroll-margin-top:70px}
  .content{padding:30px 22px 72px}
  .article{padding:34px 24px 46px;border-radius:4px;box-shadow:0 1px 3px rgba(0,0,0,.05),0 14px 36px -26px rgba(0,0,0,.2)}
}
@media (max-width:560px){
  .sidebar{padding:11px 16px}
  .brand-sub{display:none}
  .mobnav{max-width:62%}
  .content{padding:22px 14px 60px}
  .article{padding:26px 18px 38px}
  h1.title{font-size:33px}
  .lede{font-size:16.5px}
  p.body{font-size:16px}
  .sec{margin-top:38px}
  .codecard pre{font-size:11.5px}
}
"""

# ================================================================ sidebar
def sidebar(toc):
    items = ''
    opts = '<option value="">Jump to section&hellip;</option>'
    for roman, n, title in toc:
        items += ('<a href="#sec-' + str(n) + '"><span class="n">' + roman +
                  '</span><span class="t">' + _html.escape(title) + '</span></a>')
        opts += ('<option value="#sec-' + str(n) + '">' + roman + ' &middot; '
                 + _html.escape(title) + '</option>')
    return ('<aside class="sidebar">'
            '<div class="brandbar"><div class="brand">INERTIA</div>'
            '<div class="brand-sub">server adapter / spec</div></div>'
            '<select class="mobnav" aria-label="Jump to section" '
            'onchange="if(this.value){location.hash=this.value;this.selectedIndex=0}">'
            + opts + '</select>'
            '<nav class="toc">' + items + '</nav></aside>')

# ================================================================ body
MD = SRC.read_text()
TOC = scan_toc(MD)          # sidebar built from the markdown's ## headings
B = parse_spec(MD)

# ================================================================ assemble
SCRIPT = """
(function(){
  var links = Array.prototype.slice.call(document.querySelectorAll('.toc a'));
  var secs = links.map(function(a){ return document.querySelector(a.getAttribute('href')); });
  function onScroll(){
    var y = window.scrollY + 120, idx = 0;
    for (var i=0;i<secs.length;i++){ if (secs[i] && secs[i].offsetTop <= y) idx = i; }
    links.forEach(function(a,i){ a.classList.toggle('active', i===idx); });
  }
  window.addEventListener('scroll', onScroll, {passive:true});
  onScroll();

  var lb = document.getElementById('lightbox'), frame = lb.querySelector('.frame');
  function openLB(svg){
    frame.innerHTML='';
    var c = svg.cloneNode(true);
    var vb = (c.getAttribute('viewBox') || '0 0 800 600').split(/\s+/).map(Number);
    var vw = vb[2] || 800, vh = vb[3] || 600;
    var maxW = window.innerWidth * 0.92 - 70, maxH = window.innerHeight * 0.92 - 64;
    var scale = Math.min(maxW / vw, maxH / vh);
    c.setAttribute('width', Math.round(vw * scale));
    c.setAttribute('height', Math.round(vh * scale));
    c.style.maxWidth = 'none';
    frame.appendChild(c);
    lb.classList.add('open'); document.body.style.overflow='hidden';
  }
  function closeLB(){ lb.classList.remove('open'); frame.innerHTML=''; document.body.style.overflow=''; }
  Array.prototype.forEach.call(document.querySelectorAll('.fig .d'), function(d){
    d.addEventListener('click', function(){ var s=d.querySelector('svg'); if(s) openLB(s); });
  });
  lb.addEventListener('click', function(e){ if(e.target===lb || e.target.classList.contains('close')) closeLB(); });
  document.addEventListener('keydown', function(e){ if(e.key==='Escape') closeLB(); });
})();
"""

def render():
    doc = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<title>The Inertia Protocol v3 &mdash; Server Adapter Specification</title>\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=JetBrains+Mono:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">\n'
        '<style>' + CSS + '</style>\n</head>\n<body>\n'
        '<div class="page">\n'
        '<div class="shell">\n'
        '<div class="rail"><div class="binder">' + ('<i></i>' * 22) + '</div>\n'
        + sidebar(TOC) + '</div>\n'
        '<main class="content"><article class="article">\n'
        + '\n'.join(B) +
        '\n</article></main>\n</div>\n</div>\n'
        '<div class="lightbox" id="lightbox"><button class="close">Close &times;</button><div class="frame"></div></div>\n'
        '<script>' + SCRIPT + '</script>\n'
        '</body>\n</html>\n'
    )
    OUT.write_text(doc)
    print("wrote", OUT, len(doc), "bytes")

render()
