"""
Unified calculation workbook: every inventory term, its formula, its scaling rule and its
contribution, for all thirteen pathways, plus the Eq.2/Eq.6, Shapley and regional audits.

Live Excel formulas are written wherever a cell is derived, so the workbook recomputes on
open. It is a calculation chain, not a paste of final values.
"""
import os, sys, itertools, platform
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'regions'))
import carbon_model as CB
import monte_carlo as M
import scenario_decomposition as SD
import regional_model as RV

HDR = Font(bold=True, size=10)
FILL = PatternFill('solid', fgColor='DCE6F1')
wb = Workbook(); wb.remove(wb.active)


def sheet(name, header, widths=None):
    ws = wb.create_sheet(name)
    ws.append(header)
    for c in ws[1]:
        c.font = HDR; c.fill = FILL; c.alignment = Alignment(wrap_text=True, vertical='top')
    ws.freeze_panes = 'A2'
    for i, wd in enumerate(widths or [], start=1):
        ws.column_dimensions[get_column_letter(i)].width = wd
    return ws


# ================= 1. Inputs =================
ws = sheet('1_Inputs', ['Symbol', 'Meaning', 'Value', 'Unit', 'Scaling class', 'Source'],
           [16, 44, 14, 16, 18, 30, 13, 13, 13, 13, 13, 15])
for r in [
 ('cr_nat', 'National capture rate', CB.CR, 'dimensionless', 'input', 'design basis'),
 ('F_nat', 'National fossil combustion CO2', CB.F_NAT, 't-CO2/y', 'input', 'harmonised inventory'),
 ('T_nat', 'National total combustion CO2', CB.T_NAT, 't-CO2/y', 'input', 'harmonised inventory'),
 ('EF_nat', 'National grid emission factor', CB.EF_NAT, 't-CO2/MWh', 'input',
  'MoEJ/METI utility-list national average; the source inventories used 0.433 '
  'and every explicit electricity term was rebased to this value'),
 ('E_aux', 'Plant auxiliary electricity', CB.AUX, 'MWh/y', 'FIXED', 'harmonised inventory'),
 ('E_exp_base', 'Baseline electricity export, no capture', CB.EXP_NOCC, 'MWh/y', 'FIXED', 'harmonised inventory'),
 ('E_exp_cc', 'Electricity export with capture', CB.EXP_CC, 'MWh/y', 'derived', 'harmonised inventory'),
 ('P_steam', 'Steam-extraction export penalty', CB.STEAM_PEN, 'MWh/y', 'CAP', 'E_exp_base minus E_exp_cc'),
]:
    ws.append(list(r))
ws.append([])
ws.append(['Note', 'P_steam is the reboiler-duty penalty of the capture unit. It follows the '
                   'captured CO2, not the waste tonnage, and is therefore in the CAP class. '
                   'carbon_balance_v2 held it fixed, which was inconsistent with its own '
                   'scaling rule.'])
ws.append(['Scaling factors', 's_cap = (cr x T) / (cr_nat x T_nat);  s_F = F / F_nat;  both '
                              'dimensionless and equal to 1 at national conditions'])
ws.append([])
ws.append(['Per-pathway parameters. Sheets 3 and 6 compute every group from these cells with '
           'Excel formulas; no component value is typed in those sheets.'])
PARAM_ROW0 = ws.max_row + 2
ws.append(['ID', 'class', 'is capture', 'E_proc MWh/y', 'H_p t-CO2/y', 'QA_p t-CO2/y',
           'QB_p t-CO2/y', 'V_p t-CO2/y', 'L_R,p t-CO2/y', 'D_p t-CO2/y',
           'C_p t-CO2/y', 'verified national result'])
for c in ws[PARAM_ROW0]:
    c.font = HDR; c.fill = FILL
PROW = {}
for p in CB.ORDER:
    ws.append([p, CB.CLASS[p], 1 if p in CB.CAPTURES else 0, CB.E_PROC[p],
               CB.H2.get(p, 0.0), CB.QA.get(p, 0.0), CB.QB.get(p, 0.0),
               CB.V_P.get(p, 0.0), CB.L_R.get(p, 0.0),
               CB.D_P.get(p, 0.0), round(CB.residual(p), 6), CB.NET_NAT[p]])
    PROW[p] = ws.max_row
ws.append([])
ws.append(['Note', 'QA_p is the cradle-to-grave burden of the displaced fossil product; '
                   'QB_p is the combustion CO2 of the synthesised product, charged at the '
                   'fossil share f = F / T of the captured stream.  The net substitution '
                   'credit is (QA_p - f x QB_p) x s_cap.  V_p is the process vent (mixed '
                   'basis), charged at f.  L_R,p is the mineralization reactor loss only; '
                   'the capture slip (1 - cr) F is charged once, explicitly.'])
IN = "'1_Inputs'!"
CR_C, F_C, T_C, EF_C = IN + '$C$2', IN + '$C$3', IN + '$C$4', IN + '$C$5'
AUX_C, EXP_C, PEN_C = IN + '$C$6', IN + '$C$7', IN + '$C$9'

# ================= 2. Term classification (source of SI Table S5) =================
ws = sheet('2_Term_classification',
           ['Pathway', 'Inventory item', 'Symbol', 'Baseline value', 'Baseline unit',
            'Conversion factor', 'Final unit', 'Class', 'Scaling formula',
            'Random or deterministic', 'Shared or pathway-specific',
            'Treatment A/B dependence', 'Sign', 'Source'],
           [9, 36, 13, 14, 12, 15, 11, 11, 34, 21, 25, 20, 8, 26])

NA = 'N/A'
ITEMS = [
 ('Plant auxiliary electricity', 'E_aux', lambda p: CB.AUX, 'MWh/y', 'EF', 'FIXED',
  'E_aux x EF', 'random through EF', 'EF shared by all pathways', 'none', '+',
  'harmonised inventory'),
 ('Baseline electricity export', 'E_exp_base', lambda p: -CB.EXP_NOCC, 'MWh/y', 'EF', 'FIXED',
  'minus E_exp_base x EF', 'random through EF', 'EF shared by all pathways', 'none', '-',
  'harmonised inventory'),
 ('Steam generation burden', 'n/a', lambda p: 'not separate', 'MWh/y', 'n/a', 'FIXED',
  'inside E_exp_base; same waste tonnage in every region', 'deterministic',
  'shared by all pathways', 'none', 'n/a', 'harmonised inventory'),
 ('Steam-extraction export penalty', 'P_steam',
  lambda p: CB.STEAM_PEN if p in CB.CAPTURES else NA, 'MWh/y', 'EF', 'CAP',
  'P_steam x s_cap x EF', 'random through EF and cr', 'EF and cr shared', 'none', '+',
  'E_exp_base minus E_exp_cc'),
 ('Capture electricity', 'E_proc part',
  lambda p: 'inside E_proc' if p in CB.CAPTURES else NA, 'MWh/y', 'EF', 'CAP',
  'E_proc x s_cap x EF x m_el', 'random', 'm_el shared within family', 'none', '+',
  'harmonised inventory'),
 ('CO2 compression electricity', 'E_proc part',
  lambda p: 'inside E_proc' if p in CB.CAPTURES else NA, 'MWh/y', 'EF', 'CAP',
  'E_proc x s_cap x EF x m_el', 'random', 'm_el shared within family', 'none', '+',
  'harmonised inventory'),
 ('Conversion electricity', 'E_proc part',
  lambda p: 'inside E_proc' if CB.CLASS[p] in ('ccu', 'min') else NA, 'MWh/y', 'EF', 'CAP',
  'E_proc x s_cap x EF x m_el', 'random', 'm_el shared within family', 'none', '+',
  'harmonised inventory'),
 ('Total capture, compression and conversion electricity', 'E_proc',
  lambda p: CB.E_PROC[p] if p in CB.CAPTURES else NA, 'MWh/y', 'EF', 'CAP',
  'E_proc x s_cap x EF x m_el', 'random', 'm_el shared within family', 'none', '+',
  'harmonised inventory'),
 ('Pyrolysis electricity', 'E_proc',
  lambda p: CB.E_PROC[p] if CB.CLASS[p] == 'cr' else NA, 'MWh/y', 'EF', 'PLASTIC',
  'E_proc x s_F x EF x m_el', 'random', 'm_el shared within family', 'none', '+',
  'harmonised inventory'),
 ('Hydrogen demand', 'H_p', lambda p: CB.H2.get(p, NA), 't-CO2/y', 'already CO2', 'CAP',
  'H_p x s_cap x m_H2', 'random', 'm_H2 shared by all utilization pathways', 'none', '+',
  'harmonised inventory'),
 ('Direct fossil-carbon emission', 'F', lambda p: CB.F_NAT, 't-CO2/y', 'already CO2', 'CARBON',
  'enters phi; see the carbon-flow rows below', 'random', 'F shared by all pathways',
  'none', '+', 'national waste survey'),
 ('Uncaptured fossil fraction', '(1-cr) F',
  lambda p: 'applies' if p in CB.CAPTURES else NA, 't-CO2/y', 'already CO2',
  'CARBON', '(1 - cr) x F, charged exactly once', 'random through cr',
  'cr shared by capture pathways', 'none', '+', 'model'),
 ('Mineralization reactor loss', 'L_R,p', lambda p: CB.L_R.get(p, NA), 't-CO2/y',
  'already CO2', 'CAP', 'L_R x s_cap x f, inside phi (f = F / T, fossil share)',
  'random', 'pathway-specific', 'none', '+', 'source workbook, reactor loss only'),
 ('CCU process vent', 'V_p', lambda p: CB.V_P.get(p, NA), 't-CO2/y', 'already CO2',
  'CAP', 'V_p x s_cap x f, inside phi (mixed-basis vent at its fossil share)',
  'random', 'pathway-specific', 'none', '+', 'source workbook'),
 ('Product output', 'derived',
  lambda p: 'proportional to captured CO2' if CB.CLASS[p] == 'ccu' else NA, 't-CO2/y',
  'stoichiometric', 'CAP', 'proportional to cr x T; enters through QA and QB',
  'random', 'pathway-specific', 'none', 'n/a', 'harmonised inventory'),
 ('Displaced-product burden (cradle-to-grave)', 'QA_p',
  lambda p: CB.QA.get(p, NA), 't-CO2/y', 'already CO2', 'CAP',
  'minus QA x s_cap, INSIDE phi', 'random', 'pathway-specific', 'none', '-',
  'CFP database factors x product mass'),
 ('Product fossil-combustion charge', 'QB_p',
  lambda p: CB.QB.get(p, NA), 't-CO2/y', 'already CO2', 'CAP',
  'plus f x QB x s_cap, INSIDE phi; the net credit is (QA - f QB) x s_cap',
  'random', 'pathway-specific', 'none', '+',
  'stoichiometric combustion of the synthesised product'),
 ('Diverted plastic carbon', 'D_p', lambda p: CB.D_P.get(p, NA), 't-CO2/y', 'already CO2',
  'PLASTIC', 'minus D_p x s_F under treatment A; zero under treatment B',
  'random through F', 'pathway-specific', 'A only', '-', 'harmonised inventory'),
 ('Permanent geological storage', 'S_fossil',
  lambda p: 'applies' if CB.CLASS[p] in ('geo', 'min') else NA, 't-CO2/y', 'already CO2',
  'CARBON', 'implicit: the retained fraction is simply never released, and is not '
  'credited a second time', 'random through cr', 'cr shared', 'none', 'n/a', 'model'),
 ('Temporary product storage', 'tau_50, k',
  lambda p: 'applies' if CB.CLASS[p] in ('ccu', 'cr') else NA, 'y', 'Weibull',
  'not included', 'enters the dynamic climate layer only; the static balance is '
  'time-independent', 'deterministic', 'pathway-specific', 'none', 'n/a', 'Table 1 (main text)'),
 ('Final atmospheric release', 'E_product,f',
  lambda p: 'applies' if CB.CLASS[p] in ('ccu', 'cr') else NA, 't-CO2/y', 'already CO2',
  'CARBON', 'accounted through the QB charge (utilization) or D_p (recycling); the '
  'deferred release of U2b enters the dynamic layer', 'random',
  'pathway-specific', 'A/B for recycling', '+', 'model'),
 ('Capture reagents', 'R_p', lambda p: 'inside residual' if p in CB.CAPTURES else NA,
  't-CO2/y', 'already CO2', 'RESIDUAL', 'held at its national value, x m_rem',
  'random through m_rem', 'pathway-specific', 'none', '+', 'calibrated remainder'),
 ('CO2 transport', 'Tr_p', lambda p: 'inside residual' if p in CB.CAPTURES else NA,
  't-CO2/y', 'already CO2', 'RESIDUAL', 'held at its national value, x m_rem',
  'random through m_rem', 'pathway-specific', 'none', '+', 'calibrated remainder'),
 ('Product transport', 'Tr_prod',
  lambda p: 'inside residual' if CB.CLASS[p] in ('ccu', 'cr') else NA, 't-CO2/y',
  'already CO2', 'RESIDUAL', 'held at its national value, x m_rem', 'random through m_rem',
  'pathway-specific', 'none', '+', 'calibrated remainder'),
 ('Capital-related burdens', 'C_cap', lambda p: 'inside residual', 't-CO2/y', 'annualised',
  'RESIDUAL', 'annualised, held at its national value, x m_rem', 'random through m_rem',
  'pathway-specific', 'none', '+', 'calibrated remainder'),
 ('Calibrated residual, total', 'C_p', lambda p: round(CB.residual(p), 2), 't-CO2/y',
  'already CO2', 'RESIDUAL', 'C_p x m_rem', 'random through m_rem', 'pathway-specific',
  'shifts with the anchor under B', '+/-',
  'verified national value minus the explicit groups'),
]
for p in CB.ORDER:
    for (item, sym, val, bu, cf, cls, form, rnd, shr, ab, sgn, src) in ITEMS:
        v = val(p)
        applies = v != NA
        ws.append([p, item, sym if applies else NA, v, bu if applies else NA,
                   cf if applies else NA, 't-CO2/y' if applies else NA,
                   cls if applies else NA, form if applies else NA,
                   rnd if applies else NA, shr if applies else NA,
                   ab if applies else NA, sgn if applies else NA,
                   src if applies else NA])

# ================= 3. Eq.2 term by term, national, ALL FORMULAS ================
ws = sheet('3_Eq2_national',
           ['Pathway', 's_cap (formula)', 'b_fix (formula)', 'b_steam (formula)',
            'b_el (formula)', 'phi (formula)', 'b_h2 (formula)', 'C_p (link)',
            'Eq.2 total (formula)', 'Verified national value', 'Difference (formula)'],
           [22, 15, 15, 15, 15, 15, 15, 14, 19, 21, 18])
for i, p in enumerate(CB.ORDER, start=2):
    r = PROW[p]
    cls = CB.CLASS[p]
    FT = '(%s/%s)' % (F_C, T_C)                       # fossil share f = F / T
    if cls == 'ref':
        phi = '=%s' % F_C
    elif cls == 'geo':
        phi = '=(1-%s)*%s' % (CR_C, F_C)
    elif cls == 'min':
        phi = '=(1-%s)*%s+%s!I%d*B%d*%s' % (CR_C, F_C, "'1_Inputs'", r, i, FT)
    elif cls == 'ccu':
        phi = ('=(1-%s)*%s+%s!H%d*B%d*%s-(%s!F%d-%s*%s!G%d)*B%d'
               % (CR_C, F_C, "'1_Inputs'", r, i, FT,
                  "'1_Inputs'", r, FT, "'1_Inputs'", r, i))
    else:
        phi = '=%s-%s!J%d*(%s/%s)' % (F_C, "'1_Inputs'", r, F_C, F_C)
    if p in CB.CAPTURES:
        el = "='1_Inputs'!D%d*B%d*%s" % (r, i, EF_C)
        steam = '=%s*B%d*%s' % (PEN_C, i, EF_C)
    elif cls == 'cr':
        el = "='1_Inputs'!D%d*(%s/%s)*%s" % (r, F_C, F_C, EF_C)
        steam = '=0'
    else:
        el = "='1_Inputs'!D%d*%s" % (r, EF_C)
        steam = '=0'
    ws.append([p,
               '=(%s*%s)/(%s*%s)' % (T_C, CR_C, T_C, CR_C),
               '=(%s-%s)*%s' % (AUX_C, EXP_C, EF_C),
               steam, el, phi,
               "='1_Inputs'!E%d*B%d" % (r, i),
               "='1_Inputs'!K%d" % r,
               '=SUM(C%d:H%d)' % (i, i),
               "='1_Inputs'!L%d" % r,
               '=I%d-J%d' % (i, i)])
ws.append([])
ws.append(['Max abs difference', '=MAX(MAX(K2:K15),-MIN(K2:K15))'])
ws.append(['Note', 'Every cell in columns B to I is an Excel formula that reads the parameters '
                   'from 1_Inputs. Nothing in this sheet is a pasted component value, so the '
                   'sheet recomputes if any input is changed.'])

# ================= 4. Eq.6 against Eq.2 =================
det = {'fossil_C': np.array([CB.F_NAT]), 'throughput': np.array([CB.T_NAT]),
       'grid_EF': np.array([CB.EF_NAT]), 'capture_rate': np.array([CB.CR]),
       'H2_EF': np.array([1.0]), 'fossil_share': np.array([CB.F_NAT / CB.T_NAT])}
for f in M.FAMILIES: det['elec_mult_' + f] = np.array([1.0])
for p in CB.ORDER: det['rem_mult_' + p] = np.array([1.0])
dA, dB = M.evaluate(det, 'A'), M.evaluate(det, 'B')
ws = sheet('4_Eq2_vs_Eq6',
           ['Pathway', 'Eq.2 deterministic', 'Eq.6 A, all multipliers = 1',
            'Difference (formula)', 'Eq.6 B, all multipliers = 1',
            'B minus A (formula)', 'D_p, expected B minus A', 'Tolerance'],
           [22, 21, 26, 19, 26, 20, 22, 12])
for i, p in enumerate(CB.ORDER, start=2):
    ws.append([p, round(CB.net(p, CB.F_NAT, CB.T_NAT, CB.EF_NAT), 10),
               round(float(dA[p][0]), 10), '=B%d-C%d' % (i, i),
               round(float(dB[p][0]), 10), '=E%d-C%d' % (i, i),
               CB.D_P.get(p, 0.0), 1e-9])
ws.append([])
ws.append(['Max abs difference', '=MAX(MAX(D2:D15),-MIN(D2:D15))'])
ws.append(['Interpretation', 'Eq.2 and Eq.6 are one model written in two groupings. '
                             'A non-zero value in column D would mean they are not.'])

# ================= 5. Shapley =================
D = ['grid50', 'waste50', 'h2_50']
COMBOS = list(itertools.product([False, True], repeat=3))
ws = sheet('5_Shapley',
           ['Pathway'] + ['g%dw%dh%d' % (c[0], c[1], c[2]) for c in COMBOS] +
           ['Total change (formula)', 'Shapley grid', 'Shapley waste', 'Shapley H2',
            'Sum (formula)', 'Closure (formula)'],
           [22] + [13] * 8 + [19, 14, 15, 14, 15, 16])
for i, p in enumerate(CB.ORDER, start=2):
    vals = {c: SD.net(p, **dict(zip(D, c))) for c in COMBOS}
    sh = {d: 0.0 for d in D}
    for o in itertools.permutations(D):
        S = set()
        for d in o:
            b = tuple(x in S for x in D); S.add(d); a = tuple(x in S for x in D)
            sh[d] += vals[a] - vals[b]
    for d in D: sh[d] /= 6.0
    ws.append([p] + [round(vals[c], 6) for c in COMBOS] +
              ['=I%d-B%d' % (i, i), round(sh['grid50'], 6), round(sh['waste50'], 6),
               round(sh['h2_50'], 6), '=SUM(K%d:M%d)' % (i, i), '=J%d-N%d' % (i, i)])
ws.append([])
ws.append(['Max abs closure', '=MAX(MAX(O2:O15),-MIN(O2:O15))'])

# ================= 6. Regional, all 130 absolute cells =================
regs = RV.load()
ws = sheet('6_Regional_130',
           ['Pathway', 'Region', 'EF_r', 'F_r', 'T_r', 's_cap', 'b_fix',
            'b_steam + b_el', 'phi', 'Q_sub inside phi', 'b_h2', 'C_p residual',
            'Absolute (formula)', 'Reference', 'Relative kt (formula)',
            'Fig.3 displayed kt', 'Discrepancy (formula)'],
           [9, 10] + [12] * 15)
i = 2
for p in CB.ORDER:
    for n in sorted(regs):
        r = regs[n]
        sc = CB.s_cap(r['T'], CB.CR)
        bf, bs, be, phi, bh = CB.terms(p, r['F'], r['T'], r['EF'])
        if CB.CLASS[p] == 'ccu':
            q = -(CB.QA[p] - (r['F'] / r['T']) * CB.QB[p]) * sc
        else:
            q = 0.0
        ref = CB.net('S0', r['F'], r['T'], r['EF'])
        rel = CB.net(p, r['F'], r['T'], r['EF']) - ref
        ws.append([p, n, r['EF'], round(r['F'], 4), round(r['T'], 4), round(sc, 8),
                   round(bf, 6), round(bs + be, 6), round(phi, 6), round(q, 6),
                   round(bh, 6), round(CB.residual(p), 6),
                   '=SUM(G%d:I%d,K%d:L%d)' % (i, i, i, i), round(ref, 6),
                   '' if p == 'S0' else '=(M%d-N%d)/1000' % (i, i),
                   '' if p == 'S0' else round(rel / 1000, 3),
                   '' if p == 'S0' else '=ABS(O%d-P%d)' % (i, i)])
        i += 1
ws.append([])
ws.append(['Max discrepancy kt', '', '=MAX(Q2:Q%d)' % (i - 1)])

# ================= 7. Provenance =================
ws = sheet('7_Provenance', ['Item', 'Value'], [34, 104])
for k, v in [
 ('Deterministic model', 'carbon_model.py; constants from model_parameters.json, generated by '
                         'derive_parameters.py from the source workbooks with per-cell assertions'),
 ('Monte Carlo model', 'monte_carlo.py; master matrix generated by monte_carlo.build_master'),
 ('Scenario decomposition', 'scenario_decomposition.py'),
 ('Regional data loader', 'regional_model.py; regional input data loaded directly from region_waste_carbon.csv'),
 ('Machine-readable exports', 'export_files.py'),
 ('This workbook', 'build_workbook.py'),
 ('Python', sys.version.split()[0] + ' on ' + platform.platform()),
 ('numpy', np.__version__),
 ('openpyxl', __import__('openpyxl').__version__),
 ('Random seed', M.SEED),
 ('Number of draws', M.N),
 ('Draw identifiers', '0 to %d, unique, no gaps' % (M.N - 1)),
 ('Grid factors', 'MoEJ/METI utility-level basic emission factors, ten former general utilities'),
 ('Waste composition', 'national 47-prefecture waste-characterisation survey'),
 ('Reproduce', 'python run_all.py (runs the full chain), or step by step: python carbon_model.py; '
               'python monte_carlo.py; python export_files.py; python build_workbook.py'),
 ('Float tolerance', '1e-9 t-CO2/y for the Eq.2 vs Eq.6 check; 1e-12 relative for rank ties'),
 ('Output mapping', '1_Inputs and 3_Eq2_national -> Eq. 2 of the main text, recomputed with Excel formulas; '
                    '2_Term_classification -> SI Table S6; '
                    '6_Regional_130 -> SI Tables S22 and S23 and Fig3_source_data.csv; '
                    '5_Shapley -> Table 2 of the main text and SI Table S11; '
                    '4_Eq2_vs_Eq6 -> SI Table S12; '
                    'C_p decomposition -> SI Table S8'),
]:
    ws.append([k, str(v)])

out = os.path.join(HERE, 'outputs', 'Unified_calculation_workbook.xlsx')
wb.save(out)
print('saved', out)
for s_ in wb.sheetnames:
    print('  %-24s %4d rows' % (s_, wb[s_].max_row))
