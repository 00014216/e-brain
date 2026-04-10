import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def scrape_url(url):
    try:
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
        }
        resp = requests.get(url, headers=headers, timeout=12)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.content, 'lxml')

        title = ''
        og_title = soup.find('meta', property='og:title')
        if og_title:
            title = og_title.get('content', '')
        if not title and soup.title:
            title = soup.title.string or ''

        author = ''
        for sel in [{'name': 'author'}, {'property': 'article:author'}, {'name': 'twitter:creator'}]:
            tag = soup.find('meta', sel)
            if tag:
                author = tag.get('content', '')
                break

        description = ''
        og_desc = soup.find('meta', property='og:description')
        if og_desc:
            description = og_desc.get('content', '')
        if not description:
            desc_tag = soup.find('meta', {'name': 'description'})
            if desc_tag:
                description = desc_tag.get('content', '')

        pub_date = ''
        for dt_sel in [{'property': 'article:published_time'}, {'name': 'pubdate'}, {'itemprop': 'datePublished'}]:
            dt_tag = soup.find('meta', dt_sel)
            if dt_tag:
                pub_date = dt_tag.get('content', '')
                break

        for unwanted in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form', 'noscript']):
            unwanted.decompose()

        main = soup.find('article') or soup.find('main') or soup.find(id='content') or soup.find('body')
        raw_text = main.get_text(separator='\n', strip=True) if main else ''

        lines = [l.strip() for l in raw_text.splitlines() if len(l.strip()) > 40]
        text_content = '\n'.join(lines)[:6000]

        domain = urlparse(url).netloc

        return {
            'success':     True,
            'title':       title.strip(),
            'author':      author.strip(),
            'description': description.strip(),
            'pub_date':    pub_date.strip(),
            'content':     text_content,
            'domain':      domain,
            'url':         url,
        }

    except Exception as e:
        return {
            'success':     False,
            'title':       url,
            'author':      '',
            'description': '',
            'pub_date':    '',
            'content':     '',
            'domain':      '',
            'url':         url,
            'error':       str(e),
        }
