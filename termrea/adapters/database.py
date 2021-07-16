import config
import os
import sqlite3


class DatabaseAdapter():
    connection = None

    def get_connection(self):
        if not self.connection:
            self.connection = sqlite3.connect(os.path.expanduser(config.DB_PATH))
            self.connection.row_factory = sqlite3.Row

        return self.connection

    def find_unread_news(self):
        connection = self.get_connection()
        cursor = connection.cursor()

        return cursor.execute('''
            SELECT datetime(date, 'unixepoch') AS date,
            i.node_id AS source_id,
            n.title AS source,
            i.item_id,
            i.title,
            i.source AS url,
            i.read
            FROM items AS i
            INNER JOIN node AS n ON n.node_id = i.node_id
            AND i.read = 0
            AND i.parent_item_id = 0
            ORDER BY date ASC
        ''')


    def get_unread_count(self):
        connection = self.get_connection()
        cursor = connection.cursor()

        return cursor.execute('''
            SELECT COUNT(*) AS unread_count
            FROM items AS i
            WHERE i.read = 0
        ''')


    def get_source_unread_count(self, node_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        return cursor.execute('''
            SELECT COUNT(*) AS unread_count
            FROM items AS i
            INNER JOIN node AS n
            ON i.node_id = n.node_id
            AND i.read = 0
            AND (
                n.node_id = ?
                OR n.parent_id = ?
            )
        ''', (node_id, node_id))

    def get_source_items(self, node_id=None, unread_only=False, date_order='DESC'):
        connection = self.get_connection()
        cursor = connection.cursor()

        unread_condition = ''
        if unread_only:
            unread_condition = 'AND i.read = 0'

        query = '''
            SELECT datetime(date, 'unixepoch') AS date,
            i.node_id AS source_id,
            n.title AS source,
            i.item_id,
            IFNULL(i.title, '') AS title,
            i.source AS url,
            i.read
            FROM items AS i
            INNER JOIN node AS n ON i.node_id = n.node_id
            AND (
                n.node_id = ?
                OR n.parent_id = ?
            )
            %s
            ORDER BY date %s
        ''' % (unread_condition, date_order)

        return cursor.execute(query, (node_id, node_id))

    def get_source_all_items(self, node_id):
        return self.get_source_items(node_id=node_id, unread_only=False, date_order='DESC')

    def get_source_unread_items(self, node_id):
        return self.get_source_items(node_id=node_id, unread_only=True, date_order='ASC')

    def get_source_items(self, node_id, unread_source_id, selected_filter):
        if node_id and node_id != unread_source_id:
            if selected_filter == 'unread':
                rows = self.get_source_unread_items(node_id).fetchall()
            else:
                rows = self.get_source_all_items(node_id).fetchall()
        else:
            rows = self.find_unread_news().fetchall()

        self.close_connection()

        return rows

    def get_unreads_source(self):
        connection = self.get_connection()
        cursor = connection.cursor()

        return cursor.execute('''
            SELECT node_id
            FROM node
            WHERE title = 'Unread'
            AND type = 'vfolder'
        ''')

    def toggle_read_status(self, item_id, read_status):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute('UPDATE items SET read = ? WHERE item_id = ?', (read_status, item_id))
        connection.commit()
        self.close_connection()

    def set_item_read(self, item_id):
        self.toggle_read_status(item_id, 1)

    def set_item_unread(self, item_id):
        self.toggle_read_status(item_id, 0)

    def set_source_read(self, source_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE items
            SET read = 1
            WHERE item_id IN (
                SELECT i.item_id
                FROM items AS i
                INNER JOIN node AS n ON i.node_id = n.node_id
                AND (
                    n.node_id = ?
                    OR n.parent_id = ?
                )
                AND i.read = 0
            )
        ''', (source_id, source_id))
        connection.commit()
        self.close_connection()

    def set_unreads_read(self):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute('UPDATE items SET read = 1 WHERE read = 0')
        connection.commit()
        self.close_connection()

    def get_source_subscriptions(self, node_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        return cursor.execute('''
            SELECT n.node_id,
            n.parent_id,
            n.title,
            n.type,
            s.source,
            s.update_interval
            FROM node n
            INNER JOIN subscription s ON n.node_id = s.node_id
            AND n.node_id = ?
        ''', (node_id,))

    def get_source(self, node_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        return cursor.execute('''
            SELECT n.node_id,
            n.parent_id,
            n.title,
            n.type
            FROM node n
            WHERE n.node_id = ?
        ''', (node_id,))

    def get_sources_by_parent(self, parent_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        return cursor.execute('''
            SELECT n.node_id,
            n.parent_id,
            n.title,
            n.type
            FROM node n
            WHERE n.parent_id = ?
        ''', (parent_id,))

    def update_source(self, node_id, name, feed_type, url, update_interval):
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute('''
            UPDATE node
            SET title = ?,
            type = ?
            WHERE node_id = ?
        ''', (name, feed_type, node_id))

        cursor.execute('''
            UPDATE subscription
            SET source = ?,
            orig_source = ?,
            update_interval = ?
            WHERE node_id = ?
        ''', (url, url, update_interval, node_id))

        connection.commit()
        self.close_connection()

    def add_source(self, node_id, parent_node_id, name, feed_type, url, update_interval):
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute('''
            INSERT INTO node
            (node_id, parent_id, title, type, expanded, view_mode, sort_column, sort_reversed)
            VALUES
            (?, ?, ?, ?, 0, 3, 'time', 1)
        ''', (node_id, parent_node_id, name, feed_type))

        cursor.execute('''
            INSERT INTO subscription
            (node_id, source, orig_source, filter_cmd, update_interval, default_interval, discontinued, available)
            VALUES
            (?, ?, ?, '', ?, -1, 0, 0)
        ''', (node_id, url, url, update_interval))

        connection.commit()
        self.close_connection()

    def delete_source(self, node_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute('DELETE FROM node WHERE node_id = ?', (node_id,))
        cursor.execute('DELETE FROM subscription WHERE node_id = ?', (node_id,))

        connection.commit()
        self.close_connection()

    def close_connection(self):
        self.get_connection().close()
        self.connection = None

