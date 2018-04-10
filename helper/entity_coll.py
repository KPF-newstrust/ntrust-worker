#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 곧 deprecated 될 entity db

from . import mongo

entity_dic = dict()

coll = mongo.get_collection("entity_dic")
docs = coll.find(None, {"word": True, "types": True, "_id": False})
for doc in docs:
    entity_dic[doc["word"]] = doc["types"]

print("EntityCollector: %d words loaded" % (len(entity_dic)))


class EntityCollector:
    def __init__(self):
        if len(entity_dic) == 0:
            raise Exception("Entity dictionary data is not loaded.")
        self.allPersons = []
        self.allOrgans = []
        self.allLocations = []
        self.allPlans = []
        self.allProducts = []
        self.allEvents = []

    def feed(self, word):
        if word not in entity_dic:
            return
        types = entity_dic[word]
        for type in types:
            if type == "PS":
                self.allPersons.append(word)
            elif type == "OG":
                self.allOrgans.append(word)
            elif type == "LC":
                self.allLocations.append(word)
            elif type == "PL":
                self.allPlans.append(word)
            elif type == "PR":
                self.allProducts.append(word)
            elif type == "EV":
                self.allEvents.append(word)
            else:
                raise Exception("Invalid type code: " + type)

    def get_result(self, prefix, ret=None):
        if ret is None:
            ret = dict()
        ret[prefix + "PS"] = list(set(self.allPersons)) or None
        ret[prefix + "OG"] = list(set(self.allOrgans)) or None
        ret[prefix + "LC"] = list(set(self.allLocations)) or None
        ret[prefix + "PL"] = list(set(self.allPlans)) or None
        ret[prefix + "PR"] = list(set(self.allProducts)) or None
        ret[prefix + "EV"] = list(set(self.allEvents)) or None
        return ret

    def dump(self):
        print("Persons:", set(self.allPersons))
        print("Organizations:", set(self.allOrgans))
        print("Locations:", set(self.allLocations))
        print("Plans:", set(self.allPlans))
        print("Products:", set(self.allProducts))
        print("Events:", set(self.allEvents))
