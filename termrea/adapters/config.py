import config
import os
import xml.etree.ElementTree as xml


class ConfigAdapter():

    def get_sources(self):
        tree = xml.parse(os.path.expanduser(config.CONFIG_PATH))
        root = tree.getroot()

        sources = {}
        for outline in root.findall('./body/'):
            sources[outline.attrib['id']] = {
                'title': outline.attrib['title'],
                'sources': {}
            }

            for source in outline.findall('./'):
                if source.attrib['type'] in ['rss', 'atom']:
                    sources[outline.attrib['id']]['sources'][source.attrib['id']] = {
                        'title': source.attrib['title']
                    }

        return sources

