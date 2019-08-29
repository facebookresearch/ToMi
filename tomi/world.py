#!/usr/bin/env python3
# Copyright (c) 2019-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.


import json
import random
import os


class Entity:
    def __init__(self, name, properties):
        self.props = set(properties)
        self.name = name


class World:
    def __init__(self, world_file=None):
        if world_file is None:
            world_file = os.path.join(os.path.dirname(__file__), "world.json")
        with open(world_file, "r") as fin:
            self.entities = json.load(fin)
        self.ptrs = {k: -1 for k in self.entities.keys()}

    def reset(self):
        for k, v in self.entities.items():
            self.ptrs[k] = -1
            random.shuffle(v)

    def get_all(self, typ):
        return self.entities[typ]

    def get_agent(self):
        self.ptrs["agents"] += 1
        return self.entities["agents"][self.ptrs["agents"]]

    def get_location(self):
        self.ptrs["locations"] += 1
        return self.entities["locations"][self.ptrs["locations"]]

    def get_object(self):
        self.ptrs["objects"] += 1
        return self.entities["objects"][self.ptrs["objects"]]

    def get_container(self):
        self.ptrs["containers"] += 1
        return self.entities["containers"][self.ptrs["containers"]]
