"""SelfStoreDict for Python.
Author: markus schulte <ms@dom.de>
The module provides a subclassed dictionary that saves itself to a JSON file whenever changed or when used within a context
"""
import json


def adapt(parent, elem=None):
    """
    called whenever a dict or list is added. needed in order to  let SelfStoreDict know about changes happening to its childs.
    :param parent: the parent object of the to be constructed one. parent should always be off type SelfStorageDict and should always be the root object.
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
    def __init__(self, parent, l=None):
        super(ChildList, self).__init__()
        if l is None:
            l = list()
        self.parent = parent
        for v in l:
            self.append(v)
        if l != []:
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

    def get(self, k, v=None):
        v = adapt(self.parent, v)
        v = super(ChildDict, self).get(k, v)
        self.parent.save()
        return v

    def setdefault(self, k, v=None):
        v = adapt(self.parent, v)
        v = super(ChildDict, self).setdefault(k, v)
        self.parent.save()
        return v

    def clear(self):
        super(ChildDict, self).clear()
        self.parent.save()


class SelfStoreDict(ChildDict):
    """
    This class acts like a dict but constructs all attributes from JSON. please note: it is a subclass of 'ChildDict' but always the parent.
    call the constructor with a path.
    you may add an optional initial value as a dict
    """
    def __init__(self, path, d=None):
        self._saves_ = 0
        self._dirty_ = False
        self._context_ = False
        self._inactive_ = False
        self.parent = self
        self._truepath_ = ""
        self._path_ = path
        super(SelfStoreDict, self).__init__(self, d)

    def _inc_saves(self):
        self._saves_ += 1

    def _savenow(self):
        if self._inactive_:
            return False
        if self._context_:
            return False
        return self._dirty_

    def save(self):
        if self._savenow():
            with open(self._path_, "w") as fp:
                json.dump(self.copy(), fp)
            self._inc_saves()
            return
        if not self._inactive_:
            self._dirty_ = True

    @property
    def saves(self):
        return self._saves_

    @property
    def _path_(self):
        return self._truepath_

    @_path_.setter
    def _path_(self, path):
        self._truepath_ = path
        self._load()

    def __enter__(self):
        self._context_ = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._context_ = False
        self._inactive_ = False
        self.save()

    def _load(self):
        """
        called by '@path.setter' to load dict. uses '_inactive_' to prevent dict from beeing
        written on any changes caused by loading.
        :return: None
        """
        self._inactive_ = True
        try:
            with open(self._truepath_) as fp:
                for k, v in json.load(fp).items():
                    self[k] = v
        except FileNotFoundError:
            pass
        finally:
            self._inactive_ = False
            if self._context_ == False:
                self._dirty_ = True

    def reload(self):
        """
        call if another instance may have changed the json file on disk.
        :return: None
        """
        inactive = self._inactive_
        dirty = self._dirty_
        self._load()
        self._inactive_ = inactive
        self._dirty_ = dirty