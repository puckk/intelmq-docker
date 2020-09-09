
# -*- coding: utf-8 -*-
"""
SQL output bot.
See Readme.md for installation and configuration.
In case of errors, the bot tries to reconnect if the error is of operational
and thus temporary. We don't want to catch too much, like programming errors
(missing fields etc).
"""

from intelmq.lib.bot import SQLBot
import json


class CustomSQLOutputBot(SQLBot):

    def init(self):
        super().init()
        self.table = self.parameters.table
        self.jsondict_as_string = getattr(self.parameters, 'jsondict_as_string', True)

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

    def process(self):
        keys_to_save = ['extra','time.observation']
        event = json.loads(self.receive_message().to_json(hierarchical=True, jsondict_as_string=self.jsondict_as_string))
        # self.logger.info(str(event))
        to_save = self.flatten_json(event)
        # self.logger.info(str(to_save))
        to_save = {key: value for key, value in to_save.items() if any(kts in key for kts in keys_to_save)}
        # self.logger.info(str(to_save))

        keys = '", "'.join(to_save.keys())
        values = list(to_save.values())
        fvalues = len(values) * '{0}, '.format(self.format_char)
        query = ('INSERT INTO {table} ("{keys}") VALUES ({values})'
                 ''.format(table=self.table, keys=keys, values=fvalues[:-2]))

        if self.execute(query, values, rollback=True):
            self.con.commit()
            self.acknowledge_message()


BOT = CustomSQLOutputBot