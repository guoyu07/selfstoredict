"""SelfStoreDict for Python.
Author: markus schulte <ms@dom.de>
The module provides a subclassed dictionary that saves itself to a JSON file or redis-key whenever changed or when used
within a context.
"""
import json
from os.path import getmtime
from datetime import datetime, timedelta
from pathlib import Path


def adapt(parent, elem=None):
    """
    called whenever a dict or list is added. needed in order to let SelfStoreDict know about changes happening to its
    childs.
    :param parent: the parent object of the to be constructed one. parent should always be off type SelfStorageDict and
    should always be the root object.
    :param elem: the element added to SelfStoreDict or it's childs
    :return: the elem, converted to a subclass of dict or list that notifies it's parent
    """
    if isinstance(elem, list):
        return ChildList(parent, elem)
    if isinstance(elem, dict):
        return ChildDict(parent, elem)
    return elem


class ChildList(list):
    """
    a subclass of list that notifies self.parent about any change to its members
    """

    def __init__(self, parent, li=None):
        super(ChildList, self).__init__()
        if li is None:
            li = list()
        self.parent = parent
        for v in li:
            self.append(v)
        if not li:
            self.parent.save()

    def append(self, v):
        v = adapt(self.parent, v)
        super(ChildList, self).append(v)
        self.parent.save()

    def extend(self, v):
        v = adapt(self.parent, v)
        super(ChildList, self).extend(v)
        self.parent.save()

    def insert(self, i, v):
        v = adapt(self.parent, v)
        super(ChildList, self).insert(i, v)
        self.parent.save()

    def remove(self, v):
        v = adapt(self.parent, v)
        super(ChildList, self).remove(v)
        self.parent.save()

    def pop(self, i=None):
        r = super(ChildList, self).pop(i)
        self.parent.save()
        return r

    def clear(self):
        super(ChildList, self).clear()
        self.parent.save()

    def __setitem__(self, k, v):
        v = adapt(self.parent, v)
        super(ChildList, self).__setitem__(k, v)
        self.parent.save()


class ChildDict(dict):
    """
    a subclass of dict that notifies self.parent about any change to its members
    """

    def __init__(self, parent, d=None):
        super(ChildDict, self).__init__()
        if d is None:
            d = dict()
        self.parent = parent
        for k, v in d.items():
            self[k] = v
        if d != {}:
            self.parent.save()

    def __setitem__(self, k, v):
        v = adapt(self.parent, v)
        super(ChildDict, self).__setitem__(k, v)
        self.parent.save()

    def __delitem__(self, k):
        super(ChildDict, self).__delitem__(k)
        self.parent.save()

    def setdefault(self, k, v=None):
        v = adapt(self.parent, v)
        v = super(ChildDict, self).setdefault(k, v)
        self.parent.save()
        return v

    def clear(self):
        super(ChildDict, self).clear()
        self.parent.save()


class FileContainer(object):
    def __init__(self, path):
        self.path = path

    def save(self, data):
        with open(self.path, "w") as fp:
            json.dump(data.copy(), fp)

    def load(self):
        try:
            with open(self.path) as fp:
                for k, v in json.load(fp).items():
                    yield [k, v]
        except FileNotFoundError:
            raise FileNotFoundError

    def touch(self):
        Path(self.path).touch()

    @property
    def modified(self):
        return int(getmtime(self.path))


class RedisContainer(object):
    def __init__(self, key, redis):
        self.key = key
        self.redis = redis
        self.f = 9223370527000000

    def save(self, data):
        self.redis.set(self.key, json.dumps(data.copy()))
        self.redis.expire(self.key, self.f)

    def load(self):
        data = self.redis.get(self.key)
        try:
            jdata = json.loads(data)
        except TypeError:
            return
        try:
            for k, v in jdata.items():
                yield [k, v]
        except FileNotFoundError:
            raise FileNotFoundError

    def touch(self):
        self.redis.expire(self.key, self.f)

    @property
    def modified(self):
        ttl = self.redis.ttl(self.key)
        if ttl is None:
            return
        delta = timedelta(seconds=self.f - ttl)
        return int((datetime.now() - delta).timestamp())


class SelfStoreDict(ChildDict):
    """
    This class acts like a dict but constructs all attributes from JSON. please note: it is a subclass of 'ChildDict'
    but always the parent.
    call the constructor with a path or a redis connection
    you may add an optional initial value as a dict
    """

    def __init__(self, path, data=None, redis=None):
        self._saves_ = 0
        self._context_ = False
        self._inactive_ = True
        self.parent = self
        # check if there is a redis object
        if redis is not None:
            self.sc = RedisContainer(path, redis=redis)
        else:
            self.sc = FileContainer(path)
        self._path_ = path
        super(SelfStoreDict, self).__init__(self, data)
        if data is not None:
            self._inactive_ = False
            self.save()
        else:
            self._load()
        self._inactive_ = False

    def _inc_saves(self):
        self._saves_ += 1

    def _savenow(self):
        if self._inactive_:
            return False
        if self._context_:
            return False
        return True

    def save(self):
        if self._savenow():
            self.sc.save(self.copy())
            self._inc_saves()
            return

    @property
    def saves(self):
        return self._saves_

    @property
    def modified(self):
        return self.sc.modified

    def touch(self):
        self.sc.touch()

    def __enter__(self):
        self._context_ = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._context_ = False
        self._inactive_ = False
        self.save()

    def _load(self):
        """
        called by '@path.setter' to load dict.
        :return: None
        """
        try:
            for k, v in self.sc.load():
                self[k] = v
        except FileNotFoundError:
            pass
