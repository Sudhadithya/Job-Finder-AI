"""
text_cleaner.py — Converts raw HTML job descriptions into clean plain text.

Handles:
- HTML entity decoding (&amp; &lt; &gt; &#x27; &nbsp; etc.)
- Structural tag -> newline conversion (<p>, <br>, <li>, <h1-h6>)
- <script> and <style> block removal
- All remaining tag stripping
- Whitespace normalization
"""
import re
import html


def clean_description(raw: str) -> str:
    """
    Convert raw HTML job description to clean plain text / light markdown.
    Safe to call on already-clean text (idempotent).

    Handles both:
    - Normal HTML:          <p>text</p>
    - Double-encoded HTML:  &lt;p&gt;text&lt;/p&gt;  (as returned by Greenhouse)
    """
    if not raw:
        return ""

    # 0. Pre-unescape: convert &lt; &gt; &amp; etc. -> actual characters
    #    This handles Greenhouse's double-encoded HTML before tag processing.
    text = html.unescape(raw)

    # 1. Remove <script>…</script> and <style>…</style> blocks entirely
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL | re.IGNORECASE)

    # 2. Convert block/structural tags -> newlines before stripping
    #    <p>, </p>, <div>, </div>, <br>, <br/> -> newline
    text = re.sub(r'<(p|div|section|article)[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</(p|div|section|article)>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)

    # 3. Convert <li> -> "- " bullet points
    text = re.sub(r'<li[^>]*>', '\n- ', text, flags=re.IGNORECASE)
    text = re.sub(r'</li>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<ul[^>]*>|</ul>|<ol[^>]*>|</ol>', '\n', text, flags=re.IGNORECASE)

    # 4. Convert heading tags -> markdown headings
    for i in range(1, 7):
        text = re.sub(rf'<h{i}[^>]*>', '\n### ', text, flags=re.IGNORECASE)
        text = re.sub(rf'</h{i}>', '\n', text, flags=re.IGNORECASE)

    # 5. Convert <strong>, <h6>, <em>, <i> -> plain (strip the tags)
    text = re.sub(r'<(strong|b|em|i|span|a)[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'</(strong|b|em|i|span|a)>', '', text, flags=re.IGNORECASE)

    # 6. Strip ALL remaining HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)

    # 7. Final unescape pass (catches any remaining entities after step 6)
    text = html.unescape(text)

    # 8. Normalize whitespace
    #    - Replace \r with nothing
    text = text.replace('\r', '')
    #    - Collapse multiple spaces on a single line
    lines = text.split('\n')
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in lines]
    #    - Collapse 3+ consecutive blank lines -> 2 blank lines
    result_lines = []
    blank_run = 0
    for line in lines:
        if line == '':
            blank_run += 1
            if blank_run <= 2:
                result_lines.append('')
        else:
            blank_run = 0
            result_lines.append(line)

    text = '\n'.join(result_lines).strip()
    return text
