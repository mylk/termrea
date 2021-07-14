import random
import string
import urllib.request
import xml.etree.ElementTree as xml

from adapters.database import DatabaseAdapter


def generate_node_id():
    db = DatabaseAdapter()

    node = ''
    while node is not None:
        new_node_id = ''.join(random.choices(string.ascii_lowercase, k=7))
        node = db.get_source(new_node_id).fetchone()

    db.close_connection()

    return new_node_id


def detect_feed_type(url):
    data = urllib.request.urlopen(url).read()
    root = xml.fromstring(data)

    source_type = 'atom'
    if root.tag == 'rss':
        source_type = 'rss'

    return source_type


def get_link(url, feed_type):
    data = urllib.request.urlopen(url).read()
    root = xml.fromstring(data)

    if feed_type == 'rss':
        link = root.find('./channel/link')

        return link.text
    elif feed_type == 'atom':
        links = root.findall('{http://www.w3.org/2005/Atom}link')
        for link in links:
            if not 'rel' in link.attrib or link.attrib['rel'] != 'self':
                return link.attrib['href']

    return None

