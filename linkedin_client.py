import requests
from dotenv import load_dotenv
import os
import tempfile

load_dotenv()

linkedin_access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
linkedin_org_id = os.getenv('LINKEDIN_ORGANIZATION_ID')  # Solo el número, ej: 12345678


def post_to_linkedin(text, image_path=None):
    try:
        if not linkedin_access_token:
            raise ValueError('Falta el token de LinkedIn. Añádelo a tu archivo .env')

        headers = {
            'Authorization': f"Bearer {linkedin_access_token}",
            'X-Restli-Protocol-Version': '2.0.0',
            'Content-Type': 'application/json',
        }

        # ✅ FIX 1: usar urn:li:organization, NO urn:li:person
        author_urn = f"urn:li:organization:{linkedin_org_id}"

        asset = None
        temp_file = None

        # Si la imagen es una URL, descargarla temporalmente
        if image_path and image_path.startswith('http'):
            response = requests.get(image_path)
            if response.status_code != 200:
                raise Exception(f"Error descargando la imagen: {response.status_code}")
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            temp_file.write(response.content)
            temp_file.close()
            image_path = temp_file.name
            print(f"Imagen temporal guardada en {image_path}")

        # Subir imagen si existe
        if image_path:
            register_upload = requests.post(
                "https://api.linkedin.com/v2/assets?action=registerUpload",
                headers=headers,
                json={
                    "registerUploadRequest": {
                        "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                        # ✅ FIX 1 aquí también
                        "owner": author_urn,
                        "serviceRelationships": [
                            {
                                "relationshipType": "OWNER",
                                "identifier": "urn:li:userGeneratedContent"
                            }
                        ]
                    }
                }
            )

            print("🔍 register_upload response:", register_upload.status_code, register_upload.text)

            if register_upload.status_code not in (200, 201):
                raise Exception(f"Error registrando la subida: {register_upload.text}")

            upload_data = register_upload.json()
            upload_url = upload_data["value"]["uploadMechanism"][
                "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
            ]["uploadUrl"]
            asset = upload_data['value']['asset']

            # ✅ FIX 2: usar POST en vez de PUT para subir la imagen
            with open(image_path, "rb") as f:
                upload_response = requests.post(
                    upload_url,
                    data=f,
                    headers={"Authorization": f"Bearer {linkedin_access_token}"}
                )
                print("🔍 upload_response:", upload_response.status_code, upload_response.text)
                if upload_response.status_code not in (200, 201):
                    raise Exception(f"Error subiendo imagen: {upload_response.text}")

        # Crear el cuerpo del post
        post_body = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE" if not asset else "IMAGE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        if asset:
            post_body["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                {"status": "READY", "media": asset}
            ]

        response = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers=headers,
            json=post_body
        )

        print("🔍 ugcPosts response:", response.status_code, response.text)

        if response.status_code == 201:
            return {"status": 200, "message": "Publicado correctamente en LinkedIn ✅"}
        else:
            return {"status": response.status_code, "message": f"Error al publicar: {response.text}"}

    except requests.exceptions.RequestException as e:
        return {"status": 500, "message": f"Error de conexión con LinkedIn: {e}"}
    except ValueError as e:
        return {"status": 400, "message": str(e)}
    except Exception as e:
        return {"status": 500, "message": f"Error inesperado: {e}"}
    finally:
        if temp_file:
            try:
                os.remove(temp_file.name)
                print(f"Imagen temporal eliminada: {temp_file.name}")
            except Exception as cleanup_error:
                print(f"No se pudo eliminar el archivo temporal: {cleanup_error}")

"""
Función para subir vídeos a LinkedIn
Añade esto a tu linkedin_client.py
"""

def post_video_to_linkedin(text: str, video_path: str):
    """
    Sube un vídeo a LinkedIn y publica en la página de empresa.
    """
    try:
        if not linkedin_access_token:
            raise ValueError('Falta el token de LinkedIn')

        headers = {
            'Authorization': f"Bearer {linkedin_access_token}",
            'X-Restli-Protocol-Version': '2.0.0',
            'Content-Type': 'application/json',
        }

        author_urn = f"urn:li:organization:{linkedin_org_id}"
        video_size = os.path.getsize(video_path)

        # ── PASO 1: Inicializar subida del vídeo ──
        print("📤 Iniciando subida de vídeo a LinkedIn...")
        init_response = requests.post(
            "https://api.linkedin.com/v2/assets?action=registerUpload",
            headers=headers,
            json={
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-video"],
                    "owner": author_urn,
                    "serviceRelationships": [
                        {
                            "relationshipType": "OWNER",
                            "identifier": "urn:li:userGeneratedContent"
                        }
                    ],
                    "supportedUploadMechanism": ["SINGLE_REQUEST_UPLOAD"]
                }
            }
        )

        print(f"🔍 Init response: {init_response.status_code} {init_response.text}")

        if init_response.status_code not in (200, 201):
            raise Exception(f"Error iniciando subida: {init_response.text}")

        upload_data   = init_response.json()
        upload_url    = upload_data["value"]["uploadMechanism"][
            "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
        ]["uploadUrl"]
        asset         = upload_data["value"]["asset"]

        # ── PASO 2: Subir el archivo de vídeo ──
        print("⬆️  Subiendo vídeo...")
        with open(video_path, "rb") as video_file:
            upload_response = requests.post(
                upload_url,
                data=video_file,
                headers={
                    "Authorization": f"Bearer {linkedin_access_token}",
                    "Content-Type": "application/octet-stream",
                }
            )

        print(f"🔍 Upload response: {upload_response.status_code}")

        if upload_response.status_code not in (200, 201):
            raise Exception(f"Error subiendo vídeo: {upload_response.text}")

        # ── PASO 3: Publicar el post con el vídeo ──
        print("📝 Publicando post con vídeo...")
        post_body = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "VIDEO",
                    "media": [
                        {
                            "status": "READY",
                            "media": asset,
                            "title": {"attributes": [], "text": "The SynthSight"}
                        }
                    ]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        response = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers=headers,
            json=post_body
        )

        print(f"🔍 ugcPosts response: {response.status_code} {response.text}")

        if response.status_code == 201:
            return {"status": 200, "message": "Vídeo publicado correctamente en LinkedIn ✅"}
        else:
            return {"status": response.status_code, "message": f"Error al publicar: {response.text}"}

    except Exception as e:
        return {"status": 500, "message": f"Error inesperado: {e}"}