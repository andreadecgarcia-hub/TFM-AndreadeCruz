#Imports
import os
import re
import time
import unicodedata
import streamlit as st
from smolagents import ToolCallingAgent, OpenAIServerModel, tool

# Configuración

OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("Falta OPENAI_API_KEY en st.secrets.")
    st.stop()

MODEL_ID = st.secrets.get("OPENAI_MODEL", "gpt-4o-mini")

def build_model():
    return OpenAIServerModel(model_id=MODEL_ID, api_key=OPENAI_API_KEY)

#Memoria y utilidades de texto

class EvidenceStore:
    _data = {}

    @classmethod
    def reset(cls):
        cls._data = {}

    @classmethod
    def add(cls, key: str, value: str):
        cls._data[key] = value

    @classmethod
    def get(cls):
        return dict(cls._data)

def _norm(s: str) -> str:
    s = s.lower().strip()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return s
    
    # Validar formato de salida en formato aviso
def check_veredicto_completo(final_answer: str):
    if not isinstance(final_answer, str):
        raise ValueError("La salida final no es texto.")
    if not re.search(r"(?im)^\s*veredicto\s*:\s*(.+)$", final_answer):
        raise ValueError("Falta 'Veredicto: ...'.")
    if not re.search(r"(?im)^\s*justificaci[oó]n\s+breve\s*:\s*(.+)$", final_answer):
        raise ValueError("Falta 'Justificación breve: ...'.")
    if not re.search(r"(?im)^\s*confiabilidad\s*:\s*(0(\.\d+)?|1(\.0+)?)\s*$", final_answer):
        raise ValueError("Falta 'Confiabilidad: 0.0–1.0'.")
    return True

def _extract_veredicto(s: str):
    pat_es = r"(?im)^[\s\*\-_>]*veredicto\s*:\s*(verdadero|falso|dudoso)\b"
    m = list(re.finditer(pat_es, s))
    if m:
        return m[-1].group(1).lower()

    pat_en = r"(?im)^[\s\*\-_>]*(verdict|decision)\s*:\s*(true|false|uncertain|inconclusive)\b"
    m = list(re.finditer(pat_en, s))
    if m:
        word = m[-1].group(2).lower()
        return {"true":"verdadero","false":"falso","uncertain":"dudoso","inconclusive":"dudoso"}[word]

    return None

def _extract_confiabilidad(s: str):
    num = r"(0(?:[.,]\d+)?|1(?:[.,]0+)?)"
    m = re.findall(rf"(?im)^\s*confiabilidad\s*:\s*{num}\s*$", s)
    if m:
        return m[-1].replace(",", ".")

    m = re.findall(rf"(?im)\bconfiabilidad\s*:\s*{num}\b", s)
    if m:
        return m[-1].replace(",", ".")

    return None


def _extract_justificacion(s: str):
    num = r"(0(?:[.,]\d+)?|1(?:[.,]0+)?)"
    pat = rf"(?im)^[\s\*\-_>]*justificaci[oó]n\s+breve\s*:\s*(.+?)(?:\s+confiabilidad\s*:\s*{num}\s*)?$"
    m = re.search(pat, s)
    return m.group(1).strip() if m else None

#Prompts fijos

SYSTEM_PROMPT_JURADO = (
    "Eres un jurado de IA. Tu única tarea es decidir si una afirmación es "
    "VERDADERA, FALSA o DUDOSA basándote en los análisis aportados.\n\n"
    "Devuelve SIEMPRE en el siguiente formato EXACTO (en español):\n\n"
    "Veredicto: <Verdadero|Falso|Dudoso>\n"
    "Justificación breve: <máx. 3 frases, concretas>\n"
    "Confiabilidad: <número entre 0.0 y 1.0>\n"
)

SUB_PROMPT_SENSACIONALISMO = (
    "Analiza si la afirmación usa lenguaje sensacionalista/emocional. "
    "Devuelve 2-4 frases, objetivas y concisas."
)
SUB_PROMPT_GRAMATICA = (
    "Revisa la afirmación y detecta errores gramaticales/ortográficos/estilo. "
    "Devuelve 2-4 frases, claras y útiles que indiquen si hay errores gramaticales/ortográficos/estilo o por lo contrario si esta correctamente escrita la afirmación."
)
SUB_PROMPT_SENTIDO_COMUN = (
    "Evalúa si la afirmación contradice el sentido común. "
    "Devuelve 2-4 frases, con razonamiento breve."
)

# Crear Agentes
def make_agent(instructions: str, tools=None, max_steps: int = 6) -> ToolCallingAgent:
    tools = tools or []
    try:
        return ToolCallingAgent(
            model=build_model(),
            tools=tools,
            instructions=instructions,
            max_steps=max_steps,
        )
    except TypeError:
        try:
            return ToolCallingAgent(
                model=build_model(),
                tools=tools,
                instructions=instructions,
            )
        except TypeError:
            agent = ToolCallingAgent(model=build_model(), tools=tools)
            if hasattr(agent, "instructions"):
                agent.instructions = instructions
            elif hasattr(agent, "system_prompt"):
                agent.system_prompt = instructions
            return agent

def run_with_retry(agent: ToolCallingAgent, prompt: str, retries: int = 2, backoff: float = 1.0) -> str:
    for i in range(retries + 1):
        try:
            return agent.run(prompt)
        except Exception:
            if i == retries:
                raise
            time.sleep(backoff * (i + 1))

#Subagentes/Tools

@tool
def evaluar_sentido_comun(texto: str) -> str:
    """Evalúa si la afirmación contradice el sentido común.
    Args:
        texto (str): La afirmación a evaluar.
    Returns:
        str: Análisis breve (2–4 frases).
    """
    out = subagente_texto(SUB_PROMPT_SENTIDO_COMUN, texto)
    EvidenceStore.add("sentido_comun", out)
    return out

@tool
def evaluar_sensacionalismo(texto: str) -> str:
    """Detecta uso de lenguaje sensacionalista o emocional.
    Args:
        texto (str): La afirmación a evaluar.
    Returns:
        str: Análisis breve (2–4 frases).
    """
    out = subagente_texto(SUB_PROMPT_SENSACIONALISMO, texto)
    EvidenceStore.add("sensacionalismo", out)
    return out

@tool
def evaluar_gramatica(texto: str) -> str:
    """Revisa gramática, ortografía y estilo.
    Args:
        texto (str): La afirmación a evaluar.
    Returns:
        str: Análisis breve (2–4 frases).
    """
    out = subagente_texto(SUB_PROMPT_GRAMATICA, texto)
    EvidenceStore.add("gramatica", out)
    return out

def subagente_texto(instrucciones: str, afirmacion: str) -> str:
    agent = make_agent(instrucciones, tools=[])
    return run_with_retry(agent, f"Afirmación: {afirmacion}", retries=1, backoff=0.8)

# Analizar afirmación
def analizar_afirmacion(claim: str) -> str:
    claim = str(claim).strip()
    if not claim:
        raise ValueError("La afirmación está vacía.")

    EvidenceStore.reset()

    jurado = make_agent(
        SYSTEM_PROMPT_JURADO + (
            "\n\nDEBES recopilar evidencia llamando a herramientas antes del veredicto. "
            "Llama a (1) evaluar_sensacionalismo, (2) evaluar_gramatica y "
            "(3) evaluar_sentido_comun sobre la MISMA afirmación, y solo después dicta veredicto."
        ),
        tools=[evaluar_sensacionalismo, evaluar_gramatica, evaluar_sentido_comun],
        max_steps=12,
    )

    try:
        jurado.verbose = False
    except Exception:
        pass

    prompt_veredicto = (
        f'Afirmación: "{claim}"\n\n'
        "Primero, usa las herramientas indicadas con el texto de la afirmación. "
        "Cuando tengas suficiente evidencia, responde únicamente en este formato EXACTO:\n\n"
        "Veredicto: <Verdadero|Falso|Dudoso>\n"
        "Justificación breve: <máx. 3 frases, concretas>\n"
        "Confiabilidad: <número entre 0.0 y 1.0>\n"
        "No incluyas 'Confiabilidad' dentro de 'Justificación breve'."
    )


    salida = run_with_retry(jurado, prompt_veredicto, retries=2, backoff=0.8)

    aviso_validator = ""
    try:
        check_veredicto_completo(salida)
    except Exception as e:
        aviso_validator = f"\n\n> **Aviso del validador**: {e}"

    veredicto_final     = _extract_veredicto(salida) or "—"
    justificacion_final = _extract_justificacion(salida) or "—"
    confianza_final     = _extract_confiabilidad(salida) or "—"


    evid = EvidenceStore.get()
    evid_sens = evid.get("sensacionalismo", "— (no se invocó la tool)")
    evid_gram = evid.get("gramatica", "— (no se invocó la tool)")
    evid_comn = evid.get("sentido_comun", "— (no se invocó la tool)")

    # Markdown final
    resultado_md = (
        f"**Veredicto:** {veredicto_final}\n\n"
        f"**Justificación breve:** {justificacion_final}\n\n"
        f"**Confiabilidad:** {confianza_final}{aviso_validator}\n\n"
        "---\n\n"
        f"### Evidencias de subagentes\n"
        f"- **Sensacionalismo:** {evid_sens}\n"
        f"- **Gramática:** {evid_gram}\n"
        f"- **Sentido común:** {evid_comn}\n"
    )

    return resultado_md