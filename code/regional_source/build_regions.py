"""
Regional dataset builder — Japan, 47 prefectures -> 10 grid regions.

SUPERSEDED IN REVISION R1e (2026-09-20).  This script builds the SUBMITTED regional layer from our
earlier compilation of the MoEJ survey, of which 14 of 47 prefecture profiles cannot be rebuilt
from the raw facility table by any recorded rule.  The revision uses the transparent rebuild
R1_revision/02_analyses/R1e_regional/build_R1e.py (raw files in R1_revision/03_new_sources/
MoEJ_FY2021/).  This script now refuses to overwrite the R1e prefecture table; its output is
kept as prefecture_waste_carbon_submitted.csv and region_waste_carbon_unweighted.csv.  The text
below describes the submitted build.

Source: 全国ごみ性状分析　導入効果把握.xlsb (our compilation of the MoEJ national
waste survey, fiscal year 2021), sheet 日本全国ごみ性状
        = MoEJ national waste-characterization survey, dry-basis composition by
        prefecture, plus elemental composition (C/H/O/N/S/Cl) per fraction from
        sheet co2排出量計算ツール (東京都清掃研究所 研究報告第28号; 三鷹市・調布市).

VALIDATION (see verify block at end): the unweighted 47-prefecture mean composition
reproduces the manuscript's national baseline (paper 48.7 vs 49, plastic 24.0 vs 24,
wood 10.0 vs 10, kitchen 11.7 vs 12) and the implied fossil-carbon share (34-36%)
brackets the manuscript value 35.5% (=26,475/74,621 t-CO2/y). The regional layer is
therefore an expansion of the same basis, not a new one.

DATA HANDLING: 'その他' is defined in the source methodology as a back-calculated
residual (その他: 可燃ごみ全体から逆算により算出). Three prefectures (岩手, 新潟, 宮崎)
carry an inconsistent tabulated residual (sum > 101.5%); for these the residual is
recomputed as 100 - sum(other five fractions), per the source's own definition.
"""
import openpyxl, csv, os, statistics as st
import argparse

# The source workbook is NOT part of this archive.  Give its path with --src or set
# CCUS_SRC_WASTE.  The shipped prefecture_waste_carbon.csv is the output of this
# script and is what the default calculation chain reads; re-running this script is
# an optional provenance step for the authors, exactly like derive_parameters.py.
# The original file is distributed as .xlsb; openpyxl reads only .xlsx, so convert
# the sheet 日本全国ごみ性状 to .xlsx once before running.
_ap = argparse.ArgumentParser(description=__doc__)
_ap.add_argument('--src', default=os.environ.get('CCUS_SRC_WASTE'),
                 help='national waste-characterization workbook, .xlsx '
                      '(or set CCUS_SRC_WASTE)')
_A, _ = _ap.parse_known_args()
SRC = _A.src
HERE = os.path.dirname(os.path.abspath(__file__))
if not SRC or not os.path.exists(SRC):
    raise SystemExit(
        'build_regions.py: the national waste-characterization workbook is not '
        'available; give it with --src PATH or set CCUS_SRC_WASTE. '
        'This script is an optional provenance step; the calculation chain reads '
        'the shipped prefecture_waste_carbon.csv and does not need it.')

# Elemental carbon content, dry basis (source: co2排出量計算ツール sheet)
C_CONTENT = {'paper': 0.4438, 'plas': 0.74, 'kit': 0.467, 'other': 0.56,
             'wood': 0.50}      # wood not tabulated separately; 0.50 typical (biogenic; affects denominator only)
FOSSIL_SHARE_OF_C = {'paper': 0.0, 'plas': 1.0, 'wood': 0.0, 'kit': 0.0,
                     'other': 0.5}   # 'other' mixed; 0/0.5/1.0 tested in sensitivity

# ---- Regional grid emission factors -------------------------------------------
# 基礎排出係数, "(参考値)事業者全体" (company-wide reference value) for each of the ten
# former general electricity utilities, from the official MoEJ/METI list
# 電気事業者別排出係数（特定排出者の温室効果ガス排出量算定用）, file
# r07_denki_coefficient_rev4.pdf, page 9, published at
# https://policies.env.go.jp/earth/ghg-santeikohyo/calc.html
# The same document gives a national average of 0.000423 t-CO2/kWh (p.18), consistent
# with the 0.44 kg-CO2/kWh national figure used for the reference-plant baseline.
GRID_EF = {                       # t-CO2/kWh
 'Hokkaido': 0.000532, 'Tohoku': 0.000385, 'Tokyo': 0.000408, 'Chubu': 0.000393,
 'Hokuriku': 0.000481, 'Kansai': 0.000401, 'Chugoku': 0.000511, 'Shikoku': 0.000454,
 'Kyushu': 0.000402, 'Okinawa': 0.000638,
}
GRID_EF_NATIONAL = 0.000423
# 2050 regional factors are not published. Two transparent treatments are carried:
#   'proportional' — each region scaled by the national 2025->2050 ratio (0.07/0.44)
#   'convergence'  — all regions converge to the national 2050 value (0.07)
# Both are stated as assumptions, not data.
NAT_2025, NAT_2050 = 0.44e-3, 0.07e-3

# 47 prefectures -> 10 electric-utility grid regions
REGION = {
 '北海道':'Hokkaido',
 '青森県':'Tohoku','岩手県':'Tohoku','宮城県':'Tohoku','秋田県':'Tohoku','山形県':'Tohoku',
 '福島県':'Tohoku','新潟県':'Tohoku',
 '茨城県':'Tokyo','栃木県':'Tokyo','群馬県':'Tokyo','埼玉県':'Tokyo','千葉県':'Tokyo',
 '東京都':'Tokyo','神奈川県':'Tokyo','山梨県':'Tokyo',
 '長野県':'Chubu','岐阜県':'Chubu','静岡県':'Chubu','愛知県':'Chubu','三重県':'Chubu',
 '富山県':'Hokuriku','石川県':'Hokuriku','福井県':'Hokuriku',
 '滋賀県':'Kansai','京都府':'Kansai','大阪府':'Kansai','兵庫県':'Kansai','奈良県':'Kansai',
 '和歌山県':'Kansai',
 '鳥取県':'Chugoku','島根県':'Chugoku','岡山県':'Chugoku','広島県':'Chugoku','山口県':'Chugoku',
 '徳島県':'Shikoku','香川県':'Shikoku','愛媛県':'Shikoku','高知県':'Shikoku',
 '福岡県':'Kyushu','佐賀県':'Kyushu','長崎県':'Kyushu','熊本県':'Kyushu','大分県':'Kyushu',
 '宮崎県':'Kyushu','鹿児島県':'Kyushu',
 '沖縄県':'Okinawa',
}

def load():
    ws = openpyxl.load_workbook(SRC, data_only=True, read_only=True)['日本全国ごみ性状']
    out = []
    for r in ws.iter_rows(min_row=1, max_row=80, values_only=True):
        if not r[1] or not isinstance(r[3], (int, float)):
            continue
        d = dict(pref=str(r[1]).strip(), paper=r[3], plas=r[4], wood=r[5], kit=r[6],
                 inert=r[7], other=r[8], density=r[9], moisture=r[11])
        five = d['paper'] + d['plas'] + d['wood'] + d['kit'] + d['inert']
        d['residual_fixed'] = False
        if abs(five + d['other'] - 100) > 1.5:            # inconsistent tabulated residual
            d['other'] = max(0.0, 100.0 - five)           # recompute per source definition
            d['residual_fixed'] = True
        tot = five + d['other']
        for k in ('paper', 'plas', 'wood', 'kit', 'inert', 'other'):
            d[k] = d[k] * 100.0 / tot                     # normalise to 100%
        out.append(d)
    return out

def carbon(d, f_other=0.5):
    """Return (total C, fossil C) per 100 kg dry combustible waste."""
    totC = sum(d[k] * C_CONTENT[k] for k in ('paper', 'plas', 'wood', 'kit', 'other'))
    fosC = (d['plas'] * C_CONTENT['plas'] * FOSSIL_SHARE_OF_C['plas']
            + d['other'] * C_CONTENT['other'] * f_other)
    return totC, fosC

def main():
    prefs = load()
    assert len(prefs) == 47, f'expected 47 prefectures, got {len(prefs)}'
    assert all(p['pref'] in REGION for p in prefs), \
        [p['pref'] for p in prefs if p['pref'] not in REGION]

    for p in prefs:
        p['region'] = REGION[p['pref']]
        totC, fosC = carbon(p)
        p['C_total'] = totC
        p['C_fossil'] = fosC
        p['fossil_share'] = 100 * fosC / totC
        # CO2 per t of (dry) waste: C x 44/12, /100 because composition is in %
        p['CO2_total_t_per_t'] = totC / 100 * 44 / 12
        p['CO2_fossil_t_per_t'] = fosC / 100 * 44 / 12

    # ---- prefecture CSV ----
    fp = os.path.join(HERE, 'prefecture_waste_carbon.csv')
    # R1e guard: the prefecture and region tables of the revision come from the transparent rebuild
    # (R1_revision/02_analyses/R1e_regional/build_R1e.py); this script would write the submitted,
    # partly untraceable compilation back over them.
    if os.path.exists(fp) and 'n_facilities' in open(fp, encoding='utf-8-sig').readline():
        raise SystemExit('build_regions.py refused: prefecture_waste_carbon.csv is the R1e rebuild; '
                         'the submitted compilation is kept as prefecture_waste_carbon_submitted.csv')
    with open(fp, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['prefecture', 'region', 'paper_pct', 'plastic_pct', 'wood_pct',
                    'kitchen_pct', 'inert_pct', 'other_pct', 'moisture_pct',
                    'fossil_share_of_C_pct', 'CO2_total_t_per_t_dry',
                    'CO2_fossil_t_per_t_dry', 'residual_recomputed'])
        for p in sorted(prefs, key=lambda x: x['region']):
            w.writerow([p['pref'], p['region']] +
                       [round(p[k], 2) for k in ('paper', 'plas', 'wood', 'kit', 'inert',
                                                 'other', 'moisture', 'fossil_share')] +
                       [round(p['CO2_total_t_per_t'], 4), round(p['CO2_fossil_t_per_t'], 4),
                        p['residual_fixed']])

    # ---- region CSV (unweighted mean of member prefectures) ----
    regs = {}
    for p in prefs:
        regs.setdefault(p['region'], []).append(p)
    fr = os.path.join(HERE, 'region_waste_carbon.csv')
    with open(fr, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['region', 'n_prefectures', 'plastic_pct', 'moisture_pct',
                    'fossil_share_of_C_pct', 'CO2_total_t_per_t_dry',
                    'CO2_fossil_t_per_t_dry',
                    'grid_EF_2025_tCO2_per_kWh', 'grid_EF_2050_proportional',
                    'grid_EF_2050_convergence'])
        print(f"\n{'region':<10}{'n':>3}{'plastic%':>10}{'fossilC%':>10}"
              f"{'CO2fos':>9}{'gridEF':>10}{'rel.nat':>9}")
        for reg, ms in sorted(regs.items()):
            m = lambda k: st.mean([x[k] for x in ms])
            ef = GRID_EF[reg]
            w.writerow([reg, len(ms), round(m('plas'), 2), round(m('moisture'), 2),
                        round(m('fossil_share'), 2), round(m('CO2_total_t_per_t'), 4),
                        round(m('CO2_fossil_t_per_t'), 4), ef,
                        round(ef * NAT_2050 / NAT_2025, 8), NAT_2050])
            print(f"{reg:<10}{len(ms):>3}{m('plas'):>10.1f}{m('fossil_share'):>10.1f}"
                  f"{m('CO2_fossil_t_per_t'):>9.3f}{ef*1000:>10.3f}"
                  f"{ef/GRID_EF_NATIONAL:>9.2f}")

    # ---- validation against manuscript baseline ----
    nat = {k: st.mean([p[k] for p in prefs]) for k in ('paper', 'plas', 'wood', 'kit')}
    natC = st.mean([p['fossil_share'] for p in prefs])
    print('\nVALIDATION vs manuscript baseline')
    print(f"  composition  paper {nat['paper']:.1f}/49  plastic {nat['plas']:.1f}/24  "
          f"wood {nat['wood']:.1f}/10  kitchen {nat['kit']:.1f}/12")
    print(f"  fossil share of combustion C: {natC:.1f}%  (manuscript 35.5%)")
    for fo in (0.0, 0.5, 1.0):
        v = st.mean([100 * carbon(p, fo)[1] / carbon(p, fo)[0] for p in prefs])
        print(f"    sensitivity, 'other' fossil={fo:.0%}: {v:.1f}%")
    fs = sorted(prefs, key=lambda p: p['fossil_share'])
    print(f"  regional spread: {fs[0]['pref']} {fs[0]['fossil_share']:.1f}% -> "
          f"{fs[-1]['pref']} {fs[-1]['fossil_share']:.1f}%  (sd "
          f"{st.stdev([p['fossil_share'] for p in prefs]):.1f} pp)")
    print(f"  residual recomputed for: "
          f"{[p['pref'] for p in prefs if p['residual_fixed']]}")
    print(f"\nwrote {fp}\nwrote {fr}")

if __name__ == '__main__':
    main()
