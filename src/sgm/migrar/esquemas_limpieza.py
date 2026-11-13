"""Limpieza posicional de comentarios y cadenas SAS para detectar escrituras."""


def mascara_codigo(texto: str) -> str:
    """Oculta comentarios y cadenas conservando longitud y saltos de línea."""
    salida = list(texto)
    i = 0
    inicio = True
    while i < len(texto):
        fin = i
        if texto.startswith("/*", i):
            cierre = texto.find("*/", i + 2)
            fin = len(texto) if cierre < 0 else cierre + 2
        elif inicio and (texto[i] == "*" or texto.startswith("%*", i)):
            cierre = texto.find(";", i)
            fin = len(texto) if cierre < 0 else cierre + 1
        elif texto[i] in "'\"":
            comilla = texto[i]
            fin = i + 1
            while fin < len(texto):
                if texto[fin] == comilla:
                    if fin + 1 < len(texto) and texto[fin + 1] == comilla:
                        fin += 2
                        continue
                    fin += 1
                    break
                fin += 1
            inicio = False
        if fin > i:
            for j in range(i, fin):
                if texto[j] not in "\r\n":
                    salida[j] = " "
            i = fin
            continue
        if texto[i] == ";":
            inicio = True
        elif not texto[i].isspace():
            inicio = False
        i += 1
    return "".join(salida)
