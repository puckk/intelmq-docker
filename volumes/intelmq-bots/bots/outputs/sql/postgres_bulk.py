
# -*- coding: utf-8 -*-
"""
SQL output bot.
See Readme.md for installation and configuration.
In case of errors, the bot tries to reconnect if the error is of operational
and thus temporary. We don't want to catch too much, like programming errors
(missing fields etc).
"""

from threading import Thread
import queue

from intelmq.lib.bot import SQLBot
import json

from intelmq import HARMONIZATION_CONF_FILE


class CustomSQLOutputBot(SQLBot):

    def init(self):
        super().init()
        self.table = self.parameters.table
        self.jsondict_as_string = getattr(self.parameters, 'jsondict_as_string', True)

        self.table_keys = self.parameters.table_keys
        self.drop_table = getattr(self.parameters, 'drop_table', False)
        self.batch_size = getattr(self.parameters, 'batch_size', 1000)

        self.logger.info(str(self.drop_table))
        self.logger.info(str(self.batch_size))
        self.logger.info(str(self.table_keys))

        self.create_table()

    def create_table(self):
        if self.drop_table:
            query = """DROP TABLE IF EXISTS {};""".format(self.table)
            if self.execute(query, [], rollback=True):
                self.con.commit()

        initdb = """CREATE TABLE IF NOT EXISTS {} (
        "id" BIGSERIAL UNIQUE PRIMARY KEY,""".format(self.table)
        for field, field_type in sorted(self.table_keys.items()):
            initdb += '\n    "{name}" {type},'.format(name=field, type=field_type)

        initdb = initdb[:-1]  # remove last ','
        initdb += "\n);\n"

        for field in sorted(self.table_keys.keys()):
            initdb += 'CREATE INDEX IF NOT EXISTS "idx_events_{0}" ON events USING btree ("{0}");\n'.format(field)

        if self.execute(initdb, [], rollback=True):
            self.con.commit()

    def flatten_json(self, y): 
        out = {} 
    
        def flatten(x, name =''): 
            if type(x) is dict: 
                for a in x: 
                    flatten(x[a], name + a + '.') 
            elif type(x) is list: 
                i = 0
                for a in x:                 
                    flatten(a, name + str(i) + '.') 
                    i += 1
            else: 
                out[name[:-1]] = x 
    
        flatten(y) 
        return out

    def create_query(self, to_upload):
        keys = '", "'.join(sorted(self.table_keys.keys()))
        all_values = []

        for tu in to_upload:
            event = json.loads(tu.to_json(hierarchical=True, jsondict_as_string=self.jsondict_as_string))
            # self.logger.info(str(event))
            to_save = self.flatten_json(event)
            values = ["'{}'".format(to_save[k]) if k in to_save else "" for k in sorted(self.table_keys.keys())]
            # fvalues = "({})".format(len(values) * '{0}, '.format(self.format_char)[:-2])
            # all_values.extend(values)
            all_values.append("({})".format(', '.join(values)))

        # fvalues = 
        query = ('INSERT INTO {table} ("{keys}") VALUES {values}'
                 ''.format(table=self.table, keys=keys, values=', '.join(all_values)))
        self.logger.info(query)
        self.logger.info(str(values))

        return query

    def uploader(self, q, batch_size):
        # self.logger.info('staring upload')
        to_upload = []
        while True:
            # self.logger.info('getting ')
            to_upload.append(q.get())
            # self.logger.info('appended, qsize = {}'.format(len(to_upload)))
            if len(to_upload) >= batch_size:
                # self.logger.info('uploading....')
                
                query = self.create_query(to_upload)
                if self.execute(query, [], rollback=True):
                    self.con.commit()

                to_upload = []
                # self.logger.info('uploaded!')


    def process(self):

        q = queue.Queue() 
        thr1 = Thread(target=self.uploader, args=(q, self.batch_size,))
        thr1.start()
 
        while True:
            # self.logger.info('pop from pipeline')
            event = self.receive_message()
            # self.logger.info(str(event))
            q.put(event)
            self.acknowledge_message()
            # self.logger.info('added to queue')


BOT = CustomSQLOutputBot