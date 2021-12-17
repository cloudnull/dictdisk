import os
import queue
import sys
import types


possible_topdir = os.path.normpath(
    os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        os.pardir,
        os.pardir,
    )
)

base_path = os.path.join(possible_topdir, "iodict", "__init__.py")
if os.path.exists(base_path):
    sys.path.insert(0, possible_topdir)


import iodict


_D = iodict.IODict(path="/tmp/test-iodict")
assert type(_D) == iodict.IODict

_D.clear()

_D["a"] = 1
assert _D.get("a") == 1

_D["b"] = 2
_D["c"] = 3

assert _D.__repr__() == str({"a": 1, "b": 2, "c": 3})

_D["d"] = {"a": 1, "b": 2, "c": 3}

assert type(_D["d"]) == dict
assert _D["d"]["a"] == 1


def x():
    print("worked")


_D["e"] = x

assert callable(_D["e"])

assert _D.copy() == _D

_D.fromkeys(["f", "g"])
assert _D["f"] == None
assert _D["g"] == None

_D.fromkeys(["h", "i"], "testing")
assert _D["h"] == "testing"
assert _D["i"] == "testing"

assert type(_D.items()) == types.GeneratorType
assert type(_D.keys()) == types.GeneratorType
assert type(_D.values()) == types.GeneratorType

item = _D.popitem()
assert item == 1

assert _D.setdefault("j") == None
assert _D.setdefault("k", "testing") == "testing"

_D.update({"a": "a", "l": "testing"})
assert _D["a"] == "a"
assert _D["l"] == "testing"

_D["m"] = (1, 2, 3)
assert type(_D["m"]) == tuple

_D["n"] = {1, 2, 3}
assert type(_D["n"]) == set

_D["o"] = [1, 2, 3]
assert type(_D["o"]) == list

_D["p"] = b"testing"
assert type(_D["p"]) == bytes

_D["q"] = "dedup"
_D["r"] = "dedup"
_D.pop("q")

assert _D["r"] == "dedup"

e = _D.pop("e")
e()

_D.clear()
assert len(os.listdir("/tmp/test-iodict")) == 0


_Q = iodict.DurableQueue(
    path="/tmp/test-iodict-queue"
)  # Could be any path on the file system
_Q.put("test")
assert _Q.qsize() == 1
assert _Q.get() == "test"
assert _Q.qsize() == 0
_Q.put_nowait("test1")
assert _Q.qsize() == 1
assert _Q.get_nowait() == "test1"
assert _Q.qsize() == 0
_Q.close()


class NewQueue(queue.Queue, iodict.FlushQueue):
    def __init__(self, path, lock=None, semaphore=None):
        super().__init__()
        self.path = path
        self.lock = lock
        self.semaphore = semaphore


q = NewQueue(
    path="/tmp/test-iodict-queue-flush"
)  # Could be any path on the file system
q.put("test")
assert q.qsize() == 1
q.flush()
assert q.qsize() == 0
q.ingest()
assert q.qsize() == 1
assert q.get() == "test"
