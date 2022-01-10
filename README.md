# IODict

iodict is a thread safe object store which is written in pure python.

The dictionary implementation follows the `Dict` API, but stores
items using their **birthtime** allowing users to treat this datastore as a
file system backed `OrderedDict`.

> Items in the object store use file system attributes, when available to
  store key and birthtime information. File system attributes enhance the
  capability of the object store; however, they're not required. In the
  event xattrs are not available, file stat is used for file creation time.
  While stat works, in many cases, item ordering is not guarenteed.

## Dictionary Usage

``` python
import iodict
data = iodict.IODict(path='/tmp/iodict')  # Could be any path on the file system
data["key"] = "value"
data
{'key': "value"}

dir(data)
['__class__',
 '__delattr__',
 '__delitem__',
 '__dict__',
 '__dir__',
 '__doc__',
 '__enter__',
 '__eq__',
 '__exit__',
 '__format__',
 '__ge__',
 '__getattribute__',
 '__getitem__',
 '__gt__',
 '__hash__',
 '__init__',
 '__init_subclass__',
 '__iter__',
 '__le__',
 '__len__',
 '__lt__',
 '__module__',
 '__ne__',
 '__new__',
 '__reduce__',
 '__reduce_ex__',
 '__repr__',
 '__setattr__',
 '__setitem__',
 '__sizeof__',
 '__str__',
 '__subclasshook__',
 '__weakref__',
 '_db_path',
 '_encoder',
 '_lock',
 'clear',
 'copy',
 'fromkeys',
 'get',
 'items',
 'keys',
 'pop',
 'popitem',
 'setdefault',
 'update',
 'values']
```

When running in a multiprocessing / threading application, a lock is required
to be passed into the iodict class.

``` python
import threading

import iodict
data = iodict.IODict(path='/tmp/iodict', lock=threading.Lock)
```

> By default, if no lock is provided, a multiprocessing lock will be created.

The lock object allows the `iodict` to respect the locking paradigm of the
executing application.

## Durable Queue Usage

The DurableQueue class is used to create a disk-backed queue which implements
the standarad `queue.Queue` API.

``` python
import iodict
q = iodict.DurableQueue(path='/tmp/iodict')  # Could be any path on the file system
q.put("test")
data = q.get()
data
'test'
```

## Flushing Capable Queue Usage

The FlushQueue class is used to extend the capabilities of a standard queue
object by providing an extension which can be used to flush the objects within
queue to a disk. This is useful in situation when the application needs to halt
or otherwise stop working, but the inflight processes need to be saved and
resumed at a later time.

``` python
import queue

import iodict


class NewQueue(queue.Queue, iodict.FlushQueue):
    def __init__(self, path, lock=None, semaphore=None):
        super().__init__()
        self.path = path
        self.lock = lock
        self.semaphore = semaphore


q = NewQueue(path='/tmp/iodict')  # Could be any path on the file system
q.put("test")
q.qsize()
1
q.flush()
q.qsize()
0
q.ingest()
q.qsize()
1
q.get()
'test'
```
