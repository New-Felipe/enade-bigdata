"""Recuperacao de questoes objetivas com imagem incorporada."""
from pathlib import Path
import pymupdf
from extractor.localizacao_alternativas import (
    localizar_grupos_alternativas,
)
from extractor.normalizacao_ocr import normalizar_quebras_ocr
from extractor.ocr import extrair_regiao_ocr
from extractor.recuperacao_alternativas_ocr import (
    recuperar_alternativas_ocr,
)
from extractor.recuperacao_imagens_enunciado import (
    anexar_imagem_incorporada_enunciado,
)
from extractor.segmenter import identificar_titulo_ocr
def recuperar_questao_com_imagem_incorporada(
    plano,
    caminho_pdf,
    arquivo_origem,
    executavel_tesseract,
    pasta_saida,
    altura_ultima=25,
):
    """Recupera texto, alternativas e imagem original do PDF."""
    pdf = Path(caminho_pdf)
    numero = plano["numero_questao"]
    tipo = plano["tipo_questao"]
    pagina_numero = plano["pagina_inicial"]
    if not pdf.is_file():
        raise FileNotFoundError(f"PDF nao encontrado: {pdf}")
    if tipo != "objetiva":
        raise ValueError(
            "Recuperacao disponivel apenas para objetivas."
        )
    if plano["pagina_final_candidata"] != pagina_numero:
        raise ValueError(
            "Recuperacao exige questao em pagina unica."
        )
    grupos = localizar_grupos_alternativas(
        pdf,
        pagina_numero,
    )
    if (
        len(grupos) != 1
        or [a["letra"] for a in grupos[0]] != list("ABCDE")
    ):
        raise ValueError(
            "Alternativas A-E nao localizadas corretamente."
        )
    y_alternativa_a = grupos[0][0]["y"]
    with pymupdf.open(pdf) as documento:
        if not 1 <= pagina_numero <= len(documento):
            raise ValueError("Pagina inexistente no PDF.")
        pagina = documento[pagina_numero - 1]
        limites = pymupdf.Rect(pagina.rect)
        imagens = []
        for item in pagina.get_images(full=True):
            xref = item[0]
            for area in pagina.get_image_rects(xref):
                imagens.append((xref, area))
        if len(imagens) != 1:
            raise ValueError(
                "Esperada exatamente uma imagem incorporada "
                f"na pagina; encontradas {len(imagens)}."
            )
        area_imagem = pymupdf.Rect(imagens[0][1])
        regioes = {
            "superior": (
                25,
                80,
                limites.width - 25,
                area_imagem.y0 - 4,
            ),
            "inferior": (
                25,
                area_imagem.y1 + 4,
                limites.width - 25,
                y_alternativa_a - 5,
            ),
        }
        for nome, coordenadas in regioes.items():
            area = pymupdf.Rect(coordenadas)
            if area.is_empty or not limites.contains(area):
                raise ValueError(
                    f"Regiao OCR invalida: {nome}."
                )
    textos = {}
    for nome, coordenadas in regioes.items():
        textos[nome] = extrair_regiao_ocr(
            caminho_pdf=pdf,
            numero_pagina=pagina_numero,
            regiao=coordenadas,
            executavel_tesseract=executavel_tesseract,
            dpi=300,
            psm=4,
        )
    linhas = textos["superior"].splitlines()
    titulos = [
        (indice, titulo)
        for indice, linha in enumerate(linhas)
        if (titulo := identificar_titulo_ocr(linha))
    ]
    if (
        len(titulos) != 1
        or titulos[0][1] != {
            "numero_questao": numero,
            "tipo_questao": tipo,
        }
    ):
        raise ValueError(
            "Titulo OCR nao corresponde ao plano da questao."
        )
    texto_superior = "\n".join(
        linhas[titulos[0][0] + 1:]
    ).strip()
    texto_inferior = textos["inferior"].strip()
    if not texto_superior or not texto_inferior:
        raise ValueError(
            "Enunciado incompleto antes ou depois da imagem."
        )
    alternativas = recuperar_alternativas_ocr(
        caminho_pdf=pdf,
        numero_pagina=pagina_numero,
        executavel_tesseract=executavel_tesseract,
        deslocamento_texto=18,
        margem_direita=35,
        altura_ultima=altura_ultima,
    )
    if (
        [a["letra"] for a in alternativas] != list("ABCDE")
        or any(
            not a.get("texto", "").strip()
            for a in alternativas
        )
    ):
        raise ValueError(
            "Alternativas OCR incompletas ou invalidas."
        )
    texto = normalizar_quebras_ocr(
        texto_superior + "\n\n" + texto_inferior
    )
    questao = {
        "numero_questao": numero,
        "tipo_questao": tipo,
        "texto": texto,
        "alternativas": alternativas,
        "origem": {
            "arquivo": arquivo_origem,
            "pagina": pagina_numero,
        },
        "pagina_final": pagina_numero,
    }
    nome_imagem = f"questao_{numero:02d}_infografico.png"
    return anexar_imagem_incorporada_enunciado(
        questao=questao,
        caminho_pdf=pdf,
        pasta_saida=pasta_saida,
        nome_arquivo=nome_imagem,
    )
