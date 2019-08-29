#!/usr/bin/env python3
# Copyright (c) 2019-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import argparse
import os
from tomi.story import StoryType, generate_story
from tomi.world import World
from tqdm import tqdm
import numpy as np
import random


def main(opt):
    N = opt.num_stories
    w = None  # world
    world = World()
    for data_type in ["train", "val", "test"]:
        quota = {story_type: N // len(StoryType) for story_type in StoryType}
        stories_path = os.path.join(opt.out_dir, f"{data_type}.txt")
        trace_path = os.path.join(opt.out_dir, f"{data_type}.trace")
        with open(stories_path, "w") as f, open(trace_path, "w") as trace_f, tqdm(
            total=N
        ) as pbar:
            while any([v > 0 for v in quota.values()]):
                world.reset()
                stories, traces, story_type = generate_story(world)
                if quota[story_type] > 0:
                    quota[story_type] -= 1
                else:
                    # We've already generated enough of this type of story
                    continue
                for story, trace in zip(stories, traces):
                    print(
                        "\n".join(
                            [f"{i+1} {line.render()}" for i, line in enumerate(story)]
                        ),
                        file=f,
                    )
                    print(",".join(trace + [story_type.value]), file=trace_f)
                    f.flush()
                pbar.update(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", "-s", type=int, default=0, help="Seed for rng")
    parser.add_argument(
        "--num-stories",
        "-n",
        type=int,
        default=1000,
        help="Number of stories to generate for each type",
    )
    parser.add_argument("--out-dir", "-o", default="data", help="Output directory")
    opt = parser.parse_args()
    np.random.seed(opt.seed)
    random.seed(opt.seed)

    os.makedirs(opt.out_dir, exist_ok=True)
    main(opt)
