import html
import re

# Entity corruption patterns found in AG News (31% of rows).
PATTERNS = {
    "bare_num":   r"#\d{2,4};",                          # #39;  <- &#39;
    "bare_named": r"\b(?:lt|gt|quot|amp|nbsp|apos);",    # gt;   <- &gt;
    "intact":     r"&(?:#\d+|\w+);",                     # &amp; never unescaped
}
CORRUPT = PATTERNS["bare_num"] + "|" + PATTERNS["bare_named"]

_NUM = re.compile(r"(?<!&)#(3[0-9]|1[0-9]{2}|2[0-9]{2});")
_NAMED = re.compile(r"(?<!&)\b(lt|gt|quot|amp|nbsp|apos);")


def repair(s):
    """Reinsert dropped ampersands, then unescape HTML entities."""
    s = _NUM.sub(r"&#\1;", s)
    s = _NAMED.sub(r"&\1;", s)
    return html.unescape(s)


def corruption_rate(series):
    return series.str.contains(CORRUPT, regex=True).mean()



