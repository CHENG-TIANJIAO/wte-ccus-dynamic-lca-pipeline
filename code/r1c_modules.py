# -*- coding: utf-8 -*-
"""
Revision R1c of the manuscript: the unified modular boundary of the nine capture pathways
(R1_revision/BOUNDARY_DESIGN_R1c.md, sections 1, 2, 6 and decisions E1-E8) and the
declared discrete scenarios, as ONE table of named items.

This module holds no model: it turns a scenario name into, for every pathway,
  * the itemised process electricity E_PROC (MWh/y), every item = kWh per t-CO2 x the
    captured stream 67,159.1422656 t/y / 1000, or a source-workbook MWh value carried
    unchanged from R1b (mineralization, CCU synthesis, recycling);
  * the itemised transport term TRANSPORT_T (t-CO2/y);
  * the capture solvent + capture-unit increments REAGENT_T (t-CO2/y, R1b value unless a
    solvent variant is selected);
  * the CO2-loss fraction of the captured stream (0 in the base case).
Every new value is taken from R1_revision/03_new_sources/CONDITIONING_ENERGY_CANDIDATES.md
(cited per item below, "CAND x" = row x of that file); nothing is fitted.

Module numbers (design section 1): 1 base incineration; 2 common capture; 3 common
conditioning (compression to pipeline pressure); 4a pipeline; 4b ship; 4c road tanker;
4d ore / slag transport; 5a geological storage; 5b mineralization; 5c synthesis;
6 product substitution and end of life; 7 biogenic-carbon convention.

Used by apply_r1c.py (writes the BASE items into model_parameters.json) and by
carbon_model.set_scenario() (environment variable R1C_SCENARIO or a function call).
"""

Q_CAPTURED = 67159.1422656          # t-CO2/y captured = 0.9 x T_NAT (P2B2 basis)
MWH_PER_KWH_T = Q_CAPTURED / 1000.0  # MWh/y per kWh per t-CO2
EF_OFFICIAL = 0.423

CAPTURES = ['M1', 'M2', 'M3', 'M4', 'G1', 'G2', 'U1', 'U2a', 'U2b']
ORDER = ['S0', 'M1', 'M2', 'M3', 'M4', 'G1', 'G2', 'U1', 'U2a', 'U2b', 'R1', 'R2', 'R3']
CLASS = {'S0': 'ref', 'M1': 'min', 'M2': 'min', 'M3': 'min', 'M4': 'min',
         'G1': 'geo', 'G2': 'geo', 'U1': 'ccu', 'U2a': 'ccu', 'U2b': 'ccu',
         'R1': 'cr', 'R2': 'cr', 'R3': 'cr'}

# ------------------------------------------------------------------ named constants
# (value, unit, source).  "CAND" = R1_revision/03_new_sources/CONDITIONING_ENERGY_CANDIDATES.md
C = {
    'capture_unit': (15.0, 'kWh/t-CO2', 'LCCO2計算（CO2固定化）.xlsx!cc-LCA計算!D6 (capture unit), as R1b; '
                     'Bisinella et al. 2021, Waste Manag. 128, 99-113, Table 3'),
    'condenser': (10.0, 'kWh/t-CO2', 'LCCO2計算（CO2固定化）.xlsx!cc-LCA計算!D19 (air-cooled condenser), as R1b'),
    'compressor': (65.0, 'kWh/t-CO2', 'LCCO2計算（CO2固定化）.xlsx!cc-LCA計算!D21 (CO2 compression; the outlet pressure '
                   'is not stated in the source), as R1b; Bisinella et al. 2021 Table 3'),
    'compressor_high': (111.0, 'kWh/t-CO2', 'Koornneef et al. 2008, IJGGC 2, 448-467, Table 4 and Section 3.4 '
                        '(0.101325 -> 11 MPa); CAND 3a / section 6 flag; decision E1 (replacement, not added)'),
    'ship_liquefaction': (17.4, 'kWh/t-CO2', 'Roussanaly et al. 2021, Energies 14, 5635, Table 3 row "Inland emitter '
                          'scenarios" (90 bara, 40 C -> liquid 7 barg); CAND 1b; design section 6 row 4b'),
    'ship_liquefaction_high': (39.0, 'kWh/t-CO2', 'IEAGHG 2020-10, Table 10-7, Low P, pressurised; CAND 1c'),
    'unloading': (2.5, 'kWh/t-CO2', 'IEAGHG 2020-10, Table 10-11 (2.53 / 2.3 kWh/t receiving-side conditioning); '
                  'CAND 3b; design section 6 row 4b'),
    'ship_unload_pump': (4.5, 'kWh/t-CO2', 'IEAGHG 2020-10, p. 25: pumping the shipped liquid from 6.5 to 150 bar '
                         'for injection, 4-5 kWh/t, mid-point (pumping only; heating not included in the source value); CAND 3b sensitivity; R1d (audit A3): '
                         'REPLACES unloading 2.5 + wellhead boost 7 for a high-pressure well reached by ship'),
    'capture_capital': (745.649, 't-CO2/y', '资本财计算.xlsx!Sheet1 rows 9/10, capture (CC) part only: '
                        '(L9 x 3.01 + P9 x 3.41) / 20 = (777.789 x 3.01 + 3,686.752 x 3.41) / 20; the same for '
                        'every capture pathway (module 2); R1d (audit A2)'),
    'synthesis_capital_U1': (1269.243, 't-CO2/y', '资本财计算.xlsx!Sheet1 row 10, synthesis (CCU) part only: '
                             '(N10 x 3.01 + R10 x 3.41) / 20; outside the base boundary (author decision 2026-09-19: '
                             'capital = capture unit only, for all nine); declared scenario SCAPU. The list '
                             '(rows 53-60) includes a carbonator and calciner (calcium-looping capture equipment)'),
    'synthesis_capital_U2': (333.750, 't-CO2/y', '资本财计算.xlsx!Sheet1 row 9, synthesis (CCU) part only: '
                             '(N9 x 3.01 + R9 x 3.41) / 20; outside the base boundary; declared scenario SCAPU'),
    'capital_life_stated': (30.0, 'years', '资本财计算.xlsx!Sheet1!D3 (stated life); the source formula divides by 20, '
                            'kept in the base (author decision 2026-09-19); scenario SL30 uses 30'),
    'r3_gas_block': (780.2033898305085, 'MWh/y', 'LCCO2計算（ケミカルリサイクル） .xlsx!LCA計算!I42 = 0.137 kWh per kg '
                     'feed (pyrolysis-gas block, the block the national R3 anchor is built on); R1f: the process '
                     'electricity of R3 is aligned with its anchor'),
    'r3_hvc_block': (6048.0, 'MWh/y', 'LCCO2計算（ケミカルリサイクル） .xlsx!LCA計算!I18 = 0.3 kWh per kg feed (alternative '
                     'block); R1f: declared scenario SR3HVC'),
    'm4_cao_mass': (34942.24765868887, 't CaO/y', 'LCCO2計算（CO2固定化）.xlsx!LCA計算!I71 (200 kg CaO per 384.4 kg CO2)'),
    'm4_cao_factor_source': (0.422, 'kg-CO2/kg', 'LCCO2計算（CO2固定化）.xlsx!LCA計算!AE19, the unlabeled value read by the '
                             'source formula L71; R1f base uses the quicklime factor 1.12 (AD36); declared scenario SM4CAO'),
    'm4_water_sheet': (2600.0, 'kg water per 384.4 kg CO2', 'LCCO2計算（CO2固定化）.xlsx!LCA計算!D81 (value used by the '
                       'calculation sheet; base)'),
    'm4_water_transcribed': (30600.0, 'kg water per 384.4 kg CO2', 'DB.xlsx!CCUS!N8 (transcription of the source data); '
                             'R1g: declared scenario SM4WATER'),
    'm4_water_mass': (454249.2195629553, 't water/y', 'LCCO2計算（CO2固定化）.xlsx!LCA計算!I81 = 2,600/384.4 x captured CO2 '
                      '(= m4_cao_mass x 2,600/200)'),
    'm4_water_factor': (0.00065, 'kg-CO2/kg', 'LCCO2計算（CO2固定化）.xlsx!LCA計算!AD22 (no source mark); item L81 = '
                        '295.26 t-CO2/y'),
    'tanker_liquefaction': (16.0, 'kWh/t-CO2', 'IEAGHG 2020-10, Table 10-7, Medium P, pressurised; CAND 2b; declared '
                            'an ANALOGY from ship liquefaction to the road-tanker state (decision E7)'),
    'tanker_liquefaction_low': (9.0, 'kWh/t-CO2', 'Roussanaly et al. 2021 Table 3 (90 bara -> 15 barg); CAND 2a; '
                                'decision E7 range 9-16'),
    'wellhead_boost': (7.0, 'kWh/t-CO2', 'Koornneef et al. 2008, IJGGC 2, 448-467, Table 4 (recompression 10.7 -> '
                       '15 MPa at the injection site); CAND 3a; decision E4 (wellhead-pressure scenario, not a '
                       'depth factor)'),
    'ship_fuel': (22.0, 'kg-CO2/t-CO2 per ~1,000 km', 'author-DERIVED (CAND 5c): Roussanaly et al. 2021 Table 4 '
                  '(7.07 g fuel/t-CO2/km, 2.5 kt ship) x Fourth IMO GHG Study 2020 Table 21 (HFO 3.114 g CO2/g) '
                  'x 1,000 km = 22.0; decision E5'),
    'ship_ipcc': (35.0, 'kg-CO2/t-CO2 per 1,000 km', 'IPCC 2005 SRCCS Ch. 4, Section 4.3.3, p. 186: ships 3-4 % per '
                  '1,000 km incl. boil-off and engine exhaust, mid-point; CAND 5d; decision E6'),
    'pipeline': (20.0, 'kg-CO2/t-CO2 per 1,000 km', 'IPCC 2005 SRCCS Ch. 4, Section 4.6, p. 192: 1-2 % per 1,000 km, '
                 'upper end; equals Bisinella et al. 2021 Section 2.4 (decision E3); CAND 4a'),
    'road_factor': (0.134, 'kg-CO2/t-km', 'LCCO2.xlsx!co2運搬!C6 (source-workbook factor, no literature source; '
                    'disclosed)'),
    'road_km_U': (50.0, 'km', 'LCCO2.xlsx!co2運搬!C4 (to the synthesis plant), as R1b (D9)'),
    'road_km_G_port': (10.0, 'km', 'declared road leg to the port, as the 10 km truck leg of the source-workbook '
                       'storage chain (R1b variant S3)'),
    'ship_distance': (1000.0, 'km', 'NEDO LCO2 demonstration Maizuru <-> Tomakomai, about 1,000 km one way '
                      '(ClassNK technical journal 2026, p. 31-33; CAND 6d); decision E2'),
    'loss_transport': (0.01, 'fraction of the captured stream', 'Bisinella et al. 2021 (1 % transport), as R1b D8'),
    'loss_storage': (0.02, 'fraction of the captured stream', 'Bisinella et al. 2021 (2 % storage), as R1b D8'),
    'loss_tanker_U': (0.01, 'fraction of the captured stream', 'declared: the 1 % transport loss applied to the U '
                      'road-tanker leg (design C7: G and U treated alike)'),
}


def val(k):
    return C[k][0]


# ------------------------------------------------------------------ scenarios
# options: g_mode ship|pipeline; compressor kWh/t; ship_liq; unload; g1_highP, g2_highP (high-pressure well);
# no_comp (pathways without the compressor item); u_liq; ship_fuel kg/t; u_trans_abs; losses; solvent (mult, scope);
# ore_mult (M1/M2); dep12 (R1b only)
BASE_OPTS = dict(g_mode='ship', compressor=val('compressor'), ship_liq=val('ship_liquefaction'),
                 unload=val('unloading'), g1_highP=False, g2_highP=True, no_comp=(), u_liq=val('tanker_liquefaction'), ship_fuel=val('ship_fuel'),
                 u_trans_abs=None, losses=None, cap_life=20.0, cap_synth=False, r3_mwh=None, m4_cao=None, m4_water=None, solvent=(1.0, 'declared'), ore_mult=1.0,
                 loss_to=('G1', 'G2', 'U1', 'U2a', 'U2b'))

SCENARIOS = {
    'BASE': ('R1c base: common 90 kWh/t capture + conditioning; U road tanker with liquefaction 16 kWh/t; '
             'G Japan-oriented ship (~1,000 km, 7 barg), liquefaction 17.4 kWh/t, ship fuel 22 kg/t (one way) + '
             '10 km road; receiving side G1 unloading 2.5 kWh/t, G2 (high-pressure well) pumping to injection '
             'pressure 4.5 kWh/t in place of 2.5 + 7 (R1d, audit A3)', {}),
    'SP': ('pipeline instead of ship for G (20 kg/t, no liquefaction, no unloading, no road leg)',
           dict(g_mode='pipeline')),
    'SC': ('high compression energy: compressor 65 -> 111 kWh/t (replacement) for all nine capture pathways',
           dict(compressor=val('compressor_high'))),
    'SUC': ('upper bound of a possible overlap: the U synthesis electricity already contains CO2 compression; '
            'compressor 65 kWh/t removed for U1/U2a/U2b (R1d, audit A4; replaces SU15)',
            dict(no_comp=('U1', 'U2a', 'U2b'))),
    'SMC': ('upper bound of a possible overlap: the M1/M3/M4 process electricity already contains CO2 '
            'compression; compressor 65 kWh/t removed for M1, M3, M4 (R1d, audit section 4.1)',
            dict(no_comp=('M1', 'M3', 'M4'))),
    'SUL9': ('U tanker liquefaction 9 instead of 16 kWh/t', dict(u_liq=val('tanker_liquefaction_low'))),
    'SG1': ('G1 at the high wellhead pressure of G2 (ship: pumping 4.5 instead of 2.5 kWh/t; pipeline: boost '
            '7 kWh/t)', dict(g1_highP=True)),
    'SL39': ('ship liquefaction 39 instead of 17.4 kWh/t', dict(ship_liq=val('ship_liquefaction_high'))),
    'SIPCC': ('ship combined emission IPCC 3-4 % incl. boil-off, 35 kg/t (+ 10 km road)',
              dict(ship_fuel=val('ship_ipcc'))),
    'SLOSS': ('CO2 losses on the base: G 1 % transport + 2 % storage, U 1 % tanker transport',
              dict(losses='full')),
    'SP_SLOSS': ('pipeline + losses: G 1 % transport + 2 % storage, U 1 % tanker',
                 dict(g_mode='pipeline', losses='full')),
    'SIPCC_SLOSS': ('IPCC ship 35 kg/t + losses: G 2 % storage ONLY (boil-off already in the 3-4 %), U 1 % tanker',
                    dict(ship_fuel=val('ship_ipcc'), losses='storage_only_G')),
    'S1a': ('solvent x0.5 (declared 1,008 part; nine capture pathways)', dict(solvent=(0.5, 'declared'))),
    'S1b': ('solvent x2 (declared 1,008 part; nine capture pathways)', dict(solvent=(2.0, 'declared'))),
    'S1c': ('solvent x0.5 on the whole REAGENT_T (alternative scope)', dict(solvent=(0.5, 'whole'))),
    'S1d': ('solvent x2 on the whole REAGENT_T (alternative scope)', dict(solvent=(2.0, 'whole'))),
    'S4a': ('M1/M2 ore transport x0.5', dict(ore_mult=0.5)),
    'S4b': ('M1/M2 ore transport x2', dict(ore_mult=2.0)),
    'S6': ('U CO2 transport 719 (hard-coded source value) instead of 449.97', dict(u_trans_abs=719.0)),
    'SCAPU': ('U synthesis-equipment capital added back (U1 +1,269.243, U2a/U2b +333.750 t/y; capital workbook, '
              'synthesis part; its U1 list includes calcium-looping capture equipment)', dict(cap_synth=True)),
    'SL30': ('capital life 30 years (the stated life) instead of the 20-year divisor of the source formula: capture-unit '
             'capital x 20/30 for all nine capture pathways', dict(cap_life=30.0)),
    'SR3HVC': ('R3 process electricity of the alternative block, 6,048 instead of 780.2 MWh per year (R1f)',
               dict(r3_mwh=6048.0)),
    'SM4CAO': ('M4 CaO charged at the source-formula value 0.422 instead of the quicklime factor 1.12 (R1f)',
               dict(m4_cao=0.422)),
    'SM4WATER': ('M4 process water at the transcription of the source data, 30,600 instead of 2,600 kg per 384.4 kg '
                 'CO2 (R1g)', dict(m4_water=30600.0)),
    'BND_UNFAV_G': ('bounding, all-unfavourable for G: ship + IPCC 35 kg/t + liquefaction 39 + compressor 111 '
                    '(nine capture pathways, common module) + 2 % storage loss (G only)',
                    dict(ship_fuel=val('ship_ipcc'), ship_liq=val('ship_liquefaction_high'),
                         compressor=val('compressor_high'), losses='storage_only_G', loss_to=('G1', 'G2'))),
    'BND_FAV_G': ('bounding, all-favourable for G: pipeline, no loss, base compressor (identical to SP)',
                  dict(g_mode='pipeline')),
}
SCENARIO_ORDER = list(SCENARIOS)


def _item(key, label, mwh, module, source, kwh_t=None, group='b_el'):
    return dict(key=key, label=label, MWh=mwh, kWh_per_t=kwh_t, module=module, group=group, source=source)


def _titem(key, label, t, module, source, group='b_trans'):
    return dict(key=key, label=label, t=t, module=module, group=group, source=source)


def build(scenario, r1b):
    """Items of one scenario.

    r1b: dict with the R1b ledger values E_PROC_MWH, TRANSPORT_T, REAGENT_T (all 13) and
    solvent_declared (1,008); the parts R1c does not touch are carried from it.
    Returns dict(eproc_items, trans_items, eproc, trans, reag, loss, opts)."""
    if scenario == 'R1B':                       # the R1b state itself, for comparison
        eproc = dict(r1b['E_PROC_MWH']); trans = dict(r1b['TRANSPORT_T']); reag = dict(r1b['REAGENT_T'])
        return dict(eproc_items=None, trans_items=None, eproc=eproc, trans=trans, reag=reag,
                    loss={p: 0.0 for p in ORDER}, opts=None, cap={p: 0.0 for p in ORDER})
    if scenario not in SCENARIOS:
        raise KeyError(f'unknown R1c scenario {scenario!r}; known: {SCENARIO_ORDER + ["R1B"]}')
    o = dict(BASE_OPTS)
    o.update(SCENARIOS[scenario][1])
    k = MWH_PER_KWH_T
    ei, ti = {}, {}
    for p in ORDER:
        c = CLASS[p]
        e, t = [], []
        if p in CAPTURES:
            # modules 2 + 3: common capture + conditioning (identical for the nine)
            e.append(_item('capture_unit', 'capture-unit electricity', val('capture_unit') * k, 2,
                           C['capture_unit'][2], val('capture_unit')))
            e.append(_item('condenser', 'air-cooled condenser electricity', val('condenser') * k, 3,
                           C['condenser'][2], val('condenser')))
            if p not in o['no_comp']:
                src = C['compressor'][2] if o['compressor'] == val('compressor') else C['compressor_high'][2]
                e.append(_item('compressor', 'CO2 compressor to pipeline pressure', o['compressor'] * k, 3,
                               src, o['compressor']))
        if c == 'min':
            mwh = r1b['E_PROC_MWH'][p] - (val('capture_unit') + val('condenser') + val('compressor')) * k
            e.append(_item('mineralization', 'mineralization process electricity (source workbook, as R1b)',
                           mwh, '5b', 'LCCO2計算（CO2固定化）.xlsx!LCA計算 (P2B2 section 4), as R1b'))
            mult = o['ore_mult'] if p in ('M1', 'M2') else 1.0
            lab = 'ore transport (t-km, as R1b)' if p in ('M1', 'M2') else 'slag transport (as R1b)'
            t.append(_titem('ore_slag_transport', lab, r1b['TRANSPORT_T'][p] * mult, '4d',
                            'LCCO2計算（CO2固定化）.xlsx!運搬 (P2B2 section 4), as R1b'
                            + (f'; x{mult} (declared variant)' if mult != 1.0 else '')))
        elif c == 'geo':
            if o['g_mode'] == 'ship':
                src = (C['ship_liquefaction'][2] if o['ship_liq'] == val('ship_liquefaction')
                       else C['ship_liquefaction_high'][2])
                e.append(_item('ship_liquefaction', 'liquefaction after the compressor to 7 barg', o['ship_liq'] * k,
                               '4b', src, o['ship_liq']))
                highP = o['g1_highP'] if p == 'G1' else o['g2_highP']
                if highP:
                    e.append(_item('unloading', 'unloading + pumping to the injection pressure of a high-pressure '
                                   'well (replaces 2.5 + 7)', val('ship_unload_pump') * k, '4b',
                                   C['ship_unload_pump'][2], val('ship_unload_pump')))
                else:
                    e.append(_item('unloading', 'unloading / reconditioning at the receiving terminal',
                                   o['unload'] * k, '4b', C['unloading'][2], o['unload']))
                src = C['ship_fuel'][2] if o['ship_fuel'] == val('ship_fuel') else C['ship_ipcc'][2]
                t.append(_titem('ship', 'ship leg ~1,000 km one way, no ballast return' + (' (fuel only)' if o['ship_fuel'] == val('ship_fuel')
                                                               else ' (IPCC combined incl. boil-off)'),
                                o['ship_fuel'] * Q_CAPTURED / 1000.0, '4b', src))
                t.append(_titem('road_to_port', 'road leg to the port, 10 km',
                                val('road_factor') * val('road_km_G_port') * Q_CAPTURED / 1000.0, '4b',
                                C['road_factor'][2] + '; ' + C['road_km_G_port'][2]))
            else:
                t.append(_titem('pipeline', 'pipeline ~1,000 km (IPCC 2 % upper end)',
                                val('pipeline') * Q_CAPTURED / 1000.0, '4a', C['pipeline'][2]))
            highP = o['g1_highP'] if p == 'G1' else o['g2_highP']
            if highP and o['g_mode'] == 'pipeline':          # ship: pumping already in 'unloading'
                e.append(_item('wellhead_boost', 'wellhead booster 10.7 -> 15 MPa', val('wellhead_boost') * k, '5a',
                               C['wellhead_boost'][2], val('wellhead_boost')))
        elif c == 'ccu':
            mwh = r1b['E_PROC_MWH'][p] - val('capture_unit') * k
            e.append(_item('synthesis', 'CCU synthesis electricity (source workbook, as R1b)', mwh, '5c',
                           'LCCO2.xlsx!ccuーLCA計算!I9 / I20 (P2B2 section 4), as R1b'))
            src = (C['tanker_liquefaction'][2] if o['u_liq'] == val('tanker_liquefaction')
                   else C['tanker_liquefaction_low'][2])
            e.append(_item('tanker_liquefaction', 'liquefaction to the road-tanker state (analogy)',
                           o['u_liq'] * k, '4c', src, o['u_liq']))
            if o['u_trans_abs'] is None:
                t.append(_titem('road_tanker', 'road tanker 50 km',
                                val('road_factor') * val('road_km_U') * Q_CAPTURED / 1000.0, '4c',
                                C['road_factor'][2] + '; ' + C['road_km_U'][2]))
            else:
                t.append(_titem('road_tanker', 'road tanker, hard-coded 719 (declared variant)', o['u_trans_abs'],
                                '4c', 'LCCO2.xlsx!まとめ!J10 = 719 (hard-coded, not reproducible), R1b variant S6'))
        elif c == 'cr':
            mwh = r1b['E_PROC_MWH'][p]
            if p == 'R3':                                    # R1f: aligned with the R3 anchor (gas block)
                mwh = o['r3_mwh'] if o['r3_mwh'] is not None else val('r3_gas_block')
            e.append(_item('recycling_process', 'chemical-recycling process electricity', mwh, 'R',
                           C['r3_gas_block'][2] if (p == 'R3' and mwh == val('r3_gas_block')) else
                           (C['r3_hvc_block'][2] if p == 'R3' else 'as shipped (P2A_S0_R)')))
        ei[p], ti[p] = e, t
    eproc = {p: sum(i['MWh'] for i in ei[p]) for p in ORDER}
    trans = {p: sum(i['t'] for i in ti[p]) for p in ORDER}
    # reagents
    reag = dict(r1b['REAGENT_T'])
    m, scope = o['solvent']
    if m != 1.0:
        for p in CAPTURES:
            reag[p] = (reag[p] + (m - 1.0) * r1b['solvent_declared']) if scope == 'declared' else reag[p] * m
    # losses (fraction of the captured stream; convention A charges the fossil share)
    loss = {p: 0.0 for p in ORDER}
    if o['losses'] == 'full':
        for p in o['loss_to']:
            loss[p] = (val('loss_transport') + val('loss_storage')) if CLASS[p] == 'geo' else val('loss_tanker_U')
    elif o['losses'] == 'storage_only_G':
        for p in o['loss_to']:
            loss[p] = val('loss_storage') if CLASS[p] == 'geo' else val('loss_tanker_U')
    # capital (inside C_p): change relative to the base (capture unit, 20-year divisor)
    cap = {p: 0.0 for p in ORDER}
    for p in CAPTURES:
        cap[p] = val('capture_capital') * (20.0 / o['cap_life'] - 1.0)
        if o['cap_synth'] and CLASS[p] == 'ccu':
            cap[p] += val('synthesis_capital_U1' if p == 'U1' else 'synthesis_capital_U2') * 20.0 / o['cap_life']
    if o['m4_cao'] is not None:                      # R1f: M4 CaO factor scenario (a C_p item, like capital)
        cap['M4'] += val('m4_cao_mass') * (o['m4_cao'] - 1.12)
    if o['m4_water'] is not None:                    # R1g: M4 process-water scenario (a C_p item)
        cap['M4'] += val('m4_water_mass') * (o['m4_water'] / val('m4_water_sheet') - 1.0) * val('m4_water_factor')
    return dict(eproc_items=ei, trans_items=ti, eproc=eproc, trans=trans, reag=reag, loss=loss, opts=o, cap=cap)
