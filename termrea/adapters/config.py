import config
import os
import xml.etree.ElementTree as xml


class ConfigAdapter():

    def get_sources(self):
        tree = xml.parse(os.path.expanduser(config.CONFIG_PATH))
        root = tree.getroot()

        sources = {}
        for outline in root.findall('./body/'):
            mark_as_read = outline.attrib['markAsRead'] if 'markAsRead' in outline.attrib else 'false'

            sources[outline.attrib['id']] = {
                'title': outline.attrib['title'],
                'mark_as_read': mark_as_read,
                'sources': {}
            }

            for source in outline.findall('./'):
                mark_as_read = source.attrib['markAsRead'] if 'markAsRead' in source.attrib else 'false'

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

    def add_source(self, sibling_node_id, node_id, name, feed_type, url, update_interval, mark_as_read):
        tree = xml.parse(os.path.expanduser(config.CONFIG_PATH))
        root = tree.getroot()

        broken = False
        position = 1
        body = root.findall('./body/')
        for outline in body:
            if broken:
                break

            if outline.attrib['id'] == sibling_node_id:
                item = xml.Element('outline')
                item.attrib['id'] = node_id
                item.attrib['title'] = name
                item.attrib['text'] = name
                item.attrib['description'] = name
                item.attrib['type'] = feed_type
                item.attrib['sortColumn'] = 'time'
                item.attrib['xmlUrl'] = url
                # @TODO: change this
                item.attrib['htmlUrl'] = url
                item.attrib['updateInterval'] = update_interval
                item.attrib['markAsRead'] = str(mark_as_read).lower()
                item.attrib['collapsed'] = 'true'
                outline.insert(position, item)
                break
            position += 1

            position = 1
            for source in outline.findall('./'):
                if source.attrib['type'] in ['rss', 'atom'] and source.attrib['id'] == sibling_node_id:
                    item = xml.Element('outline')
                    item.attrib['id'] = node_id
                    item.attrib['title'] = name
                    item.attrib['text'] = name
                    item.attrib['description'] = name
                    item.attrib['type'] = feed_type
                    item.attrib['sortColumn'] = 'time'
                    item.attrib['xmlUrl'] = url
                    # @TODO: change this
                    item.attrib['htmlUrl'] = url
                    item.attrib['updateInterval'] = update_interval
                    item.attrib['markAsRead'] = str(mark_as_read).lower()
                    item.attrib['collapsed'] = 'true'
                    outline.insert(position, item)
                    broken = True
                    break
                position += 1

        tree.write(os.path.expanduser(config.CONFIG_PATH), xml_declaration=True)

