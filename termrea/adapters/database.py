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

    def get_node_unreads_count(self, node_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        return cursor.execute('''
            SELECT COUNT(*) AS unreads_count
            FROM items AS i
            INNER JOIN node AS n
            ON i.node_id = n.node_id
            AND i.read = 0
            AND (
                n.node_id = ?
                OR n.parent_id = ?
            )
        ''', (node_id, node_id))

    def get_node_items(self, node_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        return cursor.execute('''
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
            ORDER BY date DESC
        ''', (node_id, node_id))

    def get_unreads_node(self):
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

    def toggle_source_read_status(self, source_id, read_status):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE items
            SET read = ?
            WHERE item_id IN (
                SELECT i.item_id
                FROM items AS i
                INNER JOIN node AS n ON i.node_id = n.node_id
                AND (
                    n.node_id = ?
                    OR n.parent_id = ?
                )
                AND i.read = 0
            )''', (read_status, source_id, source_id))
        connection.commit()
        self.close_connection()

    def set_source_read(self, source_id):
        self.toggle_source_read_status(source_id, 1)

    def set_unreads_read(self):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute('UPDATE items SET read = 1 WHERE read = 0')
        connection.commit()
        self.close_connection()

    def close_connection(self):
        self.get_connection().close()

