#!/usr/bin/env python

"""
This script randomize stimuli in a way that there are always equal number of
cases where one special stimuli appears after any stimulus types, including
itself. For example, when there are 2 types of non-special stimuli (0 and 1),
the special stimulus 2 would appear X times after 0, X times after 1, and X
times after 2.

This script has not been thoroughly tested for boundary cases... Be careful
and use test_correctness() to test your results. If you get an assertion
error, something is wrong.
"""


import pickle
import random


NUM_ORDINARY_STIM_TYPES = 2
NUM_ORD_STIM_PER_TYPE_PER_BLOCK = 6
NUM_BLOCKS = 30


def test_correctness(block_result):
    assert(len(block_result) == NUM_ORDINARY_STIM_TYPES * NUM_ORD_STIM_PER_TYPE_PER_BLOCK * 2)
    # count
    pair_counters = [0 for _ in range(NUM_ORDINARY_STIM_TYPES + 1)]
    stim_counters = [0 for _ in range(NUM_ORDINARY_STIM_TYPES + 1)]
    for i in range(len(block_result)):
        stim_counters[block_result[i]] += 1
        if block_result[i] != NUM_ORDINARY_STIM_TYPES:
            continue
        pair_counters[block_result[i - 1]] += 1
    # number of stims
    assert(stim_counters.pop() == NUM_ORDINARY_STIM_TYPES * NUM_ORD_STIM_PER_TYPE_PER_BLOCK)
    assert(all([c == NUM_ORD_STIM_PER_TYPE_PER_BLOCK for c in stim_counters]))
    # number of pairs
    should_be = NUM_ORDINARY_STIM_TYPES * NUM_ORD_STIM_PER_TYPE_PER_BLOCK / (NUM_ORDINARY_STIM_TYPES + 1)
    assert(all([c == should_be for c in pair_counters]))


def main():
    results = []
    num_stim_types = NUM_ORDINARY_STIM_TYPES + 1  # 1 special stim
    num_spe_stim_per_block = NUM_ORDINARY_STIM_TYPES * NUM_ORD_STIM_PER_TYPE_PER_BLOCK
    num_stim_per_block = num_spe_stim_per_block * 2
    num_ord_spe_pairs = num_spe_stim_per_block / num_stim_types
    for _ in range(NUM_BLOCKS):
        # randomize pairs of ordinary + special
        ord_spe_stim_pairs = [i for i in range(NUM_ORDINARY_STIM_TYPES)
                                for _ in range(num_ord_spe_pairs)]
        random.shuffle(ord_spe_stim_pairs)
        # places to insert more ordinary stim
        ord_indexes = sorted([random.choice(range(num_ord_spe_pairs + 1))  # can insert before or after a pair (so + 1)
                              for _ in range(num_ord_spe_pairs)])
        ord_order = [i for i in range(NUM_ORDINARY_STIM_TYPES)
                       for _ in range(len(ord_indexes) / 2)]
        random.shuffle(ord_order)
        # places to insert more special stim (after another special stim)
        spe_indexes = sorted([random.choice(range(num_ord_spe_pairs))  # can insert after a pair, not before
                              for _ in range(num_ord_spe_pairs)])
        # construct the result list
        ord_counter, spe_counter = 0, 0
        block_result = []
        for i in range(len(ord_spe_stim_pairs) + 1):
            while ord_counter < len(ord_indexes) and ord_indexes[ord_counter] == i:
                block_result.append(ord_order[ord_counter])  # append an ordinary stim
                ord_counter += 1
            if i < len(ord_spe_stim_pairs):
                block_result.append(ord_spe_stim_pairs[i])  # append an ordinary stim
                block_result.append(NUM_ORDINARY_STIM_TYPES)  # append a special stim
            while spe_counter < len(spe_indexes) and spe_indexes[spe_counter] == i:
                block_result.append(NUM_ORDINARY_STIM_TYPES)  # append a special stim
                spe_counter += 1
        print block_result  # just printing to console because I'm lazy
        test_correctness(block_result)


if __name__ == '__main__':
    main()
