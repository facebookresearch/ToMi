#!/usr/bin/env python3
# Copyright (c) 2019-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.


import numpy as np
from .oracle import Oracle
from typing import List, Tuple


class Action(object):
    def __init__(self, templates):
        self.templates = templates

    def render(self):
        raise NotImplementedError


class DeclarativeAction(Action):
    def render(self):
        if hasattr(self, "fixed"):
            return self.templates[self.fixed]
        return np.random.choice(self.templates)


class InterrogativeAction(Action):
    def render(self):
        if hasattr(self, "fixed"):
            return self.templates[self.fixed]
        return np.random.choice(self.templates)


class ExitAction(DeclarativeAction):
    def __init__(self):
        super.__init__(
            ["%s exited the %s.", "%s left the %s.", "%s went out of the %s.",]
        )


class SearchedAction(InterrogativeAction):
    def __init__(self, oracle: Oracle, agent: str, obj: str):
        ans = oracle.get_direct_belief(agent, obj)
        # Label whether or not this question requires theory of mind
        self.tom = ans != oracle.get_object_container(obj)
        fill = (agent, obj, ans)
        super().__init__(
            ["Where will %s look for the %s?\t%s\t1" % fill,]
        )


class BeliefSearchAction(InterrogativeAction):
    def __init__(self, oracle: Oracle, a1: str, a2: str, obj: str):
        ans = oracle.get_indirect_belief(a1, a2, obj)
        # Does this question require theory of mind?
        self.tom = ans != oracle.get_object_container(obj)
        fill = (a1, a2, obj, ans)
        super().__init__(
            ["Where does %s think that %s searches for the %s?\t%s\t1" % fill,]
        )


class RealityAction(InterrogativeAction):
    def __init__(self, oracle: Oracle, obj: str):
        fill = (obj, oracle.get_object_container(obj))
        super().__init__(
            ["Where is the %s really?\t%s\t1" % fill,]
        )


class MemoryAction(InterrogativeAction):
    def __init__(self, oracle_start_state: Oracle, obj: str):
        fill = (obj, oracle_start_state.locations.obj_containers[obj])
        super().__init__(
            ["Where was the %s at the beginning?\t%s\t1" % fill,]
        )


class LocationAction(DeclarativeAction):
    def __init__(self, oracle: Oracle, args: str):
        if len(args) == 2:
            statement = "%s is in the %s." % args
            a1, loc = args
            # may be redundant
            oracle.set_location(a1, loc)
        else:  # 2 people
            statement = "%s and %s are in the %s." % args
            a1, a2, loc = args
            # may be redundant
            oracle.set_location(a1, loc)
            oracle.set_location(a2, loc)
        super().__init__([statement])


class ObjectLocAction(DeclarativeAction):
    def __init__(self, oracle: Oracle, obj: str, observers: List[str]):
        container = oracle.get_object_container(obj)
        super().__init__(
            ["The %s is in the %s." % (obj, container),]
        )

        # set direct beliefs
        for observer in observers:
            oracle.set_direct_belief(observer, obj, container)

        # set indirect beliefs
        for observer1 in observers:
            for observer2 in observers:
                if observer1 != observer2:
                    oracle.set_indirect_belief(observer1, observer2, obj, container)


class ExitedAction(DeclarativeAction):
    def __init__(self, oracle: Oracle, agent: str):
        fill = (agent, oracle.get_location(agent))

        super().__init__(
            ["%s exited the %s." % fill,]
        )
        oracle.set_location(agent, None)


class MoveAction(DeclarativeAction):
    def __init__(
        self, oracle: Oracle, args: Tuple[str, str, str], observers: List[str] = None
    ):
        super().__init__(
            ["%s moved the %s to the %s." % args,]
        )

        agent, obj, container = args
        oracle.set_object_container(obj, container)

        if not observers:
            observers = []
        observers.append(agent)
        # set direct beliefs
        for observer in observers:
            oracle.set_direct_belief(observer, obj, container)

        # set indirect beliefs
        for observer1 in observers:
            for observer2 in observers:
                if observer1 != observer2:
                    oracle.set_indirect_belief(observer1, observer2, obj, container)


class PeekAction(DeclarativeAction):
    def __init__(self, oracle, args: Tuple[str, str], observers: List[str] = None):
        super().__init__(
            ["%s looked in the %s." % args,]
        )

        agent, container = args
        contents = oracle.get_container_obj(container)

        if not observers:
            observers = []

        observers.append(agent)
        # set direct beliefs
        for observer in observers:
            for obj in contents:
                oracle.set_direct_belief(observer, obj, container)

        # set indirect beliefs
        for observer1 in observers:
            for observer2 in observers:
                if observer1 != observer2:
                    for obj in contents:
                        oracle.set_indirect_belief(observer1, observer2, obj, container)


class TellAction(DeclarativeAction):
    def __init__(self, oracle: Oracle, a1: str, a2: str, obj: str):
        super().__init__(
            ["%s told %s where the %s is." % (a1, a2, obj),]
        )

        container = oracle.get_object_container(obj)
        oracle.set_direct_belief(a2, obj, container)
        oracle.set_indirect_belief(a2, a1, obj, container)


class EnterAction(DeclarativeAction):
    def __init__(
        self,
        oracle: Oracle,
        args: Tuple[str, str],
        observers: List[str] = None,
        no_world_adjust: bool = False,
    ):
        super().__init__(
            ["%s entered the %s." % args,]
        )

        agent, location = args
        oracle.set_location(agent, location)
        # assume all containers are not enclosed
        # agent knows location of everything
        objs = oracle.get_objects_at_location(location)
        if not observers:
            observers = []
        observers.append(agent)

        if not no_world_adjust:
            for obj in objs:
                container = oracle.get_object_container(obj)
                oracle.set_direct_belief(agent, obj, container)
                for observer1 in observers:
                    for observer2 in observers:
                        if observer1 != observer2:
                            oracle.set_indirect_belief(
                                observer1, observer2, obj, container
                            )


class NoiseAction(DeclarativeAction):
    def __init__(self, oracle: Oracle, person: str, thing: str):
        super().__init__(
            [
                f"{person} likes the {thing}",
                f"{person} dislikes the {thing}",
                f"{person} loves the {thing}",
                f"{person} hates the {thing}",
            ]
        )
        self.fixed = np.random.randint(0, len(self.templates))
