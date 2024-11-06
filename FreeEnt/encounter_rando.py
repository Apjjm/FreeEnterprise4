import math
from . import databases
from .address import *

TRAPDOORS = ['DoubleDoor{}'.format(n) for n in range(2,17)]
BEHEMOTHS = ['behemoth1','behemoth2','behemoth3']

def apply(env):
    doors_to_disable = []
    behemoths_to_disable = []

    env.add_file('scripts/encounter_reduction.f4c')

    if not env.options.flags.has('encounter_keep_doors'):
        if env.options.flags.has('encounter_reduction'):
            # only disable half the trapdoors
            doors_to_disable = env.rnd.sample(TRAPDOORS, math.ceil(len(TRAPDOORS) * 0.6))
        elif env.options.flags.has('encounter_off'):
            # disable all trapdoors
            doors_to_disable = TRAPDOORS

        for d in doors_to_disable:
            env.add_substitution(f'trapdoor {d}', 'set #Temp')
    else:
        for d in TRAPDOORS:
            env.add_substitution(f'trapdoor {d}', 'clear #Temp')

    if not env.options.flags.has('encounter_keep_behemoths'):
        if env.options.flags.has('encounter_reduction'):
            # each behemoth has a 50/50 chance of being disabled
            behemoths_to_disable = [i for i in BEHEMOTHS if env.rnd.random() < 0.5]
        elif env.options.flags.has('encounter_off'):
            # disable all behemoths
            behemoths_to_disable = BEHEMOTHS

        if behemoths_to_disable:
            env.add_file('scripts/bahamut_no_behemoths.f4c')
            for b in BEHEMOTHS:
                if b not in behemoths_to_disable:
                    env.add_substitution(f'{b} disable', '')
    else:
        env.add_substitution('behemoth use toggle', '')

    if env.options.flags.has('encounter_toggle'):
        env.add_file('scripts/encounter_toggle.f4c')
    
    if env.options.flags.has('encounter_dangerous') and env.options.flags.has_any('encounter_toggle', 'encounter_off'):
        env.add_file('scripts/encounter_dangerous.f4c')
    else:
        env.add_substitution('encounter dangerous on', '')

    if not env.options.flags.has_any('encounter_toggle', 'encounter_off'):
        env.add_substitution('encounter default off', '')

    if not env.options.flags.has('encounter_reduction'):
        env.add_substitution('encounter reduction', '')

    if env.options.flags.has('encounter_cant_run'):
        env.add_file('scripts/cant_run.f4c')

    if env.options.flags.has('encounter_shuffle_wildish'):
        encounters_view = databases.get_encounters_dbview()
        for tier in range(5):
            tier_offsets = []
            tier_common = []
            tier_rare = []
            for encounter_data in encounters_view.find_all(lambda e: e.tier == tier):
                tier_offsets.append(encounter_data.id)
                tier_common.extend(encounter_data.common)
                tier_rare.append(encounter_data.rare)

            env.rnd.shuffle(tier_rare)
            env.rnd.shuffle(tier_common)
            for offset in tier_offsets:
                shuffled = [tier_common.pop() for _ in range(7)]
                _add_encounter_table(env, offset, shuffled, tier_rare.pop())

            assert(len(tier_rare) == 0)
            assert(len(tier_common) == 0)
    elif env.options.flags.has('encounter_shuffle_standard'):
        encounters_view = databases.get_encounters_dbview()
        for id in range(0x5D): # For giant only: range(0x4A, 0x50)
            encounter_data = encounters_view.find_one(lambda e: e.id == id)
            if encounter_data is not None:
                shuffled = env.rnd.sample(encounter_data.common, 7)
                _add_encounter_table(env, encounter_data.id, shuffled, encounter_data.rare)

def _add_encounter_table(env, offset, common, rare):
    env.add_binary(UnheaderedAddress(0x74796 + offset*8), common + [rare])
    if env.options.debug:
        if offset == 0x4B:
            if common[4] == 0xBC:
                print('Eshuffle - Searcher (Mac Giant) -> Searcher (Horseman) Machine x2')
            elif common[4] == 0xBB:
                print('Eshuffle - Searcher (Mac Giant) -> Machine x2 Beamer x2')
            elif common[4] == 0xC0:
                print('Eshuffle - Searcher (Mac Giant) -> Horseman x1 Beamer x2')
            elif common[4] == 0xC1:
                print('Eshuffle - Searcher (Mac Giant) -> Horseman x1 Beamer x1 Machine x1')
            elif common[4] == 0xC2:
                print('Eshuffle - Searcher (Mac Giant) -> Searcher (Mac Giant)')
            elif common[4] == 0xBE or common[4] == 0xBF:
                print('Eshuffle - Searcher (Mac Giant) -> Mac Giant x1')
            else:
                print('Eshuffle - Searcher (Mac Giant) -> {:2X}'.format(common[4]))