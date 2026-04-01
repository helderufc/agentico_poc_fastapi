"""
Wrapper do cliente OpenAI GPT-4o para uso nas features de IA.
"""
from typing import Optional
from openai import OpenAI
from config import settings


def _client() -> OpenAI:
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def gerar_conteudo_aula(texto_fonte: str) -> str:
    """
    Recebe texto extraído do PDF e/ou CKEditor e retorna HTML
    bem formatado gerado pelo GPT-4o (RF26).
    """
    prompt = (
        "Você é um assistente pedagógico. Com base no material abaixo, "
        "gere um conteúdo de aula em HTML bem estruturado, com títulos, "
        "parágrafos e listas quando apropriado. "
        "Retorne APENAS o HTML, sem blocos de código markdown.\n\n"
        f"Material:\n{texto_fonte}"
    )
    resposta = _client().chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return resposta.choices[0].message.content.strip()


def gerar_quiz(texto_fonte: str, num_perguntas: int = 5) -> list[dict]:
    """
    Recebe o conteúdo agregado do módulo e retorna uma lista de perguntas
    com alternativas e resposta correta sugerida (RF35).

    Retorna lista de dicts no formato:
    [
      {
        "enunciado": "...",
        "pontos": 1,
        "alternativas": [
          {"texto": "...", "correta": false},
          ...
          {"texto": "...", "correta": true}
        ]
      },
      ...
    ]
    """
    import json

    prompt = (
        f"Você é um professor criando uma prova. Com base no conteúdo abaixo, "
        f"gere exatamente {num_perguntas} perguntas de múltipla escolha. "
        f"Cada pergunta deve ter entre 3 e 4 alternativas, com exatamente 1 correta. "
        f"Responda APENAS com um JSON válido, sem markdown, no formato:\n"
        f'[{{"enunciado":"...","pontos":1,"alternativas":[{{"texto":"...","correta":false}},{{"texto":"...","correta":true}}]}}]\n\n'
        f"Conteúdo:\n{texto_fonte}"
    )
    resposta = _client().chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        response_format={"type": "json_object"},
    )
    raw = resposta.choices[0].message.content.strip()

    # GPT retorna {"perguntas": [...]} ou diretamente [...]
    parsed = json.loads(raw)
    if isinstance(parsed, dict):
        # tenta chave "perguntas" ou pega o primeiro valor da dict
        perguntas = parsed.get("perguntas") or next(iter(parsed.values()))
    else:
        perguntas = parsed

    return perguntas


def extrair_texto_pdf(caminho: str) -> str:
    """Extrai texto de um PDF usando pypdf."""
    from pypdf import PdfReader
    import html

    reader = PdfReader(caminho)
    partes = []
    for page in reader.pages:
        texto = page.extract_text()
        if texto:
            partes.append(texto.strip())
    return "\n".join(partes)
