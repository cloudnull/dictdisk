#   Copyright Peznauts <kevin@peznauts.com>. All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
import pickle
import unittest

from unittest.mock import call
from unittest.mock import patch

import iodict


class MockItem:
    def __init__(self, path):
        self.path = path


class MockStat:
    def __init__(*args, **kwargs) -> None:
        pass

    @property
    def st_ctime(self) -> float:
        return 1.0


class TestIODict(unittest.TestCase):
    def setUp(self):
        self.patched_makedirs = patch("os.makedirs", autospec=True)
        self.mock_makedirs = self.patched_makedirs.start()
        self.patched_symlink = patch("os.symlink", autospec=True)
        self.mock_symlink = self.patched_symlink.start()

    def tearDown(self):
        self.patched_makedirs.stop()
        self.patched_symlink.stop()

    def test_base___exit__(self):
        e = iodict.BaseClass()
        exit_value = e.__exit__(None, None, None)
        self.assertTrue(exit_value)

    @patch("traceback.print_exception", autospec=True)
    def test_base___exit__error(self, mock_print_exception):
        e = iodict.BaseClass()
        exit_value = e.__exit__(Exception, Exception, None)
        self.assertFalse(exit_value)
        mock_print_exception.assert_called()

    def test_init_no_lock(self):
        import multiprocessing

        d = iodict.IODict(path="/not/a/path")
        self.mock_makedirs.assert_called_with("/not/a/path", exist_ok=True)
        assert isinstance(d._lock, multiprocessing.synchronize.Lock)

    def test_init_thread_lock(self):
        import threading
        import _thread

        d = iodict.IODict(path="/not/a/path", lock=threading.Lock())
        self.mock_makedirs.assert_called_with("/not/a/path", exist_ok=True)
        assert isinstance(d._lock, _thread.LockType)

    @patch("os.listxattr", autospec=True)
    def test_init_xattr(self, mock_listxattr):
        mock_listxattr.return_value = ["user.birthtime"]
        d = iodict.IODict(path="/not/a/path")
        mock_listxattr.assert_called()
        assert d._encoder == iodict._object_sha3_224

    @patch("os.listxattr", autospec=True)
    def test_init_no_xattr(self, mock_listxattr):
        mock_listxattr.side_effect = OSError("error")
        d = iodict.IODict(path="/not/a/path")
        assert d._encoder == str

    @patch("os.listxattr", autospec=True)
    @patch("os.unlink", autospec=True)
    def test__delitem___(self, mock_unlink, mock_listxattr):
        d = iodict.IODict(path="/not/a/path")
        d.__delitem__("not-an-item")
        mock_unlink.assert_called_with(
            "/not/a/path/29c4514efdb8379a19bae2c24d085d87ef0d0590d3c6c29b5b8b083a"
        )

    @patch("os.unlink", autospec=True)
    def test__delitem___no_xattr(self, mock_unlink):
        d = iodict.IODict(path="/not/a/path")
        d.__delitem__("not-an-item")
        mock_unlink.assert_called_with("/not/a/path/not-an-item")

    @patch("os.unlink", autospec=True)
    def test__delitem__missing(self, mock_unlink):
        mock_unlink.side_effect = FileNotFoundError
        d = iodict.IODict(path="/not/a/path")
        with self.assertRaises(KeyError):
            d.__delitem__("not-an-item")

    @patch("os.scandir", autospec=True)
    @patch("os.listxattr", autospec=True)
    def test__exit__(self, mock_listxattr, mock_scandir):
        with patch("builtins.open", unittest.mock.mock_open()):
            with patch.object(
                iodict.IODict, "clear", autospec=True
            ) as mock_clear:
                with iodict.IODict(path="/not/a/path") as d:
                    d["not-an-item"] = {"a": 1}

            self.assertFalse(d)
            mock_clear.assert_called()

    def test__getitem__(self):
        read_data = pickle.dumps({"a": 1})
        d = iodict.IODict(path="/not/a/path")
        with patch(
            "builtins.open", unittest.mock.mock_open(read_data=read_data)
        ):
            item = d.__getitem__("not-an-item")
        self.assertEqual(item, {"a": 1})

    def test__getitem__missing(self):
        d = iodict.IODict(path="/not/a/path")
        with patch("builtins.open", unittest.mock.mock_open()) as mock_f:
            mock_f.side_effect = FileNotFoundError
            with self.assertRaises(KeyError):
                d.__getitem__("not-an-item")

    @patch("os.scandir", autospec=True)
    @patch("os.path.exists", autospec=True)
    @patch("os.getcwd", autospec=True)
    @patch("os.chdir", autospec=True)
    def test__iter__(self, mock_chdir, mock_getcwd, mock_exists, mock_scandir):
        mock_getcwd.return_value = "/"
        mock_exists.return_value = True
        mock_scandir.return_value = [MockItem("file1"), MockItem("file2")]
        d = iodict.IODict(path="/not/a/path")
        with patch("os.getxattr") as mock_getxattr:
            mock_getxattr.side_effect = [
                b"key1",
                b"A\xd8kl\xc1\xb1\xd9]",
                b"key2",
                b"A\xd8kn\x0f}\xda\x16",
            ]
            return_items = [i for i in d.__iter__()]
            self.assertEqual(return_items, ["key1", "key2"])

    @patch("os.scandir", autospec=True)
    @patch("os.path.exists", autospec=True)
    @patch("os.getcwd", autospec=True)
    @patch("os.chdir", autospec=True)
    def test__iter__not_found(
        self, mock_chdir, mock_getcwd, mock_exists, mock_scandir
    ):
        mock_getcwd.return_value = "/"
        mock_exists.return_value = True
        mock_scandir.return_value = [MockItem("file1")]
        d = iodict.IODict(path="/not/a/path")
        with patch("os.getxattr") as mock_getxattr:
            mock_getxattr.side_effect = [
                b"key1",
                b"A\xd8kn\x0f}\xda\x16",
                FileNotFoundError,
            ]
            return_items = [i for i in d.__iter__()]
            self.assertEqual(return_items, ["key1"])

    @patch("os.stat", autospec=True)
    @patch("os.scandir", autospec=True)
    @patch("os.path.exists", autospec=True)
    @patch("os.getcwd", autospec=True)
    @patch("os.chdir", autospec=True)
    def test__iter__no_xattr(
        self,
        mock_chdir,
        mock_getcwd,
        mock_exists,
        mock_scandir,
        mock_stat,
    ):
        mock_getcwd.return_value = "/"
        mock_exists.return_value = True
        mock_scandir.return_value = [
            MockItem("key1"),
            MockItem("key2"),
        ]
        d = iodict.IODict(path="/not/a/path")
        with patch("os.getxattr") as mock_getxattr:
            mock_getxattr.side_effect = OSError
            mock_stat.return_value = MockStat()
            return_items = [i for i in d.__iter__()]
            self.assertEqual(return_items, ["key1", "key2"])

    @patch("os.scandir", autospec=True)
    @patch("os.path.exists", autospec=True)
    @patch("os.getcwd", autospec=True)
    @patch("os.chdir", autospec=True)
    def test__iter__index(
        self, mock_chdir, mock_getcwd, mock_exists, mock_scandir
    ):
        mock_getcwd.return_value = "/"
        mock_exists.return_value = True
        mock_scandir.return_value = [MockItem("file1"), MockItem("file2")]
        d = iodict.IODict(path="/not/a/path")
        with patch("os.getxattr") as mock_getxattr:
            mock_getxattr.side_effect = [
                b"key1",
                b"A\xd8kn\x0f}\xda\x16",
                b"key2",
                b"A\xd8kl\xc1\xb1\xd9]",
            ]
            self.assertEqual([i for i in d.__iter__(index=1)], ["key1"])

    @patch("os.scandir", autospec=True)
    @patch("os.path.exists", autospec=True)
    @patch("os.getcwd", autospec=True)
    @patch("os.chdir", autospec=True)
    def test__iter__no_items(
        self, mock_chdir, mock_getcwd, mock_exists, mock_scandir
    ):
        mock_getcwd.return_value = "/"
        mock_exists.return_value = True
        mock_scandir.return_value = []
        d = iodict.IODict(path="/not/a/path")
        self.assertEqual([i for i in d.__iter__()], [])

    @patch("os.scandir", autospec=True)
    def test__len__zero(self, mock_scandir):
        mock_scandir.return_value = []
        d = iodict.IODict(path="/not/a/path")
        self.assertEqual(len(d), 0)

    def test__len__(self):
        d = iodict.IODict(path="/not/a/path")
        with patch.object(d, "__iter__", autospec=True) as mock__iter__:
            mock__iter__.return_value = ["file1", "file2"]
            self.assertEqual(len(d), 2)

    @patch("os.setxattr", autospec=True)
    @patch("os.getxattr", autospec=True)
    @patch("os.listxattr", autospec=True)
    def test__setitem__(self, mock_listxattr, mock_getxattr, mock_setxattr):
        read_data = pickle.dumps({"a": 1})
        d = iodict.IODict(path="/not/a/path")
        with patch(
            "builtins.open", unittest.mock.mock_open(read_data=read_data)
        ):
            d.__setitem__("not-an-item", {"a": 1})
        mock_listxattr.assert_called_with("/not/a/path")
        mock_getxattr.assert_called_with(
            "/not/a/path/29c4514efdb8379a19bae2c24d085d87ef0d0590d3c6c29b5b8b083a",
            "user.birthtime",
        )
        mock_setxattr.assert_called_with(
            "/not/a/path/29c4514efdb8379a19bae2c24d085d87ef0d0590d3c6c29b5b8b083a",
            "user.key",
            b"not-an-item",
        )

    @patch("os.getxattr", autospec=True)
    def test__setitem__no_xattrs(self, mock_getxattr):
        mock_getxattr.side_effect = OSError
        read_data = pickle.dumps({"a": 1})
        d = iodict.IODict(path="/not/a/path")
        with patch(
            "builtins.open", unittest.mock.mock_open(read_data=read_data)
        ):
            d.__setitem__("not-an-item", {"a": 1})

    def test_clear(self):
        d = iodict.IODict(path="/not/a/path")
        with patch.object(d, "__iter__", autospec=True) as mock__iter__:
            mock__iter__.return_value = ["file1", "file2"]
            with patch.object(
                d, "__delitem__", autospec=True
            ) as mock__delitem__:
                d.clear()
                mock__delitem__.assert_has_calls(
                    [call("file1"), call("file2")]
                )

    def test_copy(self):
        d = iodict.IODict(path="/not/a/path")
        self.assertEqual(d.copy(), d)

    def test_get(self):
        d = iodict.IODict(path="/not/a/path")
        with patch.object(d, "__getitem__", autospec=True) as mock__getitem__:
            mock__getitem__.return_value = "value"
            self.assertEqual(d.get("file1"), "value")

    def test_get_default(self):
        d = iodict.IODict(path="/not/a/path")
        with patch.object(d, "__getitem__", autospec=True) as mock__getitem__:
            mock__getitem__.side_effect = KeyError
            self.assertEqual(d.get("file1", "default"), "default")

    @patch("os.path.exists", autospec=True)
    @patch("os.getxattr", autospec=True)
    def test__get_item_key(self, mock_getxattr, mock_exists):
        mock_getxattr.side_effect = [b"key1"]
        mock_exists.return_value = True
        keyname = iodict._get_item_key("/not/a/path")
        self.assertEqual(keyname, "key1")

    @patch("os.path.exists", autospec=True)
    @patch("os.getxattr", autospec=True)
    def test__get_item_key_unicode(self, mock_getxattr, mock_exists):
        mock_getxattr.side_effect = OSError
        mock_exists.return_value = True
        keyname = iodict._get_item_key("/not/a/gAR9lC4=")
        self.assertEqual(keyname, {})

    @patch("os.path.exists", autospec=True)
    @patch("os.getxattr", autospec=True)
    def test__get_item_key_unicode(self, mock_getxattr, mock_exists):
        mock_getxattr.side_effect = OSError
        mock_exists.return_value = False
        with self.assertRaises(FileNotFoundError):
            iodict._get_item_key("/not/a/gAR9lC4=")

    def test_fromkeys(self):
        d = iodict.IODict(path="/not/a/path")
        with patch.object(d, "__setitem__", autospec=True) as mock__setitem__:
            d.fromkeys(["file1", "file2"])
            mock__setitem__.assert_has_calls(
                [call("file1", None), call("file2", None)]
            )

    def test_fromkeys_default(self):
        d = iodict.IODict(path="/not/a/path")
        with patch.object(d, "__setitem__", autospec=True) as mock__setitem__:
            d.fromkeys(["file1", "file2"], "testing")
            mock__setitem__.assert_has_calls(
                [call("file1", "testing"), call("file2", "testing")]
            )

    def test_items(self):
        d = iodict.IODict(path="/not/a/path")
        with patch.object(d, "__iter__", autospec=True) as mock__iter__:
            mock__iter__.return_value = ["file1", "file2"]
            with patch.object(
                d, "__getitem__", autospec=True
            ) as mock__getitem__:
                mock__getitem__.side_effect = ["value1", "value2"]
                return_items = [i for i in d.items()]
        self.assertEqual(
            return_items, [("file1", "value1"), ("file2", "value2")]
        )

    def test_keys(self):
        d = iodict.IODict(path="/not/a/path")
        with patch.object(d, "__iter__", autospec=True) as mock__iter__:
            mock__iter__.return_value = ["file1", "file2"]
            return_items = [i for i in d.keys()]

        self.assertEqual(return_items, ["file1", "file2"])

    @patch("os.setxattr", autospec=True)
    def test__makedirs(self, mock_setxattr):
        iodict._makedirs("/not/a/path")
        self.mock_makedirs.assert_called_with("/not/a/path", exist_ok=True)

    @patch("os.setxattr", autospec=True)
    def test__makedirs_key(self, mock_setxattr):
        iodict._makedirs("/not/a/path", key="things")
        self.mock_makedirs.assert_called_with("/not/a/path", exist_ok=True)
        mock_setxattr.assert_called_with(
            "/not/a/path", "user.key", "things".encode()
        )

    @patch("os.setxattr", autospec=True)
    @patch("os.unlink", autospec=True)
    def test__makedirs_file_exists(self, mock_unlink, mock_setxattr):
        self.mock_makedirs.side_effect = [FileExistsError, True]
        iodict._makedirs("/not/a/path", key="things")
        self.mock_makedirs.assert_called_with("/not/a/path", exist_ok=True)
        mock_setxattr.assert_called_with(
            "/not/a/path", "user.key", "things".encode()
        )
        mock_unlink.assert_called_with("/not/a/path")

    def test__object_sha3_224(self):
        sha3_224 = iodict._object_sha3_224(obj={"test": "value"})
        self.assertEqual(
            sha3_224,
            "72b84f14a5cc4a53bf9af53b95043617388629bf733f8b48d6fefe47",  # noqa
        )

    def test__object_sha3_224_encoding(self):
        sha3_224 = iodict._object_sha3_224(obj="string")
        self.assertEqual(
            sha3_224,
            "1f75b776042429f25dc7f131097188a8c98c18e6a3016aa6680bd4c8",  # noqa
        )

    def test_pop(self):
        d = iodict.IODict(path="/not/a/path")
        with patch.object(d, "__getitem__", autospec=True) as mock__getitem__:
            mock__getitem__.return_value = "value"
            with patch.object(
                d, "__delitem__", autospec=True
            ) as mock__delitem__:
                self.assertEqual(d.pop("file1"), "value")
                mock__delitem__.assert_called_with("file1")

    def test_pop_default(self):
        d = iodict.IODict(path="/not/a/path")
        with patch.object(d, "__getitem__", autospec=True) as mock__getitem__:
            mock__getitem__.side_effect = KeyError
            with patch.object(
                d, "__delitem__", autospec=True
            ) as mock__delitem__:
                self.assertEqual(d.pop("file1", "default1"), "default1")
                mock__delitem__.assert_called_with("file1")

    def test_pop_no_default_keyerror(self):
        d = iodict.IODict(path="/not/a/path")
        with patch.object(d, "__getitem__", autospec=True) as mock__getitem__:
            mock__getitem__.side_effect = KeyError
            with patch.object(
                d, "__delitem__", autospec=True
            ) as mock__delitem__:
                with self.assertRaises(KeyError):
                    d.pop("file1")
                mock__delitem__.assert_called_with("file1")

    def test_popitem(self):
        d = iodict.IODict(path="/not/a/path")
        with patch.object(d, "__getitem__", autospec=True):
            with patch.object(d, "__delitem__", autospec=True):
                with patch.object(
                    d, "__iter__", autospec=True
                ) as mock__iter__:
                    mock__iter__.return_value = iter(["file1", "file2"])
                    with patch.object(d, "pop", autospec=True) as mock_pop:
                        mock_pop.side_effect = ["value1", "value2"]
                        item_value = d.popitem()

        self.assertEqual(item_value, "value1")

    def test_popitem(self):
        d = iodict.IODict(path="/not/a/path")
        with patch.object(d, "__getitem__", autospec=True):
            with patch.object(d, "__delitem__", autospec=True):
                with patch.object(
                    d, "__iter__", autospec=True
                ) as mock__iter__:
                    mock__iter__.return_value = iter(["file1", "file2"])
                    with patch.object(d, "pop", autospec=True) as mock_pop:
                        mock_pop.side_effect = StopIteration
                        with self.assertRaises(KeyError):
                            d.popitem()

    @patch("os.scandir", autospec=True)
    def test_repr(self, mock_scandir):
        d = iodict.IODict(path="/not/a/path")
        self.assertEqual(d.__repr__(), "{}")

    def test_setdefault(self):
        read_data = pickle.dumps("")
        d = iodict.IODict(path="/not/a/path")
        with patch(
            "builtins.open", unittest.mock.mock_open(read_data=read_data)
        ):
            item = d.setdefault("not-an-item")

        self.assertEqual(item, None)

    def test_setdefault_default(self):
        read_data = pickle.dumps({"a": 1})
        d = iodict.IODict(path="/not/a/path")
        with patch(
            "builtins.open", unittest.mock.mock_open(read_data=read_data)
        ):
            item = d.setdefault("not-an-item", {"a": 1})

        self.assertEqual(item, {"a": 1})

    def test_update(self):
        mapping = {"a": 1, "b": 2, "c": 3}
        d = iodict.IODict(path="/not/a/path")
        with patch.object(d, "__setitem__", autospec=True) as mock__setitem__:
            d.update(mapping)
        mock__setitem__.assert_has_calls(
            [call("a", 1), call("b", 2), call("c", 3)]
        )

    def test_values(self):
        d = iodict.IODict(path="/not/a/path")
        with patch.object(d, "__iter__", autospec=True) as mock__iter__:
            mock__iter__.return_value = ["file1", "file2"]
            with patch.object(
                d, "__getitem__", autospec=True
            ) as mock__getitem__:
                mock__getitem__.side_effect = ["value1", "value2"]
                return_items = [i for i in d.values()]

        self.assertEqual(return_items, ["value1", "value2"])
