import unittest
#from pymaprdb import Connection, Table, Batch
from spam import _connection, _table

# TODO lol I reimported _connection and _table once and it resulted in a segmentation fault?

CLDBS = "hdnprd-c01-r03-01:7222,hdnprd-c01-r04-01:7222,hdnprd-c01-r05-01:7222"

TABLE_NAME = '/app/SubscriptionBillingPlatform/testpymaprdb'


class TestCConnection(unittest.TestCase):
    def test_bad_cldbs(self):
        connection = _connection('abc')
        self.assertFalse(connection.is_open())
        self.assertRaises(ValueError, connection.open)
        self.assertFalse(connection.is_open())
        connection.close()

    def test_good_cldbs(self):
        connection = _connection(CLDBS)
        self.assertFalse(connection.is_open())
        connection.open()
        self.assertTrue(connection.is_open())
        connection.close()
        self.assertFalse(connection.is_open())
        connection.close()


class TestCConnectionManageTable(unittest.TestCase):
    def setUp(self):
        connection = _connection(CLDBS)
        try:
            connection.delete_table(TABLE_NAME)
        except ValueError:
            pass
        connection.close()

    def tearDown(self):
        connection = _connection(CLDBS)
        try:
            connection.delete_table(TABLE_NAME)
        except ValueError:
            pass
        connection.close()

    def test_good(self):
        connection = _connection(CLDBS)
        connection.create_table(TABLE_NAME, {'f': {}})
        connection.delete_table(TABLE_NAME)

    def test_already_created(self):
        connection = _connection(CLDBS)
        connection.create_table(TABLE_NAME, {'f': {}})
        self.assertRaises(ValueError, connection.create_table, TABLE_NAME, {'f': {}})
        connection.delete_table(TABLE_NAME)

    def test_already_deleted(self):
        connection = _connection(CLDBS)
        connection.create_table(TABLE_NAME, {'f': {}})
        connection.delete_table(TABLE_NAME)
        self.assertRaises(ValueError, connection.delete_table, TABLE_NAME)

    def test_large_qualifier(self):
        connection = _connection(CLDBS)
        connection.create_table(TABLE_NAME, {''.join(['a' for _ in range(1000)]): {}})
        connection.delete_table(TABLE_NAME)

    def test_too_large_qualifier(self):
        connection = _connection(CLDBS)
        self.assertRaises(ValueError, connection.create_table, TABLE_NAME, {''.join(['a' for _ in range(10000)]): {}})
        # Verify that table was not fake-created mapr bug
        self.assertRaises(ValueError, connection.delete_table, TABLE_NAME)

    def test_really_big_table_name(self):
        ## I think MapR C API seg faults with a tablename > 10000
        connection = _connection(CLDBS)
        self.assertRaises(ValueError, connection.create_table, TABLE_NAME + ''.join(['a' for _ in range(10000)]), {'f': {}})
        self.assertRaises(ValueError, connection.delete_table, TABLE_NAME + ''.join(['a' for _ in range(10000)]))

    def test_pretty_big_table_name(self):
        ## I think MapR C API does not seg faults with a tablename ~ 1000
        connection = _connection(CLDBS)
        self.assertRaises(ValueError, connection.create_table, TABLE_NAME + ''.join(['a' for _ in range(1000)]), {'f': {}})
        self.assertRaises(ValueError, connection.delete_table, TABLE_NAME + ''.join(['a' for _ in range(1000)]))

    def test_delete_really_big_table_name(self):
        connection = _connection(CLDBS)
        self.assertRaises(ValueError, connection.delete_table, TABLE_NAME + ''.join(['a' for _ in range(10000)]))

    def test_delete_pretty_big_table_name(self):
        connection = _connection(CLDBS)
        self.assertRaises(ValueError, connection.delete_table, TABLE_NAME + ''.join(['a' for _ in range(1000)]))

    def test_max_versions_happy(self):
        connection = _connection(CLDBS)
        connection.create_table(TABLE_NAME, {'f': {
            'max_versions': 1,
            'min_versions': 1,
            'time_to_live': 0,
            'in_memory': 0,
        }})
        connection.delete_table(TABLE_NAME)


    def test_max_version_bad(self):
        connection = _connection(CLDBS)
        self.assertRaises(ValueError, connection.create_table, TABLE_NAME, {'f': {'max_versions': 'foo',}})
        self.assertRaises(ValueError, connection.delete_table, TABLE_NAME)
        self.assertRaises(ValueError, connection.create_table, TABLE_NAME, {'f': {'max_versions': 10000000000000000000}})
        self.assertRaises(ValueError, connection.create_table, TABLE_NAME, {'f': 'not a dict'})

    def test_invalid_key(self):
        connection = _connection(CLDBS)
        self.assertRaises(ValueError, connection.create_table, TABLE_NAME, {'f': {'foo': 'foo'}})

    def test_accept_unicode(self):
        connection = _connection(CLDBS)
        connection.create_table(TABLE_NAME, {u'f': {u'max_versions': 1}})







class TestCTableInit(unittest.TestCase):
    def setUp(self):
        self.connection = _connection(CLDBS)
        self.connection.create_table(TABLE_NAME, {'f': {}})

    def tearDown(self):
        try:
            self.connection.delete_table(TABLE_NAME)
        except ValueError:
            pass
        self.connection.close()

    def test_bad_table(self):
        self.connection.open()
        self.connection.delete_table(TABLE_NAME)
        self.assertRaises(ValueError, _table, self.connection, TABLE_NAME)
        self.connection.close()  # This segfaulted if I set self->connection before raising the exception for some reason

    def test_unopened_connection(self):
        self.connection = _connection(CLDBS)
        table = _table(self.connection, TABLE_NAME)
        self.connection.close()



class TestCTableRow(unittest.TestCase):
    def setUp(self):
        self.connection = _connection(CLDBS)
        self.connection.create_table(TABLE_NAME, {'f': {}})
        self.table = _table(self.connection, TABLE_NAME)
        self.table.put("foo", {"f:bar": "baz"})

    def tearDown(self):
        try:
            self.connection.delete_table(TABLE_NAME)
        except ValueError:
            pass
        self.connection.close()

    def test_happy(self):
        row = self.table.row('foo')
        self.assertEquals(row, {'f:bar': "baz"})

    def test_read_only_table_name(self):
        self.assertRaises(TypeError, setattr, self.table, 'table_name', 'foo')


class TestCTablePut(unittest.TestCase):
    def setUp(self):
        self.connection = _connection(CLDBS)
        self.connection.create_table(TABLE_NAME, {'f': {}})
        self.table = _table(self.connection, TABLE_NAME)

    def tearDown(self):
        self.connection.delete_table(TABLE_NAME)
        self.connection.close()

    def test_happy(self):
        self.table.put("foo", {"f:bar": "baz"})
        row = self.table.row('foo')
        for _ in range(10):
            # Loop to check for buffer overflow error
            self.assertEquals(row, {'f:bar': "baz"})

    def test_empty_put(self):
        self.assertRaises(ValueError, self.table.put, 'foo', {})

    def test_bad_column_family_no_colon(self):
        """All keys in the put dict must contain a colon separating the family from the qualifier"""
        self.assertRaises(ValueError, self.table.put, 'foo', {'bar': 'baz'})

    def test_bad_colon_no_family(self):
        self.assertRaises(ValueError, self.table.put, 'foo', {":bar": "baz", 'invalid:foo': 'bar'})
        row = self.table.row('foo')
        self.assertEquals(row, {})

    def test_bad_colon_no_qualifier(self):
        # LOL Apparently this is totaly fine
        self.table.put('foo', {"f:": "baz"})
        row = self.table.row('foo')
        self.assertEquals(row, {"f:": "baz"})

    def test_invalid_column_family(self):
        self.assertRaises(ValueError, self.table.put, 'foo', {"f:bar": "baz", 'invalid:foo': 'bar'})
        row = self.table.row('foo')
        self.assertEquals(row, {})

    def test_set(self):
        self.assertRaises(TypeError, self.table.put, 'foo', {"f:bar", "baz"})
        row = self.table.row('foo')
        self.assertEquals(row, {})

    def test_empty_value(self):
        self.table.put("foo", {"f:bar": ""})
        row = self.table.row('foo')
        self.assertEquals(row, {'f:bar': ""})

    def test_unicode(self):
        self.table.put(u"foo", {u"f:bar": u"baz"})
        row = self.table.row('foo')
        self.assertEquals(row, {'f:bar': "baz"})

    def test_big_value(self):
        ## Greater than 1024
        self.table.put('foo', {'f:bar': ''.join(['a' for _ in range(10000)])})
        row = self.table.row('foo')
        self.assertEquals(row, {'f:bar': ''.join(['a' for _ in range(10000)])})

    def test_big_qualifier(self):
        ## Greater than 1024
        self.table.put('foo', {'f:' + ''.join(['a' for _ in range(10000)]): 'baz'})
        row = self.table.row('foo')
        self.assertEquals(row, {'f:' + ''.join(['a' for _ in range(10000)]): 'baz'})

    def test_big_row_key(self):
        ## Greater than 1024
        self.table.put(''.join(['a' for _ in range(10000)]), {'f:bar': 'baz'})
        row = self.table.row(''.join(['a' for _ in range(10000)]))
        self.assertEquals(row, {'f:bar': 'baz'})

    def test_big_column_family(self):
        self.connection.delete_table(TABLE_NAME)
        self.connection.create_table(TABLE_NAME, {''.join(['a' for _ in range(1000)]): {}})
        self.table.put('foo', {''.join(['a' for _ in range(1000)]) + ':bar': 'baz'})
        row = self.table.row('foo')
        self.assertEquals(row, {''.join(['a' for _ in range(1000)]) + ':bar': 'baz'})


class TestCTablePutSplit(unittest.TestCase):
    """Purpose of this is to test the C split function"""
    def setUp(self):
        self.connection = _connection(CLDBS)

    def tearDown(self):
        try:
            self.connection.delete_table(TABLE_NAME)
        except ValueError:
            pass
        self.connection.close()

    def test_first(self):
        self.connection.create_table(TABLE_NAME, {'f': {}})
        self.table = _table(self.connection, TABLE_NAME)
        self.table.put("a", {"f:{cq}".format(cq='f' * i): str(i) for i in range(100)})
        row = self.table.row("a")
        self.assertEquals(row, {"f:{cq}".format(cq='f' * i): str(i) for i in range(100)})

    def test_second(self):
        self.connection.create_table(TABLE_NAME, {'ff': {}})
        self.table = _table(self.connection, TABLE_NAME)
        self.table.put("a", {"ff:{cq}".format(cq='f' * i): str(i) for i in range(100)})
        row = self.table.row("a")
        self.assertEquals(row, {"ff:{cq}".format(cq='f' * i): str(i) for i in range(100)})

    def test_third(self):
        self.connection.create_table(TABLE_NAME, {'fff': {}})
        self.table = _table(self.connection, TABLE_NAME)
        self.table.put("a", {"fff:{cq}".format(cq='f' * i): str(i) for i in range(100)})
        row = self.table.row("a")
        self.assertEquals(row, {"fff:{cq}".format(cq='f' * i): str(i) for i in range(100)})



class TestCTableDelete(unittest.TestCase):
    def setUp(self):
        self.connection = _connection(CLDBS)
        self.connection.create_table(TABLE_NAME, {'f': {}})
        self.table = _table(self.connection, TABLE_NAME)

    def tearDown(self):
        self.connection.delete_table(TABLE_NAME)
        self.connection.close()

    def test_happy(self):
        self.table.put("foo", {"f:bar": "baz"})
        row = self.table.row('foo')
        self.assertEquals(row, {'f:bar': "baz"})
        self.table.delete('foo')
        row = self.table.row('foo')
        self.assertEquals(row, {})

    def test_empty_row_key(self):
        self.assertRaises(ValueError, self.table.delete, '')


class TestCTableScanHappy(unittest.TestCase):
    def setUp(self):
        self.connection = _connection(CLDBS)
        self.connection.create_table(TABLE_NAME, {'f': {}})
        self.table = _table(self.connection, TABLE_NAME)
        for i in range(1, 10):
            self.table.put("foo{i}".format(i=i), {"f:bar{i}".format(i=i): 'baz{i}'.format(i=i)})

        for i in range(1, 10):
            self.table.put("aaa{i}".format(i=i), {"f:aaa{i}".format(i=i): 'aaa{i}'.format(i=i)})

        for i in range(1, 10):
            self.table.put("zzz{i}".format(i=i), {"f:zzz{i}".format(i=i): 'zzz{i}'.format(i=i)})

    def tearDown(self):
        self.connection.delete_table(TABLE_NAME)
        self.connection.close()

    def test_happy(self):
        i = 0
        for row_key, obj in self.table.scan():
            i += 1
            if i <= 9:
                self.assertEquals(row_key, "aaa{i}".format(i=i))
                self.assertEquals(obj, {"f:aaa{i}".format(i=i): 'aaa{i}'.format(i=i)})
            elif i <= 18:
                self.assertEquals(row_key, "foo{i}".format(i= i - 9))
                self.assertEquals(obj, {"f:bar{i}".format(i=i-9): 'baz{i}'.format(i=i-9)})
            else:
                self.assertEquals(row_key, "zzz{i}".format(i=i-18))
                self.assertEquals(obj, {"f:zzz{i}".format(i=i-18): 'zzz{i}'.format(i=i-18)})


        self.assertEquals(i, 27)

    def test_happy_start(self):
        i = 0
        for row_key, obj in self.table.scan('zzz'):
            i += 1
            self.assertEquals(row_key, "zzz{i}".format(i=i))
            self.assertEquals(obj, {"f:zzz{i}".format(i=i): 'zzz{i}'.format(i=i)})


        self.assertEquals(i, 9)

    def test_happy_stop(self):
        i = 0
        for row_key, obj in self.table.scan('', 'aaa9~'):
            i += 1
            self.assertEquals(row_key, "aaa{i}".format(i=i))
            self.assertEquals(obj, {"f:aaa{i}".format(i=i): 'aaa{i}'.format(i=i)})


        self.assertEquals(i, 9)

    def test_happy_start_stop(self):
        i = 0
        for row_key, obj in self.table.scan('foo1', 'foo9~'):
            i += 1
            self.assertEquals(row_key, "foo{i}".format(i=i))
            self.assertEquals(obj, {"f:bar{i}".format(i=i): 'baz{i}'.format(i=i)})

        self.assertEquals(i, 9)

    def test_no_rows(self):
        i = 0
        for row_key, obj in self.table.scan('fake', 'fake~'):
            i += 1

        self.assertEquals(i, 0)



class TestCTableBatch(unittest.TestCase):
    def setUp(self):
        self.connection = _connection(CLDBS)
        self.connection.create_table(TABLE_NAME, {'f': {}})
        self.table = _table(self.connection, TABLE_NAME)

    def tearDown(self):
        self.connection.delete_table(TABLE_NAME)
        self.connection.close()

    def test_happy(self):
        self.table.batch([('put', 'foo{}'.format(i), {"f:bar{i}".format(i=i): 'baz{i}'.format(i=i)}) for i in range(1, 1001)])
        rows = sorted(self.table.scan(), key=lambda x: int(x[0][3:]))
        i = 1
        for row_key, obj in rows:
            self.assertEquals(row_key, "foo{i}".format(i=i))
            self.assertEquals(obj, {"f:bar{i}".format(i=i): 'baz{i}'.format(i=i)})
            i += 1

        self.assertEquals(i, 1001)

        self.table.batch([('delete', 'foo{}'.format(i)) for i in range(1, 1001)])

        i = 0
        for row_key, obj in self.table.scan():
            i += 1

        self.assertEquals(i, 0)

    def test_mixed_errors_put(self):
        actions = [
            ('put', 'a', {'f:foo': 'bar'}),
            ('put', 'b', {'f': 'bar'}),
            ('put', 'c', {'f:': 'bar'}), # This is legal
            ('put', 'd', {':foo': 'bar'}),
            ('put', 'e', {'invalid:foo': 'bar'}),
            ('put', 'f', 'invalid data type'),
            ('put', 'g', {'f:foo', 'bar'}),
            (1, 'h', {'f:foo': 'bar'}),
            ('put', 2, {'f:foo': 'bar'}),
            ('put', 'j', 3),
            'not a tuple',
            ('invalid', 'k', {'f:foo': 'bar'}),
            ('put', 'z', {'f:foo': 'bar'}),
        ]
        errors, results = self.table.batch(actions)
        self.assertEquals(errors, len(actions) - 3)
        # TODO scan for the good rows
        i = 0
        for row_key, obj in self.table.scan():
            print row_key, obj
            i += 1

        self.assertEquals(i, 3)


    def test_mixed_errors_delete(self):
        raise NotImplementedError

    def test_empty_actions(self):
        errors, results = self.table.batch([])
        self.assertEquals(errors, 0)


if __name__ == '__main__':
    unittest.main()

"""

import spam
connection = spam._connection("hdnprd-c01-r03-01:7222,hdnprd-c01-r04-01:7222,hdnprd-c01-r05-01:7222")
connection.open()

table = spam._table(connection, '/app/SubscriptionBillingPlatform/testInteractive')
table.batch([('put', 'hello{}'.format(i), {'Name:bar':'bar{}'.format(i)}) for i in range(100000)])
#table.scan()

table.put('foo', {'f:bar': ''.join(['a' for _ in range(10000)])})

import spam
connection = spam._connection("hdnprd-c01-r03-01:7222,hdnprd-c01-r04-01:7222,hdnprd-c01-r05-01:7222")
connection.open()

table = spam._table(connection, '/app/SubscriptionBillingPlatform/testInteractive')
table.batch([('delete', 'hello{}'.format(i), {'Name:bar':'bar{}'.format(i)}) for i in range(100000)])


from spam import _connection, _table

# TODO lol I reimported _connection and _table once and it resulted in a segmentation fault?

CLDBS = "hdnprd-c01-r03-01:7222,hdnprd-c01-r04-01:7222,hdnprd-c01-r05-01:7222"

TABLE_NAME = '/app/SubscriptionBillingPlatform/testpymaprdb'

connection = _connection(CLDBS)
connection.create_table(TABLE_NAME, {'f': {}})
table = _table(connection, TABLE_NAME)
table.put("foo", {"f:bar", "baz"})

def tearDown(self):
try:
    connection.delete_table(TABLE_NAME)
except ValueError:
    pass
self.connection.close()

def test_happy(self):
row = table.row('foo')
self.assertEquals(row, {'f:bar': "baz"})

# TODO Add test for empty put body
"""


"""
from spam import _connection, _table
CLDBS = "hdnprd-c01-r03-01:7222,hdnprd-c01-r04-01:7222,hdnprd-c01-r05-01:7222"
TABLE_NAME = '/app/SubscriptionBillingPlatform/testpymaprdb'
connection = _connection(CLDBS)
connection.delete_table(TABLE_NAME)
connection.create_table(TABLE_NAME, {'f': {}})
table = _table(connection, TABLE_NAME)
table.batch([('put', 'hello{}'.format(i), {'f:bar':'bar{}'.format(i)}) for i in range(100000)])
table.put("test", {"f:foo": "bar"})
table.row('test')
table.delete('test')
table.row('test')

"""

"""
from spam import _connection, _table
CLDBS = "hdnprd-c01-r03-01:7222,hdnprd-c01-r04-01:7222,hdnprd-c01-r05-01:7222"
TABLE_NAME = '/app/SubscriptionBillingPlatform/testpymaprdb'
connection = _connection(CLDBS)
connection.delete_table(TABLE_NAME)
connection.create_table(TABLE_NAME, {'f': {}})
table = _table(connection, TABLE_NAME)
for i in range(10):
    table.put("test{}".format(i), {"f:foo{}".format(i): "bar{}".format(i)})

for k, v in table.scan():
    print k, v

for k, v in table.scan('test3'):
    print k, v

for k, v in table.scan():
    print k, v


"""


"""
from datetime import datetime
from spam import _connection, _table
CLDBS = "hdnprd-c01-r03-01:7222,hdnprd-c01-r04-01:7222,hdnprd-c01-r05-01:7222"
TABLE_NAME = '/app/SubscriptionBillingPlatform/testpymaprdb'
connection = _connection(CLDBS)
connection.delete_table(TABLE_NAME)
connection.create_table(TABLE_NAME, {'f': {}})
table = _table(connection, TABLE_NAME)
s = datetime.now()
table.batch([('put', 'hello{}'.format(i), {'f:bar':'bar{}'.format(i)}) for i in range(1000000)], True)
e = datetime.now()
print e - s



from datetime import datetime
from spam import _connection, _table
CLDBS = "hdnprd-c01-r03-01:7222,hdnprd-c01-r04-01:7222,hdnprd-c01-r05-01:7222"
TABLE_NAME = '/app/SubscriptionBillingPlatform/testpymaprdb'
connection = _connection(CLDBS)
connection.delete_table(TABLE_NAME)
connection.create_table(TABLE_NAME, {'f': {}})
table = _table(connection, TABLE_NAME)
lol = [('put', 'hello{}'.format(i), {'f:bar':'bar{}'.format(i)}) for i in range(1000000)]
s = datetime.now()
table.batch(lol, True)
e = datetime.now()
print e - s


from datetime import datetime
from spam import _connection, _table
CLDBS = "hdnprd-c01-r03-01:7222,hdnprd-c01-r04-01:7222,hdnprd-c01-r05-01:7222"
TABLE_NAME = '/app/SubscriptionBillingPlatform/testpymaprdb'
connection = _connection(CLDBS)
connection.delete_table(TABLE_NAME)
connection.create_table(TABLE_NAME, {'f': {}})
table = _table(connection, TABLE_NAME)
lol = [('put', 'hello{}'.format(i), {'f:lolaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa{}'.format(o): "baraaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa{}".format(o) for o in range(i, i + 11)}) for i in range(100000)]

s = datetime.now()
table.batch(lol, True)
e = datetime.now()
print e - s




connection.delete_table(TABLE_NAME)
connection.create_table(TABLE_NAME, {'f': {}})
table = _table(connection, TABLE_NAME)
table.put("test", {"f:foo": "bar"})
"""



"""
from spam import _connection, _table
CLDBS = "hdnprd-c01-r03-01:7222,hdnprd-c01-r04-01:7222,hdnprd-c01-r05-01:7222"
TABLE_NAME = '/app/SubscriptionBillingPlatform/testpymaprdb'
connection = _connection(CLDBS)
#lol = {''.join(['a' for _ in range(5)]): {}}
connection.delete_table(TABLE_NAME)
connection.create_table(TABLE_NAME, {'f': {}})
table = _table(connection, TABLE_NAME)

actions = [
    ('put', 'a', {'f:foo': 'bar'}),
    ('put', 'c', {'f:': 'bar'}),
    ('put', 'b', {'f:foo': 'bar'}),
]
table.batch(actions)

# Odd, sometimes it segfaults, sometime count isn't updated and it hangs..

"""

"""
from spam import _connection, _table
CLDBS = "hdnprd-c01-r03-01:7222,hdnprd-c01-r04-01:7222,hdnprd-c01-r05-01:7222"
TABLE_NAME = '/app/SubscriptionBillingPlatform/testpymaprdb'
connection = _connection(CLDBS)
#lol = {''.join(['a' for _ in range(5)]): {}}
connection.delete_table(TABLE_NAME)
connection.create_table(TABLE_NAME, {''.join(['a' for _ in range(10000)]): {}})
connection.create_table(TABLE_NAME, {'aaaaa': {}})
#connection.create_table(TABLE_NAME, {'f': {}})

from spam import _connection, _table
CLDBS = "hdnprd-c01-r03-01:7222,hdnprd-c01-r04-01:7222,hdnprd-c01-r05-01:7222"
TABLE_NAME = '/app/SubscriptionBillingPlatform/testpymaprdb'
connection = _connection(CLDBS)
connection.delete_table(TABLE_NAME)
connection.create_table(TABLE_NAME, {'f': {'max_versions': 1}})

lol = TABLE_NAME + ''.join(['a' for _ in range(1000)])
connection.create_table(lol, {'f': {}})


table = _table(connection, TABLE_NAME)
//table.put('foo', {'f:bar': ''.join(['a' for _ in range(10000)])})

table.put(''.join(['a' for _ in range(10000)]), {'f:bar': 'baz'})

table.put('foo', {'f:bar': ''.join(['a' for _ in range(10000)])})

table.put('foo', {'f:' + ''.join(['a' for _ in range(10000)]): 'baz'})

connection.create_table(TABLE_NAME, {''.join(['a' for _ in range(1000)]): {}})


table.put('foo', {'f:' + ''.join(['a' for _ in range(10000)]): 'baz'})

for i in range(1, 10):
    table.put("foo{i}".format(i=i), {"f:bar{i}".format(i=i): 'baz{i}'.format(i=i)})

for i in range(1, 10):
    table.put("aaa{i}".format(i=i), {"f:aaa{i}".format(i=i): 'aaa{i}'.format(i=i)})

for i in range(1, 10):
    table.put("zzz{i}".format(i=i), {"f:zzz{i}".format(i=i): 'zzz{i}'.format(i=i)})

"""