"""Alias de ruta para transferencias de archivos SAS/CONNECT."""

from __future__ import annotations

from itertools import islice
from pathlib import Path

import yaml

from sgm.cli_migrar import migrar
from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.models import Graph, Operator, Plan
from sgm.ir.pase_copias_remotas import CopiaRemota, aplicar_copias, copias_remotas
from sgm.seguridad.escaner_secretos import escanear_ruta
from sgm.talend_item.desde_plan_contextos import rutas_de_plan

CLIENTE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "sas"
    / "client"
    / "client_large.sas"
)


def _fragmento(inicio: int, fin: int) -> str:
    """Lee solo el rango pedido del fixture redactado y conserva sus números de línea."""
    with CLIENTE.open(encoding="utf-8") as archivo:
        lineas = "".join(islice(archivo, inicio - 1, fin))
    return "\n" * (inicio - 1) + lineas


def _plan(texto: str) -> Plan:
    analisis = analyze_program({"programa.sas": texto})
    return compile_file(analisis, "programa.sas", project_base()).plan


def _plan_con_operadores(*operadores: Operator) -> Plan:
    grafo = Graph()
    for operador in operadores:
        grafo.add_operator(operador)
    return Plan("programa", graph=grafo)


def test_extrae_descarga_literal_del_fragmento_sas_redactado():
    copias, pendientes = copias_remotas(_fragmento(146, 164))

    assert len(copias) == 1
    assert copias[0].sentido == "download"
    assert copias[0].infile.endswith("Base_datos_Nequi.csv")
    assert copias[0].outfile == "/work_sasstudio/pcfiles/Base_datos_Nequi.csv"
    assert copias[0].linea == 153
    assert pendientes == []


def test_aplicar_descarga_normaliza_rutas_y_contexto_usa_el_origen_remoto():
    copia = CopiaRemota(
        "download",
        r"\\servidor\carpeta\origen.csv",
        "/work/entradas/clientes.csv",
        15,
    )
    lectura = Operator(
        "lectura",
        "read_file",
        {"datafile": r"\WORK\entradas\CLIENTES.csv", "outputs": ["WORK.BASE_CLIENTES_NEQUI"]},
    )
    plan = _plan_con_operadores(lectura)

    plan, pendientes = aplicar_copias(plan, [copia])

    assert pendientes == []
    assert lectura.params["datafile"] == copia.infile
    assert rutas_de_plan(plan) == {copia.infile: "ruta_base_clientes_nequi"}


def test_upload_real_reemplaza_la_salida_local_por_el_destino_remoto():
    texto = _fragmento(24263, 24278)
    copias, pendientes = copias_remotas(texto)
    plan = _plan(texto)
    escritura = next(op for op in plan.graph.operators() if op.kind == "write_file")

    plan, sin_efecto = aplicar_copias(plan, copias)

    assert len(copias) == 1
    assert copias[0].sentido == "upload"
    assert copias[0].linea == 24274
    assert escritura.params["outfile"].startswith("\\\\sbcldwpsgf01\\")
    assert "FA_NO_VIGENTES_AHO.csv" in escritura.params["outfile"]
    assert pendientes == sin_efecto == []
    assert rutas_de_plan(plan)[escritura.params["outfile"]] == "ruta_fa_no_vigentes_aho"


def test_macrovariables_y_copias_de_dataset_quedan_pendientes_sin_reflejar_secretos():
    texto = (
        "signon user=u pass='***';\n"
        'proc upload infile="&dir./a.csv" outfile="/x/a.csv";\n'
        "proc download data=base.tabla out=work.tabla;\n"
    )

    copias, pendientes = copias_remotas(texto)

    assert copias == []
    assert [p.codigo for p in pendientes] == [
        "P-COPIA-REMOTA-DINAMICA",
        "P-COPIA-REMOTA-DATASET",
    ]
    assert all("***" not in p.mensaje and "pass" not in p.mensaje.lower() for p in pendientes)


def test_copia_sin_operador_coincidente_informa_su_linea():
    copia = CopiaRemota("download", "/servidor/entrada.csv", "/local/entrada.csv", 9)
    plan, pendientes = aplicar_copias(_plan_con_operadores(), [copia])

    assert plan.graph.operators() == []
    assert len(pendientes) == 1
    assert pendientes[0].codigo == "P-COPIA-REMOTA-SIN-EFECTO"
    assert pendientes[0].linea == 9


def test_migrar_contexto_default_conserva_la_ruta_remota_sin_hallazgos(tmp_path):
    texto = _fragmento(146, 164)
    programa = tmp_path / "programa.sas"
    programa.write_text(texto, encoding="utf-8")

    resultado = migrar(programa, tmp_path / "out")

    contexto = yaml.safe_load(
        (resultado.carpeta / "contextos" / "Default.yaml").read_text(encoding="utf-8")
    )
    variables = {v["nombre"]: v["valor"] for v in contexto["variables"]}
    assert variables["ruta_base_clientes_nequi"].startswith("\\\\sbcldwpsgf01\\")
    assert "Base_datos_Nequi.csv" in variables["ruta_base_clientes_nequi"]
    assert not escanear_ruta(resultado.carpeta).hallazgos


def test_no_detecta_proc_dentro_de_comentarios_o_cadenas():
    texto = "/* proc upload infile='a' outfile='b'; */\n"
    texto += 'x = "proc download infile=\'c\' outfile=\'d\'";\n'

    copias, pendientes = copias_remotas(texto)

    assert copias == []
    assert pendientes == []


def test_transferencia_sin_infile_u_outfile_no_tumba_el_analisis():
    try:
        copias, pendientes = copias_remotas('proc upload infile="/cliente/a.csv";')
        resultado = (copias, [p.codigo for p in pendientes])
    except Exception as error:  # el parser debe dejar pendiente, no interrumpir la migración
        resultado = type(error).__name__

    assert resultado == ([], ["P-COPIA-REMOTA-INCOMPLETA"])
