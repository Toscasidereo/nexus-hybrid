# ==============================================================================
# NEXUS LAB-V7 — COMPATIBILIDAD DE CEREBROS: Fase 4 lab (export) -> EA_V12.01_LAB.txt (código real compilado con g++)
# Carpeta: lab_v7/
# ==============================================================================
# BITÁCORA
#   V0.1 (2026-11-06) — Creación. Orden del CRO: "comprobar bit a bit, adaptar el EA para que acepte los cerebros".
#   Reglas fijadas antes de correr (cada una es booleana; pasa solo si todas lo son):
#     C1 el bloque exportado por `_bloque_mql5` (long y short; tamaño off/A/B) COMPILA tal cual dentro de un arnés C++ que contiene las
#        definiciones REALES de structs y enums extraídas del EA (-Wall -Werror): todo campo, índice, tipo y enum existe.
#     C2 Cada asignación a w[], w_T[], w_superv[], tam_w/mu/sd[] cubre exactamente los índices que el EA lee (10, 10, n_features, 11).
#     C3 La escala de tamaño: `LabEscalaTamano` y `LabActividad` del EA (texto real, compilado) == `escala_desde_parametros` / `lab_actividad_nb`
#        de Python, bit a bit, con los parámetros leídos del TEXTO exportado (ya redondeado a DEC_W).
#     C4 T_pred: la expresión del EA (texto real, compilada) == la expresión del kernel Python, bit a bit (ambas con los pesos del texto).
#        Si no, se mide cuántas comparaciones `T_pred < K_abortar` cambian de signo (informe, no se oculta).
#     C5 Efecto del redondeo del export: diferencia entre la escala/T_pred con parámetros sin redondear (entrenamiento) y redondeados (EA).
#   V0.2 (2026-11-07, lab-v8) — C6: `CalcularVida3Vivo` del EA (texto real, g++) == `v3_vivo_nb` (numba) bit a bit, con las constantes leídas del bloque exportado
#        (long y short); sin V3P el bloque no contiene campos `vida_*`. C1 de tamaño off/A/B no cambia.
#   Uso: python lab_v7/lab_compat_ea.py  -> escribe lab_v7/lab_compat_ea_resultados.json
# ==============================================================================
import os, sys, re, json, subprocess, tempfile
import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(AQUI, '..'))
sys.path.insert(0, RAIZ); sys.path.insert(0, AQUI)
import Fase_4_lab as L
import Fase_4_5_lab_A as L45
from lab_escala import escala_desde_parametros, lab_actividad_nb

EA = os.environ.get('NEXUS_EA_LAB', os.path.join(AQUI, 'EA_V12.01_LAB.txt'))
TXT = open(EA, encoding='utf-8', errors='replace').read()
PM = 10000.0
out = {}


def extraer_struct(nombre):
    m = re.search(r'struct\s+' + nombre + r'\s*\{.*?\n\};', TXT, re.S)
    return m.group(0) if m else None


def extraer_funcion(firma_regex):
    m = re.search(firma_regex, TXT)
    i = TXT.index('{', m.start()); d = 0
    for j in range(i, len(TXT)):
        d += (TXT[j] == '{') - (TXT[j] == '}')
        if d == 0:
            return TXT[m.start():j + 1]
    return None


ENUMS = "\n".join(l for l in TXT.splitlines() if re.match(r'\s*enum\s+ENUM_(MARCO_FSM|RESOLUCION_FSM|METRICA_BASE|METRICA_ACUMULADOR)\b', l))
STRUCTS = "\n".join(extraer_struct(n) for n in ('CerebroML', 'CerebroSuperv', 'ConfigMotor')) + "\nstruct ConfigPar { bool configurado; ConfigMotor toro; ConfigMotor oso; };"
F_ESC = extraer_funcion(r'double\s+LabEscalaTamano\s*\(').replace('double &X[]', 'const double *X')
F_ACT = extraer_funcion(r'double\s+LabActividad\s*\(')
SHIM = r'''
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>
#define MathAbs fabs
using std::string;
static std::vector<double> OP; static long NOWI = 0; static int TF_Accion = 0;
static double iOpen(const std::string&, int, int shift) { long k = NOWI - shift; return (k >= 0 && k < (long)OP.size()) ? OP[k] : 0.0; }
'''


def bloque(c_extra, tam, escalon_n, lado):
    cfg, ml, sv = ('toro', 'ml_toro', 'superv_toro') if lado == 'L' else ('oso', 'ml_oso', 'superv_oso')
    g = np.random.default_rng(5 if lado == 'L' else 6)
    row = {'Fold': 1, 'Rank': 1, '⚖️ BASE IN': 'FPP_MID_60', '📊 ACUM IN': 'Z20_FPP_MID_60', '⚙️ Arm_IN': '35%', '⚡ Chq_IN': '70%',
           '⚖️ BASE OUT': 'INT_V_FAST_30', '📊 ACUM OUT': 'INT_V_FAST_30'.replace('INT_V_FAST_30', 'Z30_INT_V_FAST_30'), '⚙️ Arm_OUT': '40%', '⚡ Chq_OUT': '65%'}
    c = {'row': row, 'W_R': g.normal(0, 1, 10), 'B_R': float(g.normal()), 'W_S': g.normal(0, 0.3, 10), 'B_S': float(g.normal(0.4, 0.1)),
         'K_opt': 0.31234, 'W_T': g.normal(0, 1, 10), 'B_T': float(g.normal()), 'T_min': 0.55, 'med_v': 0.7, 'mad_v': 0.4, 'atrac_t': 30.0,
         'ClaveRank': 1.0, 'ScoreFlujo': 2.0, 'Med_T_OOS': 0.5, 'TAM': tam}
    c.update(c_extra)
    return L._bloque_mql5(c, 0, 'LONG' if lado == 'L' else 'SHORT', cfg, ml, sv, 'X', 0.5), c


def compilar(src, nombre):
    d = tempfile.mkdtemp(prefix='compat_'); cpp = os.path.join(d, nombre + '.cpp'); exe = os.path.join(d, nombre)
    open(cpp, 'w').write(src)
    r = subprocess.run(['g++', '-std=c++17', '-O1', '-ffp-contract=off', '-fno-fast-math', '-Wall', '-Werror', '-Wno-unused-variable',
                        '-Wno-unused-function', '-Wno-unused-result', cpp, '-o', exe], capture_output=True, text=True)
    return r.returncode == 0, r.stderr[:1500], exe, d


# --- parámetros de tamaño realistas (mismo procedimiento que L8) -------------------------------------------------------------------------------
gg = np.random.default_rng(21); Nn = 4000
op = 1.10 + np.cumsum(gg.normal(0, 0.8, Nn)) / PM
ACT = lab_actividad_nb(op, PM, 60)
idec = np.sort(gg.choice(np.arange(120, 1900), 150, replace=False)); X8 = gg.normal(0, 1, (3500 - 100, 10))
df8 = pd.DataFrame(X8[idec - 100], columns=L.COLS_X_ENTRADA)
df8['MFE_Pips'] = 5 + 2 * df8.iloc[:, 0] + np.abs(gg.normal(0, 1, 150)) + 3; df8['Idx_Decision'] = idec - 100
PARS = {}
for modo in ('A', 'B'):
    par = {}; L.lab_escala_v(modo, False, np.random.default_rng(1), Nn, 100, 2000, 2000, 3500, df8, ACT, X8 if modo == 'A' else None, par); PARS[modo] = par

# --- C1 / C2: compilación del bloque exportado -----------------------------------------------------------------------------------------------
c1 = {}; c2 = {}
for nom_tam, tam in (('off', None), ('A', PARS['A']), ('B', PARS['B'])):
    for lado in ('L', 'S'):
        bl, _ = bloque({}, tam, 8, lado)
        src = SHIM + ENUMS + "\n" + STRUCTS + "\nstruct Par { ConfigPar cfg; CerebroML ml_toro, ml_oso; CerebroSuperv superv_toro, superv_oso; };\nstatic Par g_pares[1];\n" \
              "void cargar() { int idx = 0;\n" + bl + "\n}\nint main() { cargar(); return 0; }\n"
        ok, err, exe, _d = compilar(src, f'blk_{nom_tam}_{lado}')
        c1[f'compila_tam_{nom_tam}_{lado}'] = bool(ok)
        if not ok: c1[f'error_tam_{nom_tam}_{lado}'] = err
        idx_w = lambda campo: sorted(int(k) for k in re.findall(re.escape(campo) + r'\[(\d+)\]\s*=', bl))
        c2[f'w_10_{nom_tam}_{lado}'] = bool(idx_w('.w') == list(range(10)))
        c2[f'w_T_10_{nom_tam}_{lado}'] = bool(idx_w('.w_T') == list(range(10)))
        c2[f'w_superv_{nom_tam}_{lado}'] = bool(idx_w('.w_superv') == list(range(L.N_FEAT_SUPERV)))
        if nom_tam == 'A':
            for k in ('tam_w', 'tam_mu', 'tam_sd'):
                c2[f'{k}_11_{lado}'] = bool(idx_w('.' + k) == list(range(11)))
        if nom_tam == 'off':
            c2[f'sin_tam_en_off_{lado}'] = bool('tam_' not in bl)
out['C1_bloque_compila_contra_structs_del_EA'] = {'detalle': c1, 'pasa': all(v for k, v in c1.items() if not k.startswith('error'))}
out['C2_cobertura_de_indices'] = {'detalle': c2, 'pasa': all(c2.values())}

# --- C3 / C4 / C5: aritmética real del EA compilada vs Python ----------------------------------------------------------------------------------
m_sw = re.search(r'double T_Pred_Live = \(g_pares\[i\]\.superv_toro\.w_superv\[0\].*?w_superv\[7\] \* inter_FD\);', TXT, re.S)
m_10 = re.search(r'T_Pred_Live \+= \(g_pares\[i\]\.superv_toro\.w_superv\[8\] \* dT\);\s*T_Pred_Live \+= \(g_pares\[i\]\.superv_toro\.w_superv\[9\] \* \(dT \* Theta\)\);', TXT)
m_b = re.search(r'T_Pred_Live \+= g_pares\[i\]\.superv_toro\.b_superv;', TXT)
T_SRC_8 = m_sw.group(0).replace('g_pares[i]', 'g_pares[0]') if m_sw else None
T_SRC_10 = m_10.group(0).replace('g_pares[i]', 'g_pares[0]') if m_10 else None
T_SRC_B = m_b.group(0).replace('g_pares[i]', 'g_pares[0]') if m_b else None
rg = np.random.default_rng(77); NV = 3000
Xr = rg.normal(0, 1, (NV, 10)); fila_i = np.arange(100, 100 + NV)
fid, d_, th, c_, zp, vn, dT = (rg.uniform(0, 1, NV), rg.uniform(0, 1, NV), rg.uniform(0, 1, NV), rg.uniform(0, 1, NV),
                               np.tanh(rg.normal(0, 1, NV)), np.tanh(rg.uniform(0, 3, NV)), rg.uniform(-1, 1, NV))
resultado34 = {}; c3 = {}; c4 = {}; c5 = {}
for nom_tam in ('A', 'B'):
    par = PARS[nom_tam]
    bl, c = bloque({}, par, 10, 'L')
    harness = SHIM + ENUMS + "\n" + STRUCTS + "\nstruct Par { ConfigPar cfg; CerebroML ml_toro, ml_oso; CerebroSuperv superv_toro, superv_oso; };\nstatic Par g_pares[1];\n" \
        + F_ACT + "\n" + F_ESC + "\nvoid cargar() { int idx = 0;\n" + bl + "\n}\n" + r'''
int main(int argc, char** argv) {
   cargar();
   FILE* f = fopen(argv[1], "rb"); int N, M; fread(&N, 4, 1, f); fread(&M, 4, 1, f);
   std::vector<double> X(N * 10), FID(N), D(N), TH(N), CC(N), ZP(N), VN(N), DT(N); std::vector<int> I(N);
   OP.resize(M); fread(OP.data(), 8, M, f); fread(I.data(), 4, N, f); fread(X.data(), 8, N * 10, f);
   fread(FID.data(), 8, N, f); fread(D.data(), 8, N, f); fread(TH.data(), 8, N, f); fread(CC.data(), 8, N, f);
   fread(ZP.data(), 8, N, f); fread(VN.data(), 8, N, f); fread(DT.data(), 8, N, f); fclose(f);
   FILE* o = fopen(argv[2], "wb");
   for (int n = 0; n < N; n++) {
      NOWI = I[n] + 1;                                   // vela cerrada = I[n] (shift 1)
      double act = LabActividad("S", 1, 10000.0);
      double e = LabEscalaTamano(g_pares[0].ml_toro, &X[n * 10], act);
      double Fid = FID[n], D_ = D[n], Theta = TH[n], C_ = CC[n], z_pred_norm = ZP[n], v_ef_norm = VN[n], dT = DT[n];
      double inter_TD = Theta * D_, inter_FD = Fid * D_;
      @@T8@@
      @@T10@@
      @@TB@@
      fwrite(&act, 8, 1, o); fwrite(&e, 8, 1, o); fwrite(&T_Pred_Live, 8, 1, o);
   }
   fclose(o); return 0;
}
'''
    harness = harness.replace('@@T8@@', T_SRC_8 or '#error').replace('@@T10@@', T_SRC_10 or '#error').replace('@@TB@@', T_SRC_B or '#error')
    ok, err, exe, d = compilar(harness, f'cmp_{nom_tam}')
    c3[f'{nom_tam}_arnes_compila'] = bool(ok)
    if not ok:
        c3[f'{nom_tam}_error'] = err; continue
    with open(os.path.join(d, 'in.bin'), 'wb') as f:
        f.write(np.int32(NV).tobytes()); f.write(np.int32(Nn).tobytes()); f.write(op.astype(np.float64).tobytes()); f.write(fila_i.astype(np.int32).tobytes())
        for a in (Xr, fid, d_, th, c_, zp, vn, dT): f.write(np.ascontiguousarray(a, dtype=np.float64).tobytes())
    subprocess.run([exe, os.path.join(d, 'in.bin'), os.path.join(d, 'out.bin')], check=True)
    R = np.fromfile(os.path.join(d, 'out.bin'), dtype=np.float64).reshape(NV, 3)
    act_c, esc_c, tp_c = R[:, 0], R[:, 1], R[:, 2]
    # parámetros leídos del TEXTO exportado
    ptxt = L45.parse_tam('X' + L.lab_bloque_tam('ml_toro', par), 'ml_toro')
    act_py = lab_actividad_nb(op, PM, 60)[fila_i]
    esc_txt = escala_desde_parametros(ptxt, Xr, act_py)
    esc_raw = escala_desde_parametros({**par, 'esc_min': par.get('esc_min', L.ESCALA_MIN), 'esc_max': par.get('esc_max', L.ESCALA_MAX)}, Xr, act_py)
    c3[f'{nom_tam}_actividad_EA_igual_Python'] = bool(np.array_equal(act_c.view(np.int64), act_py.view(np.int64)))
    c3[f'{nom_tam}_escala_EA_igual_Python_con_texto'] = bool(np.array_equal(esc_c.view(np.int64), esc_txt.view(np.int64)))
    dif = np.abs(esc_raw - esc_txt)
    c5[f'{nom_tam}_escala_redondeo_max_abs'] = float(dif.max()); c5[f'{nom_tam}_escala_redondeo_filas_distintas'] = int((dif > 0).sum())
    # T_pred: orden del kernel Python, con pesos del texto (8 decimales)
    txt_w = {k: float(v) for k, v in re.findall(r'w_superv\[\d+\]=([-\d.]+);', bl)} if False else None
    Ws = np.array([float(v) for v in re.findall(r'superv_toro\.w_superv\[\d+\]=([-\d.]+);', bl)])
    Bs = float(re.search(r'superv_toro\.b_superv = ([-\d.]+);', bl).group(1)); Ks = float(re.search(r'superv_toro\.k_abortar = ([-\d.]+);', bl).group(1))
    nf = len(Ws); Wp = np.zeros(10); Wp[:nf] = Ws
    tp_py = (Wp[0]*fid + Wp[1]*d_ + Wp[2]*th + Wp[3]*c_ + Wp[4]*zp + Wp[5]*vn + Wp[6]*(th*d_) + Wp[7]*(fid*d_) + Wp[8]*dT + Wp[9]*(dT*th)) + Bs
    n_feat_ea = int(re.search(r'superv_toro\.n_features = (\d+);', bl).group(1))
    c4[f'{nom_tam}_n_features'] = n_feat_ea
    c4[f'{nom_tam}_T_pred_EA_igual_kernel_Python_bit_a_bit'] = bool(np.array_equal(tp_c.view(np.int64), tp_py.view(np.int64)))
    c4[f'{nom_tam}_T_pred_filas_distintas'] = int((tp_c != tp_py).sum())
    c4[f'{nom_tam}_T_pred_max_abs'] = float(np.abs(tp_c - tp_py).max())
    c4[f'{nom_tam}_cruces_K_distintos'] = int(((tp_c < Ks) != (tp_py < Ks)).sum())
out['C3_escala_EA_compilada_vs_Python'] = {'detalle': c3, 'pasa': all(v for k, v in c3.items() if isinstance(v, bool))}
out['C4_T_pred_EA_compilada_vs_Python'] = {'detalle': c4, 'pasa': bool(sum(k.endswith('bit_a_bit') for k in c4) == 2 and all(v for k, v in c4.items() if k.endswith('bit_a_bit')))}
out['C5_efecto_del_redondeo_de_export'] = {'detalle': c5, 'informativo': True}

# --- C6 [LAB-V8]: Vida v3 vivo del EA compilada vs numba, con las constantes leídas del TEXTO exportado ------------------------------------------
c6 = {}
F_V3 = extraer_funcion(r'double\s+CalcularVida3Vivo\s*\(')
c6['funcion_presente_en_EA'] = bool(F_V3)
if F_V3:
    import vida_v3 as VV
    gv = np.random.default_rng(31)
    v3p0 = np.array([30.0, 3.0, 1.0] + list(gv.uniform(0.3, 0.7, 5)) + list(gv.uniform(0.2, 1.5, 5)) + [0.2] * 5)
    v3p_txt = np.array([float(f"{x:.{L.DEC_W}f}") for x in v3p0])
    NV3 = 4000
    P = gv.normal(0, 3, NV3); MFE = np.abs(gv.normal(4, 3, NV3)) + np.maximum(P, 0); MAE = -np.abs(gv.normal(3, 2, NV3)) + np.minimum(P, 0)
    VEL = gv.integers(1, 60, NV3).astype(np.float64); CNn = np.maximum(VEL - 1.0, 1.0); CGg = np.floor(CNn * gv.uniform(0, 1, NV3))
    MINP = np.minimum(P, -np.abs(gv.normal(1, 1.5, NV3))); VF = np.minimum(VEL, np.floor(gv.uniform(1, 60, NV3))); CS = 1.0
    for lado in ('L', 'S'):
        bl, _ = bloque({'V3P': v3p_txt}, None, 10, lado)
        sv = 'superv_toro' if lado == 'L' else 'superv_oso'
        hv = SHIM + "#define MathMax fmax\n#define MathMin fmin\n#define MathTanh tanh\n" + ENUMS + "\n" + STRUCTS + \
            "\nstruct Par { ConfigPar cfg; CerebroML ml_toro, ml_oso; CerebroSuperv superv_toro, superv_oso; };\nstatic Par g_pares[1];\n" + F_V3 + "\nvoid cargar() { int idx = 0;\n" + bl + "\n}\n" + r"""
int main(int argc, char** argv) {
   cargar(); FILE* f = fopen(argv[1], "rb"); int N; fread(&N, 4, 1, f);
   std::vector<double> A(N*8); fread(A.data(), 8, N*8, f); fclose(f);
   FILE* o = fopen(argv[2], "wb");
   for (int n = 0; n < N; n++) {
      double v = CalcularVida3Vivo(g_pares[0].@@SV@@, A[n*8+0], A[n*8+1], A[n*8+2], A[n*8+3], A[n*8+4], A[n*8+5], A[n*8+6], A[n*8+7], 1.0);
      fwrite(&v, 8, 1, o);
   }
   fclose(o); return 0;
}
""".replace('@@SV@@', sv)
        ok, err, exe, d = compilar(hv, f'v3_{lado}')
        c6[f'{lado}_compila'] = bool(ok)
        if not ok:
            c6[f'{lado}_error'] = err; continue
        A = np.column_stack([P, MFE, MAE, VEL, CGg, CNn, MINP, VF])
        with open(os.path.join(d, 'in.bin'), 'wb') as fh:
            fh.write(np.int32(NV3).tobytes()); fh.write(np.ascontiguousarray(A, dtype=np.float64).tobytes())
        subprocess.run([exe, os.path.join(d, 'in.bin'), os.path.join(d, 'out.bin')], check=True)
        ea_v = np.fromfile(os.path.join(d, 'out.bin'), dtype=np.float64)
        # constantes tal como las ve el EA: texto -> numero
        medtxt = [float(x) for x in re.findall(r'\.vida_med\[\d\]=([-\d.]+);', bl)]
        c6[f'{lado}_texto_trae_5_med_5_esc_5_peso'] = bool(len(medtxt) == 5 and len(re.findall(r'\.vida_esc\[\d\]=', bl)) == 5 and len(re.findall(r'\.vida_peso\[\d\]=', bl)) == 5)
        py_v = np.array([VV.v3_vivo_nb(P[k], MFE[k], MAE[k], VEL[k], CGg[k], CNn[k], MINP[k], VF[k], CS, v3p_txt) for k in range(NV3)])
        c6[f'{lado}_V3_vivo_EA_igual_numba_bit_a_bit'] = bool(np.array_equal(ea_v.view(np.int64), py_v.view(np.int64)))
        c6[f'{lado}_filas_distintas'] = int((ea_v != py_v).sum()); c6[f'{lado}_max_abs'] = float(np.abs(ea_v - py_v).max())
        c6[f'{lado}_bloque_activa_vida'] = bool('vida_activa = true' in bl)
for lado in ('L', 'S'):
    bl0, _ = bloque({}, None, 10, lado)
    c6[f'{lado}_sin_V3P_no_hay_bloque_vida'] = bool('vida_' not in bl0)
out['C6_Vida_v3_vivo_EA_compilada_vs_numba'] = {'detalle': c6, 'pasa': bool(c6.get('funcion_presente_en_EA')) and all(v for k, v in c6.items() if isinstance(v, bool)) and all(c6.get(f'{l}_V3_vivo_EA_igual_numba_bit_a_bit') is not None for l in 'LS')}

out['todas_pasan'] = all(v.get('pasa', True) for v in out.values() if isinstance(v, dict))
json.dump(out, open(os.path.join(AQUI, 'lab_compat_ea_resultados.json'), 'w'), indent=1, ensure_ascii=False, default=str)
print(json.dumps(out, indent=1, ensure_ascii=False, default=str)[:6000])
