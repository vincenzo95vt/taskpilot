# 🤖 SynthSight AutoPosts Bot

Un bot inteligente desarrollado en **Python** que publica noticias de **tecnología e inteligencia artificial** en **Instagram** de forma automática.  
Obtiene titulares desde **fuentes RSS**, los analiza y reescribe con **OpenAI GPT** para lograr un estilo informativo, conciso y atractivo, y los publica a través de la **API de Meta (Instagram Graph API)**.

---

## 🚀 Características principales

- 🔄 **Automatización completa:** obtiene, procesa y publica contenido sin intervención manual.  
- 🧠 **Reescritura con IA:** transforma los titulares originales en textos más naturales, objetivos y atractivos.  
- 📰 **Fuentes RSS dinámicas:** configurable para distintas webs de noticias tecnológicas.  
- 📸 **Publicación automática:** genera imágenes o miniaturas y las sube directamente a Instagram.  
- ⚙️ **Configuración sencilla:** mediante variables de entorno (`.env`) y un archivo `config.py`.  
- 📅 **Ejecución programada:** utiliza **GitHub Actions** para publicar dos veces al día de forma automática.  

---

## 🧩 Tecnologías utilizadas

- **Python 3.12**  
- **OpenAI API** — Reescritura y mejora de titulares  
- **Meta Graph API** — Publicación en Instagram  
- **Google Sheets API + gspread** — Registro y control de publicaciones  
- **GitHub Actions** — Automatización de tareas y despliegue  

---

## 🧱 Estructura del proyecto

autoposts/
│
├── bot.py # Script principal del bot
├── google_client.py # Módulo de conexión con Google Sheets
├── utils/ # Funciones auxiliares (formato, logs, etc.)
├── config.py # Configuración general del proyecto
├── requirements.txt # Dependencias necesarias
└── .github/workflows/
└── autoposts.yml # Automatización con GitHub Actions
## 🧩 Ejemplo de flujo

1. El bot obtiene los titulares más recientes de un **Feed RSS**.  
2. Reescribe los titulares usando **OpenAI GPT** con un estilo claro y objetivo.  
3. Genera una imagen o diseño visual para acompañar la publicación.  
4. Publica automáticamente el contenido en la cuenta de Instagram configurada.  
5. Guarda el registro en **Google Sheets** para evitar duplicados.  
6. Envía una notificación a **Telegram** con el estado del proceso.  

---

## 🧠 Proyecto SynthSight

**SynthSight** es una iniciativa de automatización de contenidos que combina inteligencia artificial y redes sociales para compartir noticias tecnológicas de forma eficiente, creativa y transparente.  
Forma parte del ecosistema de automatizaciones de **TaskPilot**, enfocado en la creación de contenido autónomo impulsado por IA.

---

## 💡 Próximas mejoras

- 🎥 Integración con **TikTok y YouTube Shorts**.  
- 📊 Sistema de analítica para medir engagement y rendimiento.  
- 🧍‍♂️ Generación de vídeos con **avatares IA** explicando las noticias.  
- 🌐 Panel web de control para gestionar fuentes RSS, horarios y estilo de publicación.  

---

## 🧑‍💻 Autor

**Pablo Vincenzo Vasta Triviño**  
Desarrollador Fullstack especializado en automatización con IA  
🔗 [linkedin.com/in/pablovasta](https://linkedin.com/in/pablovasta)
