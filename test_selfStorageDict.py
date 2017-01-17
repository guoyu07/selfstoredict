from unittest import TestCase
import selfstoredict
import glob
import os
import pprint
import json

pp = pprint.PrettyPrinter(indent=4)


class TestSelfStorageDict(TestCase):
    def tearDown(self):
        for path in glob.glob("./test*json"):
            os.remove(path)

    def test_write_dict(self):
        ssd1 = selfstoredict.SelfStoreDict("test1.json")
        ssd1["team"] = dict()
        ssd1["team"]["leftback"]="hector"
        ssd1["team"]["goaly"]="neuer"
        ssd1["team"]["forward"]="modeste"
        print("{name} was saved {saves} times".format(name="ssd1", saves=ssd1.saves))
        with open("test1.json") as fp:
            pp.pprint(json.load(fp))

        # the assertion constructs a new object from file:
        self.assertEqual(selfstoredict.SelfStoreDict("test1.json")["team"]["goaly"], "neuer")

    def test_write_dict_in_context(self):
        path = "test2.json"
        with selfstoredict.SelfStoreDict(path) as ssd2:
            ssd2["team"] = dict()
            ssd2["team"]["leftback"]="hector"
            ssd2["team"]["goaly"]="neuer"
            ssd2["team"]["forward"]="modeste"
        print("{name} was saved {saves} times".format(name="ssd2", saves=ssd2.saves))
        with open(path) as fp:
            pp.pprint(json.load(fp))
        self.assertEqual(selfstoredict.SelfStoreDict(path)["team"]["goaly"], "neuer")

    def test_child_tells_parent(self):
        path = "test2.json"
        with selfstoredict.SelfStoreDict(path) as ssd2:
            ssd2["team"] = dict()
            ssd2["team"]["leftback"]="hector"
            ssd2["team"]["goaly"]="neuer"
            ssd2["team"]["forward"]="modeste"

        ssd3 = selfstoredict.SelfStoreDict(path)

        # ssd3["team"] is a child-dict
        ssd3["team"]["goaly"] = "horn"
        print("{name} was saved {saves} times".format(name="ssd3", saves=ssd3.saves))
        with open(path) as fp:
            pp.pprint(json.load(fp))

        # changes in child-dict are reflected in the json file
        self.assertEqual(selfstoredict.SelfStoreDict(path)["team"]["goaly"], "horn")

    def test_child_list_tells_parent(self):
        path = "test2.json"
        with selfstoredict.SelfStoreDict(path) as ssd5:
            ssd5["team"] = dict()
            ssd5["team"]["leftback"]="hector"
            ssd5["team"]["goaly"]="neuer"
            ssd5["team"]["forward"]="modeste"
            ssd5["substitutes"] = list()
            ssd5["substitutes"].append("mueller")
            ssd5["substitutes"].append("robben")
            ssd5["substitutes"].append("ribery")

        # you really save writes by using a context. but you don't have to
        print("{name} was saved {saves} times".format(name="ssd5", saves=ssd5.saves))

        ssd6 = selfstoredict.SelfStoreDict(path)
        print("sacked for badness: %s" % ssd6["substitutes"].pop(1))
        print("{name} was saved {saves} times".format(name="ssd6", saves=ssd6.saves))
        with open(path) as fp:
            pp.pprint(json.load(fp))

        # worx for child-lists too.
        self.assertEqual(selfstoredict.SelfStoreDict(path)["substitutes"][1], "ribery")

    def test_child_dict_in_list_tells_parent(self):
        path = "test3.json"
        with selfstoredict.SelfStoreDict(path) as ssd7:
            ssd7["team"] = dict()
            ssd7["team"]["leftback"]="hector"
            ssd7["team"]["goaly"]="neuer"
            ssd7["team"]["forward"]="modeste"
            ssd7["substitutes"] = list()
            ssd7["substitutes"].append("mueller")
            ssd7["substitutes"].append({"name": "robben", "attribute": "dutch"})
            ssd7["substitutes"].append("ribery")
        print("{name} was saved {saves} times".format(name="ssd7", saves=ssd7.saves))
        ssd8 = selfstoredict.SelfStoreDict(path)
        ssd8["substitutes"][1]["attribute"] = "diver"
        print("{name} was saved {saves} times".format(name="ssd8", saves=ssd8.saves))
        with open(path) as fp:
            pp.pprint(json.load(fp))

        # and for dicts in lists in dict....
        self.assertEqual(selfstoredict.SelfStoreDict(path)["substitutes"][1]["attribute"], "diver")