"""Capa de hechos: trazabilidad, catálogo cerrado, credenciales, determinismo y casos mínimos."""

from __future__ import annotations

import json
from pathlib import Path

from sgm.facts.model import MASK, TIPOS, alcance_de
from sgm.facts.project import facts_for_project

ROOT = Path(__file__).resolve().parents[2]
CLIENT_LARGE = ROOT / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"


def _hechos(texto: str, nombre: str = "programa.sas") -> list:
    return facts_for_project({nombre: texto})[nombre]


def _por_tipo(hechos: list, tipo: str) -> list:
    return [h for h in hechos if h.tipo == tipo]


def test_hechos_tienen_fuente_dentro_del_archivo() -> None:
    texto = CLIENT_LARGE.read_text(encoding="utf-8-sig", errors="replace")
    total_lineas = len(texto.splitlines())
    hechos = facts_for_project({"client_large.sas": texto})["client_large.sas"]
    assert len(hechos) > 1000
    for h in hechos:
        assert 1 <= h.linea_inicio <= h.linea_fin <= total_lineas, h.id


def test_tipos_estan_en_el_catalogo() -> None:
    texto = CLIENT_LARGE.read_text(encoding="utf-8-sig", errors="replace")
    hechos = facts_for_project({"client_large.sas": texto})["client_large.sas"]
    assert {h.tipo for h in hechos} <= TIPOS


def test_credenciales_salen_enmascaradas() -> None:
    texto = "proc sql;\nconnect to impala (dsn=IMPALA user=ana password='secreto-123');\nquit;\n"
    hechos = _hechos(texto)
    creds = _por_tipo(hechos, "credencial")
    assert creds and all(h.valor == MASK for h in creds)
    assert "secreto-123" not in json.dumps([h.to_dict() for h in hechos])


def test_determinismo_mismo_resultado_dos_veces() -> None:
    texto = CLIENT_LARGE.read_text(encoding="utf-8-sig", errors="replace")
    a = facts_for_project({"x.sas": texto})["x.sas"]
    b = facts_for_project({"x.sas": texto})["x.sas"]
    assert [h.to_dict() for h in a] == [h.to_dict() for h in b]


def test_data_step_lee_y_escribe_con_alcance_work() -> None:
    hechos = _hechos("data work.a;\nset work.b;\nrun;\n")
    escritas = {(h.valor, h.alcance) for h in _por_tipo(hechos, "tabla_escrita")}
    leidas = {(h.valor, h.alcance) for h in _por_tipo(hechos, "tabla_leida")}
    assert ("work.a", "work") in escritas
    assert ("work.b", "work") in leidas


def test_proc_sql_create_table_as_select() -> None:
    texto = "proc sql;\ncreate table work.c as select * from work.d;\nquit;\n"
    hechos = _hechos(texto)
    assert any(h.tipo == "tabla_escrita" and h.valor == "work.c" for h in hechos)
    assert any(h.tipo == "tabla_leida" and h.valor == "work.d" for h in hechos)


def test_biblioteca_permanente_no_es_work() -> None:
    assert alcance_de("lib.tabla", set()) == "permanente"
    assert alcance_de("tabla", set()) == "work"
    assert alcance_de("ext.tabla", {"ext"}) == "externo"


def test_nombre_con_macro_variable_se_marca_dinamico() -> None:
    # Una variable constante se expande a su valor; una dinámica no, y su nombre queda marcado.
    texto = "%let t=%sysfunc(today());\ndata work.&t;\nset work.b;\nrun;\n"
    hechos = _hechos(texto)
    dinamicas = [h for h in _por_tipo(hechos, "tabla_escrita") if "&" in h.valor]
    assert dinamicas and all(h.detalle.get("dinamico") == "si" for h in dinamicas)


def test_macro_y_let_se_observan() -> None:
    texto = "%let ruta=abc;\n%macro m(p);\n%mend m;\n%m(1);\n"
    hechos = _hechos(texto)
    assert any(h.tipo == "variable_constante" and h.valor == "ruta" for h in hechos)
    assert any(h.tipo == "macro_definida" and h.valor == "m" for h in hechos)
    assert any(h.tipo == "macro_llamada" and h.valor == "m" for h in hechos)


def _lineas_con_estructura(texto: str) -> set[int]:
    """Líneas cubiertas por algún paso o sentencia del texto (incluido el cuerpo de macros)."""
    from sgm.frontend.lexer import split_statements
    from sgm.frontend.steps import MacroDef, parse_steps

    stmts = split_statements(texto)
    steps, _ = parse_steps(stmts)
    cubiertas: set[int] = set()
    for s in stmts:
        cubiertas.update(range(s.line, s.end_line + 1))

    def recorre(pasos: list[object]) -> None:
        for paso in pasos:
            inicio = getattr(paso, "line", None)
            if inicio:
                cubiertas.update(range(inicio, (getattr(paso, "end_line", inicio) or inicio) + 1))
            for st in getattr(paso, "statements", None) or []:
                if getattr(st, "line", None):
                    cubiertas.add(st.line)
            if isinstance(paso, MacroDef):
                recorre(paso.body)

    recorre(steps)
    return cubiertas


def _lineas_con_contenido(texto: str) -> list[int]:
    en_comentario = False
    numeros = []
    for n, linea in enumerate(texto.splitlines(), 1):
        s = linea.strip().replace("​", "")
        if en_comentario or s.startswith(("/*", "*")):
            en_comentario = "*/" not in s
            continue
        if "/*" in s and "*/" not in s:
            en_comentario = True
        if s and s != ";":
            numeros.append(n)
    return numeros


def test_cada_linea_con_contenido_esta_en_un_paso() -> None:
    texto = CLIENT_LARGE.read_text(encoding="utf-8-sig", errors="replace").replace("​", "")
    cubiertas = _lineas_con_estructura(texto)
    sin_cubrir = [n for n in _lineas_con_contenido(texto) if n not in cubiertas]
    assert sin_cubrir == []


def test_archivos_hostiles_no_lanzan_excepciones() -> None:
    casos = {
        "vacio.sas": "",
        "sin_cerrar.sas": "%macro a;\ndata work.x;\nset work.y;\n",
        "comillas.sas": "proc sql;\nconnect to x (password='abc);\nquit;\n",
        "binario.sas": "\x00\x01\x02 data \xff\xfe",
        "solo_comentario.sas": "/* nada */\n",
    }
    resultado = facts_for_project(casos)
    assert set(resultado) == set(casos)
