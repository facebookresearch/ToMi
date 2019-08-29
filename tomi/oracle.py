#!/usr/bin/env python3
# Copyright (c) 2019-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.


import copy
from .world import World
from typing import List
import numpy as np
from numpy.random import randint


class LocationMap(object):
    def __init__(
        self,
        agents: List[str],
        locations: List[str],
        objects: List[str],
        containers: List[str],
    ):
        # Maps agents to their locations.
        self.locations = {
            agent: locations[randint(0, len(locations))] for agent in agents
        }
        self.container_locations = {}
        self.containers = {l: [] for l in locations}
        for container in containers:
            loc = locations[randint(0, len(locations))]
            self.container_locations[container] = loc
            self.containers[loc].append(container)

        self.container_objs = {container: [] for container in containers}
        self.obj_containers = {}
        for obj in objects:
            container = containers[randint(0, len(containers))]
            self.container_objs[container].append(obj)
            self.obj_containers[obj] = container


class MemoryMap(object):
    def __init__(self, agents: List[str], objects: List[str]):

        obj_dict = {obj: None for obj in objects}
        mem_dict = {agent: copy.deepcopy(obj_dict) for agent in agents}

        # Dictionary of dictionaries mapping
        # agents to objects to containers. Represents
        # agents' belief about location of containers.
        self.direct_beliefs = copy.deepcopy(mem_dict)

        # Dictionary of dictionaries of dictionaries
        # mapping agents to direct belief dictionaries.
        # Represents agents' belief about other agents'
        # beliefs about location of containers.
        self.indirect_beliefs = {agent: copy.deepcopy(mem_dict) for agent in agents}


class Oracle(object):
    def __init__(self, world: World):
        self.world = World
        agents = world.get_all("agents")
        locations = world.get_all("locations")
        objects = world.get_all("objects")
        containers = world.get_all("containers")
        self.memory_map = MemoryMap(agents, objects)
        self.locations = LocationMap(agents, locations, objects, containers)

    #########################################
    ################ Beliefs ################
    #########################################

    def get_direct_belief(self, agent: str, obj: str) -> str:
        beliefs = self.memory_map.direct_beliefs
        return beliefs[agent][obj]

    def set_direct_belief(self, agent: str, obj: str, container: str):
        beliefs = self.memory_map.direct_beliefs
        beliefs[agent][obj] = container

    def get_indirect_belief(self, a1: str, a2: str, obj: str) -> str:
        indirect_beliefs = self.memory_map.indirect_beliefs
        return indirect_beliefs[a1][a2][obj]

    def set_indirect_belief(self, a1: str, a2: str, obj: str, container: str):
        indirect_beliefs = self.memory_map.indirect_beliefs
        indirect_beliefs[a1][a2][obj] = container

    #########################################
    ############### Locations ###############
    #########################################

    def get_location(self, agent: str) -> str:
        return self.locations.locations[agent]

    def set_location(self, agent: str, location: str):
        self.locations.locations[agent] = location

    def get_containers(self, location: str) -> List[str]:
        # Returns a list of containers at location
        return self.locations.containers[location]

    def set_containers(self, location: str, containers: List[str]):
        # May need to change to move containers bt locs
        # Containers is a list of containers at location
        for container in containers:
            self._set_container_location(container, location)
        self.locations.containers[location] = containers

    def get_objects_at_location(self, location: str) -> List[str]:
        objects = []
        for container in self.get_containers(location):
            objects.extend(self.get_container_obj(container))
        return objects

    def get_container_location(self, container: str) -> str:
        return self.locations.container_locations[container]

    def _set_container_location(self, container: str, location: str):
        self.locations.container_locations[container] = location

    def get_container_obj(self, container: str) -> str:
        # get list of objects in container
        return self.locations.container_objs[container]

    def _add_container_obj(self, container: str, obj: str):
        self.locations.container_objs[container].append(obj)

    def _remove_container_obj(self, container: str, obj: str):
        self.locations.container_objs[container].remove(obj)

    def get_object_container(self, obj: str) -> str:
        # get container that holds object
        return self.locations.obj_containers[obj]

    def set_object_container(self, obj: str, container: str):
        # set container that holds object
        prev_container = self.get_object_container(obj)
        if prev_container:
            self._remove_container_obj(prev_container, obj)
        self._add_container_obj(container, obj)
        self.locations.obj_containers[obj] = container
