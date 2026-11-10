REVIEW_PROMPT = """Eres un analista de reseñas de productos de consumo.
Analiza las siguientes opiniones de compradores. No inventes datos: usa solo los textos proporcionados.

Reseñas:
{reviews}

Devuelve SOLO un JSON válido, sin texto adicional, con esta forma exacta:
{{
  "score": 7.5,
  "resenas_analizadas": 9,
  "sintesis": "Resumen breve de la opinión general.",
  "pros": ["punto positivo 1", "punto positivo 2", "punto positivo 3"],
  "contras": ["punto negativo 1", "punto negativo 2", "punto negativo 3"]
}}

El score debe estar entre 0 y 10. Si no hay contras claras, usa una lista vacía.
"""

AUDIENCE_PROMPT = """Eres un asesor de compras. A partir de las opciones y resúmenes, identifica al menos 4 perfiles de usuario relevantes (por ejemplo: estudiante, profesional, gamer, hogar).
Cada recomendación debe basarse en los datos proporcionados, sin inventar especificaciones.

Producto buscado: {producto}
Opciones:
{opciones}

Resumen de precios: {precios}
Resumen de reseñas: {resenas}

Devuelve SOLO un JSON válido, sin texto adicional, con esta forma:
{{
  "perfiles": [
    {{"perfil": "Estudiante", "descripcion": "Recomendación concreta.", "evidencia": "Nombre y precio de la opción.", "porcentaje": 85}}
  ],
  "sintesis": "Resumen de las recomendaciones por perfil."
}}
"""

SYNTHESIS_PROMPT = """Eres un asistente de compras experto. Redacta una recomendación final en español, clara y honesta, usando solo la información proporcionada. No inventes precios, especificaciones ni opiniones.

Producto buscado: {producto}

Opciones analizadas:
{opciones}

Resumen de precios:
{precios}

Resumen de reseñas:
{resenas}

Recomendaciones por perfil:
{perfiles}

Advertencias:
{advertencias}

Redacta un texto de máximo 250 palabras con esta estructura:
1. Mejor opción y por qué.
2. Comparación de precios entre tiendas.
3. Lo que dicen las reseñas (fortalezas y quejas).
4. Recomendación por perfil de usuario.
5. Advertencia si algún dato proviene de respaldo mock.
"""
