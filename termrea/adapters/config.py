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

    def update_source(self, node_id, name, url, update_interval, mark_as_read):
        tree = xml.parse(os.path.expanduser(config.CONFIG_PATH))
        root = tree.getroot()

        for outline in root.findall('./body/'):
            if outline.attrib['id'] == node_id:
                outline.set('title', name)
                outline.set('text', name)
                outline.set('xmlUrl', url)
                outline.set('htmlUrl', url)
                outline.set('updateInterval', update_interval)
                outline.set('markAsRead', str(mark_as_read).lower())
                break

            for source in outline.findall('./'):
                if source.attrib['type'] in ['rss', 'atom'] and source.attrib['id'] == node_id:
                    source.set('title', name)
                    source.set('text', name)
                    source.set('xmlUrl', url)
                    source.set('htmlUrl', url)
                    source.set('updateInterval', update_interval)
                    source.set('markAsRead', str(mark_as_read).lower())
                    break

        tree.write(os.path.expanduser(config.CONFIG_PATH), xml_declaration=True, encoding='utf-8')

    def delete_source(self, node_id):
        tree = xml.parse(os.path.expanduser(config.CONFIG_PATH))
        root = tree.getroot()

        for outline in root.findall('./body/'):
            if outline.attrib['id'] == node_id:
                root.remove(outline)
                break

            for source in outline.findall('./'):
                if source.attrib['type'] in ['rss', 'atom'] and source.attrib['id'] == node_id:
                    outline.remove(source)
                    break

        tree.write(os.path.expanduser(config.CONFIG_PATH), xml_declaration=True, encoding='utf-8')

