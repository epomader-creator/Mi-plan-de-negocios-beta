
import os
from pathlib import Path

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)

allowed_origin = os.environ.get("ALLOWED_ORIGIN", "").strip()

if allowed_origin:
    CORS(app, resources={
        r"/api/*": {"origins": allowed_origin}
    })

SYSTEM = """
Eres el asistente de inteligencia artificial de
MI PLAN DE NEGOCIOS | BY JUAN POMADER.

Tu misión es acompañar al usuario, en español,
para construir un plan de negocios profesional,
práctico, personalizado y financieramente viable.

Trabaja de manera conversacional, haciendo
preguntas claras, preferentemente una a la vez.

Guía al usuario por estas etapas:

1. Idea y oportunidad de negocio.
2. Cliente objetivo y problema que resuelve.
3. Mercado y competencia.
4. Propuesta de valor.
5. Modelo de negocio.
6. Marketing Mix: producto, precio, plaza y promoción.
7. Estrategia comercial y métricas.
8. Proyecciones financieras y punto de equilibrio.
9. Validación de la idea.
10. Riesgos y oportunidades.
11. Plan de acción.
12. Campaña de marketing con inteligencia artificial.
13. Presentación ejecutiva del negocio.

Reglas fundamentales:

- Nunca inventes datos del mercado ni cifras financieras.
- Diferencia hechos, hipótesis y estimaciones.
- Solicita los datos que falten.
- Explica conceptos empresariales con lenguaje sencillo.
- Calcula el punto de equilibrio cuando existan datos suficientes.
- Si el margen de contribución es cero o negativo,
  explica que no existe un punto de equilibrio viable
  con esos valores.
- Evalúa críticamente la viabilidad del negocio.
- Propón acciones concretas y realistas.
- Mantén respuestas claras y no demasiado largas.
- No afirmes que el usuario ha pagado ni que existe
  una pasarela de pagos cuando no esté implementada.
"""

@app.get("/")
def inicio():
    archivo = Path(__file__).resolve().parent / "index.html"

    if not archivo.is_file():
        return (
            "No se encuentra index.html en el proyecto.",
            404
        )

    return send_file(archivo)


@app.get("/api/health")
def health():
    return jsonify({
        "ok": True,
        "service": "Mi Plan de Negocios IA"
    })


@app.post("/api/chat")
def chat():
    if not os.environ.get("OPENAI_API_KEY"):
        return jsonify({
            "error": "La clave de OpenAI no está configurada."
        }), 503

    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])

    if not isinstance(messages, list) or not messages:
        return jsonify({
            "error": "No se recibieron mensajes válidos."
        }), 400

    clean = []

    for msg in messages[-16:]:
        if not isinstance(msg, dict):
            continue

        role = msg.get("role")
        content = msg.get("content")

        if (
            role in ("user", "assistant")
            and isinstance(content, str)
            and content.strip()
        ):
            clean.append({
                "role": role,
                "content": content[:6000]
            })

    if not clean or clean[-1]["role"] != "user":
        return jsonify({
            "error": "El último mensaje debe ser del usuario."
        }), 400

    try:
        client = OpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            timeout=45.0
        )

        response = client.chat.completions.create(
            model=os.environ.get(
                "OPENAI_MODEL",
                "gpt-4o-mini"
            ),
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM
                },
                *clean
            ],
            temperature=0.5,
            max_tokens=900
        )

        reply = response.choices[0].message.content

        return jsonify({
            "reply": reply or "No pude generar una respuesta."
        })

    except Exception:
        app.logger.exception("Error al consultar OpenAI")

        return jsonify({
            "error": (
                "No fue posible consultar la inteligencia "
                "artificial. Revisa la configuración y "
                "vuelve a intentarlo."
            )
        }), 502


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
    
