#!/usr/bin/python

import unittest

from syncconfig import *

class ConfigTest(unittest.TestCase):

    def test_add_config(self):
        config_list = SyncConfigList()
        old_count = len(config_list.get_entries())
        new_config = SyncConfig("TestConfig")
        new_config.set_value("KeyA", "ValueA")
        new_config.set_value("KeyB", "ValueB")
        config_list.add_entry(new_config)
        self.assertEquals(len(config_list.get_entries()), old_count + 1)
        entry = config_list.get_entry("TestConfig")
        self.assertNotEquals(entry, None)
        self.assertEquals(entry.get_value("KeyA"), "ValueA")
        self.assertEquals(entry.get_value("KeyB"), "ValueB")
        config_list.save()

    def test_password(self):
        config_list_1 = SyncConfigList()
        entry_1 = config_list_1.get_entry("TestConfig")
        entry_1.set_password("geheim123")
        self.assertEquals(entry_1.check_password("geheim123"), True)
        self.assertEquals(entry_1.check_password("geheim000"), False)
        config_list_1.save()
        config_list_2 = SyncConfigList()
        entry_2 = config_list_2.get_entry("TestConfig")
        self.assertEquals(entry_2.check_password("geheim123"), True)
        self.assertEquals(entry_2.check_password("geheim000"), False)
 
if __name__ == "__main__":
    unittest.main()
