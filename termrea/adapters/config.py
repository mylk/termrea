import config
import os
import xml.etree.ElementTree as xml


class ConfigAdapter():

    def get_sources(self):
        tree = xml.parse(os.path.expanduser(config.CONFIG_PATH))
        root = tree.getroot()

        sources = {}
        for outline in root.findall('./body/'):
            mark_as_read = outline.attrib['markAsRead'] if 'markAsRead' in outline.attrib else False

            sources[outline.attrib['id']] = {
                'title': outline.attrib['title'],
                'mark_as_read': mark_as_read,
                'sources': {}
            }

            for source in outline.findall('./'):
                mark_as_read = source.attrib['markAsRead'] if 'markAsRead' in source.attrib else False

                if source.attrib['type'] in ['rss', 'atom']:
                    sources[outline.attrib['id']]['sources'][source.attrib['id']] = {
                        'title': source.attrib['title'],
                        'mark_as_read': mark_as_read
                    }

        return sources

    def get_source(self, node_id):
        sources = self.get_sources()

        for source in sources:
            if source == node_id:
                return sources[source]

            for subsource in sources[source]['sources']:
                if subsource == node_id:
                    return sources[source]['sources'][subsource]

        return None

