-- ============================================================
-- AUTOPOSTS - Schema Supabase
-- Ejecuta esto en el SQL Editor de tu proyecto Supabase
-- ============================================================

-- Tabla de prompts (editables desde el dashboard)
CREATE TABLE prompts (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name         text UNIQUE NOT NULL,
    system_prompt text,
    user_prompt  text NOT NULL,
    updated_at   timestamptz DEFAULT now()
);

-- Auto-actualizar updated_at al editar
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prompts_updated_at
BEFORE UPDATE ON prompts
FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- Tabla de fuentes RSS (gestionables desde el dashboard)
CREATE TABLE rss_feeds (
    id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name   text,
    url    text UNIQUE NOT NULL,
    active boolean DEFAULT true
);


-- Tabla de artículos (reemplaza Google Sheets)
CREATE TABLE articles (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    url          text UNIQUE NOT NULL,
    status       text DEFAULT 'pending',   -- 'pending' | 'published' | 'failed'
    published_at timestamptz,
    created_at   timestamptz DEFAULT now()
);


-- ============================================================
-- DATOS INICIALES
-- ============================================================

INSERT INTO rss_feeds (name, url) VALUES
    ('MIT Technology Review', 'https://www.technologyreview.com/feed/');


INSERT INTO prompts (name, user_prompt) VALUES
(
    'instagram_caption',
    E'Eres el community manager de The SynthSight, empresa de software en Málaga.\nTu tarea es escribir una descripción corta para acompañar un Reel de Instagram sobre esta noticia.\nNoticia: {content}\nInstrucciones:\n- Escribe MÁXIMO 3 líneas en total.\n- La primera línea debe ser un gancho que genere intriga o impacto, sin revelar toda la noticia.\n- La segunda línea (opcional) añade un dato o contexto breve que pique la curiosidad.\n- La última línea debe invitar a ver el vídeo, por ejemplo: "Mira el vídeo 👆" o "Te lo contamos en el Reel 👆"\n- Tono directo, tech, sin corporativismos.\n- No cuentes la noticia completa — eso lo hace el vídeo.\n- Al final del texto, añade una línea en blanco y luego entre 8 y 12 hashtags relevantes.\n- Los hashtags deben mezclar: 3-4 específicos de la noticia, 3-4 de nicho tech/IA en español, 2-3 generales.\n- Ejemplo de formato hashtags: #GPT5 #OpenAI #InteligenciaArtificial #TechEspanol #IA #Tecnologia'
),
(
    'linkedin_post',
    E'Eres el editor de The SynthSight, medio de noticias tech/IA en español.\nTu tarea es reescribir esta noticia para publicarla en LinkedIn.\n\nNoticia: {content}\n\nInstrucciones:\n- Escribe entre 150-300 palabras\n- Tono profesional pero accesible, con opinión propia\n- Estructura: contexto → qué ha pasado → por qué importa → reflexión final\n- NO uses frases como "Te lo contamos en el Reel" o "Mira el vídeo"\n- Termina con una pregunta que invite a comentar\n- Añade 8-10 hashtags relevantes al final\n- Escribe SIEMPRE en español'
);

INSERT INTO prompts (name, system_prompt, user_prompt) VALUES
(
    'reel_script',
    E'Eres el community manager de The SynthSight, empresa de software en Málaga.\nTono: directo, técnico pero accesible, con opinión propia. Frases cortas.\nTu tarea: convertir un artículo en un guión para un Reel de Instagram.\nDivide el contenido en 3-5 escenas cortas.\n\nIMPORTANTE:\n- La ÚLTIMA escena siempre debe cerrar con una frase corta y definitiva, por ejemplo:\n  "Esto es todo por hoy." o "¿Tú qué opinas? Déjalo en comentarios." o "Síguenos para más noticias tech."\n- Nunca termines con una frase inconclusa o que suene a que hay más contenido después.\n- Cada narración debe sonar completa por sí sola, con pausas naturales.\n\nResponde SOLO con un JSON válido, sin backticks ni explicaciones:\n[\n  {\n    "narration": "texto que se narrará en voz alta (máx 2 frases)",\n    "image_prompt": "prompt en inglés para DALL-E, estilo tech moderno, vertical 9:16"\n  }\n]',
    'Convierte este artículo en guión de Reel:\n\n{content}'
),
(
    'broll_keywords',
    E'Eres un director de vídeo. Tu tarea es extraer keywords visuales específicas para buscar clips de b-roll en Pexels.\n\nREGLAS:\n- Devuelve SOLO un JSON array con 6 keywords en inglés\n- Sé MUY específico: no uses "technology" o "artificial intelligence"\n- Usa términos visuales concretos: "robot arm factory", "server room cables",\n  "person typing laptop", "stock market screen", "satellite space", etc.\n- Piensa en qué imágenes aparecerían en un telediario sobre esta noticia\n- Varía entre primer plano, plano general y plano detalle\n\nResponde SOLO con JSON, sin backticks:\n["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6"]',
    'Extrae keywords visuales para esta noticia:\n\n{content}'
);
