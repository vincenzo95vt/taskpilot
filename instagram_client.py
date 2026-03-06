import requests
import os
from dotenv import load_dotenv
import cloudinary 
import cloudinary.uploader
import time
load_dotenv()
id_business_account = os.getenv('IG_BUSINESS_ACCOUNT')
user_token = os.getenv('META_USER_TOKEN')
app_token = os.getenv('META_APP_TOKEN')

cloudinary.config(
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

def post_to_ig(caption, image_url):
    create_url = f"https://graph.facebook.com/v18.0/{id_business_account}/media"
    params = {
        'image_url': image_url,
        "caption": caption,
        "access_token" : user_token
    }
    res = requests.post(create_url, params=params)
    data = res.json()

    if "id" not in data:
        print('Error al crear el contenedor:', data)
        return None
    container_id = data['id']
    for i in range(5):
        time.sleep(2)
        status_url = f"https://graph.facebook.com/v18.0/{container_id}?fields=status_code&access_token={user_token}"
        status = requests.get(status_url).json()
        print('Estado:', status)
        if status.get("status_code") == 'FINISHED':
            break
    else:
        print('imagen no lista')
        return None
    publish_url = f"https://graph.facebook.com/v18.0/{id_business_account}/media_publish"
    params = {'creation_id': container_id, 'access_token': user_token}
    publis_res = requests.post(publish_url, params=params)
    return publis_res.json()

def upload_video_to_cloudinary(video_path: str) -> str:
    print('subiendo video a cloudinary')
    result = cloudinary.uploader.upload(
        video_path,
        resource_type="video",
        folder="reels",
    )
    url = result["secure_url"]
    print(f"✅ Vídeo disponible en: {url}")
    return url

def post_reel_to_ig(caption: str, video_path: str) -> dict:
    """
    Publica un Reel en Instagram.
    video_path: ruta local al archivo .mp4 generado por reel_generator.py
    """
    # Paso 1: Subir vídeo a Cloudinary para obtener URL pública
    video_url = upload_video_to_cloudinary(video_path)

    # Paso 2: Crear contenedor de Reel en Meta
    print("📦 Creando contenedor de Reel...")
    create_url = f"https://graph.facebook.com/v18.0/{id_business_account}/media"
    params = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "share_to_feed": "true",  # Aparece también en el feed principal
        "access_token": user_token
    }
    res = requests.post(create_url, params=params)
    data = res.json()

    if "id" not in data:
        print("❌ Error al crear contenedor de Reel:", data)
        return {"status": 500, "message": str(data)}

    container_id = data["id"]
    print(f"✅ Contenedor creado: {container_id}")

    print("⏳ Esperando procesamiento del vídeo...")
    for attempt in range(15):
        time.sleep(5)
        status_url = (
            f"https://graph.facebook.com/v18.0/{container_id}"
            f"?fields=status_code&access_token={user_token}"
        )
        status = requests.get(status_url).json()
        status_code = status.get("status_code")
        print(f"  Intento {attempt + 1}/15 — Estado: {status_code}")

        if status_code == "FINISHED":
            break
        elif status_code == "ERROR":
            return {"status": 500, "message": "Meta reportó error procesando el vídeo"}
    else:
        return {"status": 500, "message": "Timeout: el vídeo no se procesó a tiempo"}

    print("🚀 Publicando Reel...")
    publish_url = f"https://graph.facebook.com/v18.0/{id_business_account}/media_publish"
    publish_res = requests.post(publish_url, params={
        "creation_id": container_id,
        "access_token": user_token
    })
    result = publish_res.json()

    if "id" in result:
        print(f"✅ Reel publicado: {result['id']}")
        return {"status": 200, "message": "Reel publicado correctamente", "id": result["id"]}
    else:
        return {"status": 500, "message": str(result)}