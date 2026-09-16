#!/usr/bin/env python3
"""Static/policy regressions; does not simulate the Stellaris engine."""
from __future__ import annotations
import re
import unittest
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRIGGERS = ROOT / 'common/scripted_triggers/foc_uprising_annexation_triggers.txt'
EFFECTS = ROOT / 'common/scripted_effects/foc_uprising_annexation_effects.txt'
EVENTS = ROOT / 'events/foc_uprising_annexation_events.txt'
HOOKS = ROOT / 'common/on_actions/foc_uprising_annexation_on_actions.txt'
TOKEN = re.compile(r'#[^\n]*|"(?:\\.|[^"\\])*"|[{}]|[=<>]+|[^\s{}=<>#]+')


def parse(text):
    tokens = [m.group() for m in TOKEN.finditer(text) if not m.group().startswith('#')]
    i = 0
    def block(nested=False):
        nonlocal i
        rows = []
        while i < len(tokens):
            key = tokens[i]; i += 1
            if key == '}':
                if not nested:
                    raise ValueError('Unexpected closing brace')
                return rows
            if i == len(tokens) or tokens[i] not in {'=', '>', '<', '>=', '<='}:
                rows.append((key, None, None)); continue
            op = tokens[i]; i += 1
            if i == len(tokens):
                raise ValueError('Missing value')
            value = tokens[i]; i += 1
            if value == '{':
                value = block(True)
            elif value.startswith('"'):
                value = value[1:-1]
            rows.append((key, op, value))
        if nested:
            raise ValueError('Unclosed block')
        return rows
    return block()


@dataclass
class Country:
    flags: set[str] = field(default_factory=set)
    ai: bool = True
    kind: str = 'default'
    origin: str = 'origin_separatists'
    planets: int = 1


class UprisingPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.defs = {key: val for key, op, val in parse(TRIGGERS.read_text('utf-8'))}
        cls.effects = EFFECTS.read_text('utf-8')

    def evaluate(self, name, c):
        def rows(entries):
            return all(test(row) for row in entries)
        def test(row):
            key, op, val = row
            if key == 'OR': return any(test(x) for x in val)
            if key == 'NOR': return not any(test(x) for x in val)
            if key == 'NOT': return not rows(val)
            if key in self.defs: return rows(self.defs[key]) == (val == 'yes')
            if key == 'has_country_flag': return val in c.flags
            if key == 'has_origin': return c.origin == val
            if key == 'is_country_type': return c.kind == val
            if key == 'is_ai': return c.ai == (val == 'yes')
            if key == 'num_owned_planets':
                if op == '>': return c.planets > int(val)
                if op == '=': return c.planets == int(val)
            raise AssertionError('Unsupported policy expression: ' + str(row))
        return rows(self.defs[name])

    def parent(self,c): return self.evaluate('foc_uprising_parent_country',c)
    def receiver(self,c): return self.evaluate('foc_uprising_rebel_recipient',c)
    def candidate(self,c): return self.evaluate('foc_uprising_breakaway_candidate',c)

    def test_empire_and_first_order_parents(self):
        for flag in ['foc_republic_origin_empire_country', 'foc_khan_first_order_country',
                     'fop_player_first_order', 'foc_republic_origin_became_first_order',
                     'foc_republic_origin_remnant_rebranded_first_order', 'foc_republic_origin_empire_crisis']:
            self.assertTrue(self.parent(Country({flag})), flag)
        self.assertTrue(self.parent(Country(origin='origin_fop_first_order', ai=False)))

    def test_final_order_excluded_with_stale_flags(self):
        for flag in ['foc_khan_final_order_country','fop_player_final_order',
                     'fop_origin_player_final_order_established']:
            c=Country({'foc_republic_origin_empire_country','fop_player_first_order',flag})
            self.assertFalse(self.parent(c)); self.assertFalse(self.candidate(c))
        self.assertFalse(self.parent(Country({'fop_player_first_order'},kind='foc_final_order_crisis_country')))

    def test_unrelated_parent_excluded(self):
        for flag in ['foc_republic_origin_republic_country','foc_republic_origin_separatist_country',
                     'foc_sw_new_republic_country','foc_mandalore_independent_country']:
            self.assertFalse(self.parent(Country({flag})))
        self.assertFalse(self.parent(Country()))

    def test_rebel_receivers_ai_or_player(self):
        for flag in ['foc_republic_origin_imperial_rebel_country','foc_republic_origin_rebel_alliance_country',
                     'foc_khan_rebel_alliance_country','foc_khan_first_order_resistance_country']:
            for ai in [True,False]: self.assertTrue(self.receiver(Country({flag}, ai=ai)))
        self.assertTrue(self.receiver(Country({'foc_khan_rebel_alliance_country'},kind='foc_khan_rebel_country')))

    def test_wrong_or_dead_recipient_rejected(self):
        for flag in ['foc_sw_new_republic_country','foc_sw_imperial_remnant_country',
                     'fop_player_first_order','fop_player_final_order']:
            self.assertFalse(self.receiver(Country({'foc_khan_rebel_alliance_country',flag})))
        self.assertFalse(self.receiver(Country({'foc_khan_rebel_alliance_country'},planets=0)))

    def test_human_and_story_countries_not_candidates(self):
        self.assertFalse(self.candidate(Country(ai=False)))
        for flag in ['foc_republic_origin_republic_country','foc_republic_origin_player_republic',
                     'foc_republic_origin_separatist_country','foc_sw_new_republic_country',
                     'foc_sw_imperial_remnant_country','foc_mandalore_independent_country',
                     'foc_v196_hutt_criminal_empire_country','foc_uprising_absorption_started']:
            self.assertFalse(self.candidate(Country({flag})),flag)
        self.assertFalse(self.candidate(Country(kind='fallen_empire')))
        self.assertFalse(self.candidate(Country(planets=0)))

    def test_mixed_faction_flags_fail_closed(self):
        rebels = ['foc_republic_origin_imperial_rebel_country',
                  'foc_republic_origin_rebel_alliance_country',
                  'foc_khan_rebel_alliance_country',
                  'foc_khan_first_order_resistance_country']
        imperial = ['foc_republic_origin_empire_country','fop_player_first_order',
                    'foc_khan_first_order_country','foc_republic_origin_empire_crisis']
        for a in rebels:
            for b in imperial:
                c = Country({a, b})
                self.assertFalse(self.parent(c))
                self.assertFalse(self.receiver(c))
                self.assertFalse(self.candidate(c))
        self.assertFalse(self.receiver(Country({rebels[0]}, origin='origin_fop_first_order')))
        self.assertFalse(self.candidate(Country(origin='origin_fop_first_order')))

    def test_native_origin_rewrites_not_excluded(self):
        for origin in ['origin_separatists','origin_necrophage','origin_void_dwellers',
                       'origin_void_machines','origin_subterranean','origin_tree_of_life']:
            self.assertTrue(self.candidate(Country(origin=origin)),origin)

    def test_provenance_is_mandatory_at_transfer_site(self):
        ast=parse(self.effects)
        found=[]
        def visit(rows):
            for key,op,val in rows:
                if isinstance(val,list):
                    if key=='every_country':
                        limits=[v for k,o,v in val if k=='limit']
                        if limits and any(k=='foc_uprising_breakaway_candidate' for k,o,v in limits[0]):
                            found.append(limits[0])
                    visit(val)
        visit(ast)
        self.assertEqual(len(found),1)
        self.assertIn(('has_country_flag','=','separatist_rebel_of_@event_target:foc_uprising_parent'),found[0])
        native=(ROOT/'events/unrest_events.txt').read_text('utf-8-sig')
        self.assertIn('set_country_flag = separatist_rebel_of_@root.owner',native)
        self.assertNotIn('is_at_war_with',self.effects)
        self.assertNotIn('has_origin',self.effects)

    def test_stale_target_and_ambiguity_guards(self):
        self.assertIn('event_target:foc_khan_rebel_alliance = { foc_uprising_rebel_recipient = yes }', self.effects)
        self.assertIn('NOT = { is_same_value = event_target:foc_uprising_recipient_candidate }',self.effects)
        self.assertNotIn('save_global_event_target_as',self.effects)
        self.assertNotIn('clear_global_event_target',self.effects)

    def test_transfer_safeguards_and_no_new_rewards(self):
        for word in ['every_owned_fleet','every_owned_starbase','every_owned_megastructure',
                     'every_owned_planet','every_planet_army','num_owned_planets = 0',
                     'has_fleet_flag = ssp_strike_fleet']:
            self.assertIn(word,self.effects)
        self.assertLess(self.effects.index('destroy_fleet = this'),self.effects.index('every_owned_planet'))
        self.assertNotIn('create_fleet',self.effects)
        self.assertNotIn('add_resource',self.effects)
        self.assertIn('else = { remove_country_flag = foc_uprising_absorption_started }',self.effects)

    def test_legacy_entry_point_has_safe_wrapper_only(self):
        text=(ROOT/'common/scripted_effects/foc_republic_origin_effects.txt').read_text('utf-8-sig')
        name='foc_republic_origin_absorb_empire_breakaway_revolts'
        ast=[(k,v) for k,o,v in parse(text) if k==name]
        self.assertEqual(ast,[(name,[('foc_uprising_scan_native_breakaways','=','yes')])])

    def test_independent_schedule_and_load_recovery(self):
        text=HOOKS.read_text('utf-8')
        self.assertIn('on_monthly_pulse_country',text)
        self.assertIn('on_single_player_save_game_load',text)
        events=EVENTS.read_text('utf-8')
        self.assertNotIn('foc_v197_republic_story_actor',events)
        self.assertNotIn('foc_republic_origin_empire_war_active',events)
        for event_id in ['foc_uprising_annex.1','foc_uprising_annex.2']:
            n=0
            for p in (ROOT/'events').glob('*.txt'):
                for kind,op,block in parse(p.read_text('utf-8-sig')):
                    if isinstance(block,list) and (('id','=',event_id) in block): n+=1
            self.assertEqual(n,1,event_id)

    def test_encoding_and_new_script_balance(self):
        for p in [TRIGGERS,EFFECTS,EVENTS,HOOKS]:
            b=p.read_bytes(); self.assertFalse(b.startswith(b'\xef\xbb\xbf'))
            parse(b.decode('utf-8'))


if __name__=='__main__':
    unittest.main(verbosity=2)
