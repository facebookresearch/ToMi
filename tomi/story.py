#!/usr/bin/env python3
# Copyright (c) 2019-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

from . import actions
import copy
from enum import Enum
from .world import World
from .oracle import Oracle
from typing import List, Tuple
from . import actions
import numpy as np


def sample_question(
    oracle_start_state, oracle, agent1, agent2, obj, question, agent_order
):
    idx_dummy = [0]
    if question == "memory":
        action, trace = actions.MemoryAction(oracle_start_state, obj), "memory"
    elif question == "reality":
        action, trace = actions.RealityAction(oracle, obj), "reality"
    elif question == "belief":
        action = actions.BeliefSearchAction(oracle, agent1, agent2, obj)
        trace = f'second_order_{agent_order}_{"" if action.tom else "no_"}tom'
    elif question == "search":
        action = actions.SearchedAction(oracle, agent1, obj)
        trace = f'first_order_{agent_order}_{"" if action.tom else "no_"}tom'
    return action, trace


class StoryType(Enum):
    true_belief = "true_belief"
    false_belief = "false_belief"
    second_order_false_belief = "second_order_false_belief"


def enter(oracle: Oracle, agent: str, observers: List[int], location: str):
    if oracle.get_location(agent) == location:  # already in location
        return actions.LocationAction(oracle, (agent, location))
    else:  # somewhere else, move this person into location
        return actions.EnterAction(oracle, (agent, location), observers)


def generate_story(
    world: World,
) -> Tuple[List[List[actions.Action]], List[List[str]], StoryType]:
    oracle = Oracle(world)

    a1, a2, a3 = (world.get_agent() for _ in range(3))
    story_type = StoryType.true_belief

    location = world.get_location()
    alternative_loc = world.get_location()

    # Get an initial object and container in the room
    obj = world.get_object()
    container_1 = world.get_container()
    container_2 = world.get_container()
    oracle.set_containers(location, [container_1, container_2])
    oracle.set_object_container(obj, container_1)

    trace = []
    chapter = []

    # randomize the order in which agents enter the room
    first_agent = None
    agents = [(a1, 0), (a2, 1)]
    enter_observers = []
    np.random.shuffle(agents)
    agent_1, agent_2 = (x for _, x in agents)
    for agent, order in agents:
        chapter.append(enter(oracle, agent, enter_observers, location))
        enter_observers.append(agent)
        trace.append(f"enter_agent_{order}")

    # announce location of object
    chapter.append(actions.ObjectLocAction(oracle, obj, [a for a, _ in agents]))
    start_state = copy.deepcopy(oracle)

    # Allow up to 2 location changes and 1 move.  Randomize the order...
    act_types = ["move"] + ["loc_change"] * np.random.randint(1, 3)
    np.random.shuffle(act_types)

    # If we move in the middle, this story moves into the false belief scenario.
    story_type = StoryType.false_belief if act_types[1] == "move" else story_type

    move_observers = {a1, a2}
    for i, act_type in enumerate(act_types):
        if act_type == "move":
            # move the object to container_2
            chapter.append(
                actions.MoveAction(oracle, (a1, obj, container_2), list(move_observers))
            )
            trace.append(f"agent_0_moves_obj")
        elif oracle.get_location(a2) == location:
            # a2 is in location, exit...
            chapter.append(actions.ExitedAction(oracle, a2))
            move_observers.remove(a2)
            trace.append(f"agent_1_exits")
        else:
            enter_observers = [a1]
            # Assuming this is the last action, then with 50% chance exit the moving actor
            if np.random.randint(0, 2) == 0 and i == len(act_types) - 1:
                story_type = (
                    StoryType.second_order_false_belief
                )  # this now is a second order falst belief
                # We can only do this if this is the last index of act_types, otherwise this agent
                # will try to move the object, but will be in the wrong location
                chapter.append(actions.ExitedAction(oracle, a1))
                move_observers.remove(a1)
                enter_observers = []
                trace.append(f"agent_0_exits")

            enter_loc = location if np.random.randint(0, 2) == 0 else alternative_loc
            # a2 already exited, re-enter same room, or a different one
            chapter.append(
                actions.EnterAction(oracle, (a2, enter_loc), enter_observers)
            )
            if enter_loc == location:
                move_observers.add(a2)
            trace.append(
                f"agent_1_reenters_" + ("alt_loc" if enter_loc != location else "loc")
            )

    # generate indices for which person 3 should enter/exit
    indices = np.random.choice(
        np.arange(len(chapter) + 1), replace=False, size=np.random.randint(0, 3)
    )
    indices.sort()
    for idx, action in zip(indices, ["enter", "exit"]):
        if action == "exit":
            chapter.insert(idx, actions.ExitedAction(oracle, a3))
            enter_observers.pop()  # remove person 3 from observers
            trace.insert(idx, f"agent_2_exits")
        else:
            enter_loc = location if np.random.randint(0, 2) == 0 else alternative_loc
            chapter.insert(
                idx, actions.EnterAction(oracle, (a3, enter_loc), enter_observers)
            )
            enter_observers.append(a3)
            trace.insert(idx, f"agent_2_enters")

    # Add noise:
    indices = np.random.choice(
        np.arange(len(chapter) + 1), replace=False, size=np.random.randint(0, 3)
    )
    for idx in indices:
        person = np.random.choice([a1, a2, a3], 1)[0]
        things = world.get_all("objects")
        thing = np.random.choice(things, 1)[0]
        chapter.insert(idx, actions.NoiseAction(oracle, person, thing))

    stories, traces = [], []
    for q in ["memory", "search", "belief", "reality"]:
        qtext, qtrace = sample_question(start_state, oracle, a1, a2, obj, q, agent_1)
        stories.append(chapter + [qtext])
        traces.append(trace + [qtrace])
    for q in ["search", "belief"]:
        qtext, qtrace = sample_question(start_state, oracle, a2, a1, obj, q, agent_2)
        stories.append(chapter + [qtext])
        traces.append(trace + [qtrace])
    return stories, traces, story_type
