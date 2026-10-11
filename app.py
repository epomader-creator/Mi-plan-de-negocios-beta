import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
allowed = os.environ.get('ALLOWED_ORIGINS', 'https://epomader-creator.github.io').split(',')
CORS(app, resources={r'/api/*': {'origins': [x.strip() for x in allowed]}}, methods=['POST','GET'])

SYSTEM = '''Eres el copiloto de MI PLAN DE NEGOCIOS | BY JUAN POMADER. Hablas español claro, profesional y cercano. Ayudas al emprendedor a construir un plan de negocios viable mediante preguntas guiadas y análisis práctico. Sigue estas 13 etapas: (1) idea y oportunidad, (2) cliente objetivo y problema, (3) mercado y competencia, (4) propuesta de valor, (5) modelo de negocio, (6) marketing mix 4P, (7) estrategia comercial y métricas, (8) finanzas y punto de equilibrio, (9) validación y prueba mínima, (10) riesgos, (11) decisión y plan de acción, (12) campaña creativa con IA, (13) presentación final. Haz una pregunta concreta por turno cuando falten datos. Distingue HECHO, HIPÓTESIS y ESTIMACIÓN. No inventes cifras, fuentes, clientes ni validaciones. Si el usuario pide cálculos, explica supuestos y fórmulas. Recomienda LANZAR, AJUSTAR, VALIDAR MÁS o NO LANZAR únicamente cuando haya evidencia suficiente. No solicites cédulas, claves, números de tarjeta u otros datos sensibles. Respuestas de 50-180 palabras, salvo solicitud de detalle.'''

@app.get('/api/health')
def health():
    return jsonify({'ok': True, 'service': 'Mi Plan de Negocios IA'})

@app.post('/api/chat')
def chat():
    if not os.environ.get('OPENAI_API_KEY'):
        return jsonify({'error': 'Falta configurar OPENAI_API_KEY en Render.'}), 503
    data = request.get_json(silent=True) or {}
    messages = data.get('messages', [])
    if not isinstance(messages, list) or not messages:
        return jsonify({'error': 'No se recibió un mensaje.'}), 400
    clean = []
    for msg in messages[-16:]:
        if isinstance(msg, dict) and msg.get('role') in ('user', 'assistant') and isinstance(msg.get('content'), str):
            clean.append({'role': msg['role'], 'content': msg['content'][:5000]})
    if not clean or clean[-1]['role'] != 'user':
        return jsonify({'error': 'Mensaje inválido.'}), 400
    try:
        client = OpenAI(api_key=os.environ['OPENAI_API_KEY'], timeout=30)
        response = client.chat.completions.create(model=os.environ.get('OPENAI_MODEL', 'gpt-4o-mini'), messages=[{'role':'system','content':SYSTEM}, *clean], max_tokens=650, temperature=0.5)
        return jsonify({'reply': response.choices[0].message.content or 'No pude generar una respuesta.'})
    except Exception as exc:
        # Do not expose provider error details or credentials to visitors.
        app.logger.error('OpenAI request failed: %s', type(exc).__name__)
        return jsonify({'error': 'No fue posible contactar al asistente. Revisa la configuración y el saldo de API en OpenAI.'}), 502

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
