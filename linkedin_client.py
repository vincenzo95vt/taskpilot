import requests
from dotenv import load_dotenv
import os
load_dotenv()

client_secret = os.getenv('LINKEDIN_PRIMARY_SECRET')
linkedin_id = os.getenv('LINKEDIN_CLIENT_ID')
linkedin_access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
linkedin_org_id = os.getenv('LINKEDIN_ORGANIZATION_ID')
def post_to_linkeind(text, image_path= None):
    if not linkedin_access_token:
        raise ValueError('falta el token de Linkedin. Añadelo a tu archivo .env')
    headers = {
        'Authorization': f"Bearer{linkedin_access_token}",
        'X-Restli-Protocol-Version': '2.0.0'
    }
    asset = None
    if image_path:
        register_upload = requests.post(
        "https://api.linkedin.com/v2/assets?action=registerUpload",
        headers = headers,
        json = {
            "registerUploadRequest" : {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": f"urn:li:organization:{linkedin_org_id}",
                    "serviceRelationships": [
                        {"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}
                    ]   
                }
            }
        )
        print("🔍 register_upload response:", register_upload.status_code, register_upload.text)
        upload_data = register_upload.json()
        upload_url = upload_data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
        asset = upload_data['value']['asset']

        with open(image_path, "rb") as f:
            upload_response = requests.put(upload_url, data=f, headers={"Authorization": f"Bearer {linkedin_access_token}"})
            if upload_response.status_code not in (200, 201):
                return {
                    "status": upload_response.status_code,
                    "messaeg": f"Error subiendo imagen: {upload_response.text}"
                }
    post_body = {
        "author": f"urn:li:organization:{linkedin_org_id}",
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
    response = requests.post("https://api.linkedin.com/v2/ugcPosts", headers=headers, json=post_body)
    if response.status_code == 201:
        return  {
            "status": 200,
            "message": 'Publicado correctamente en Linkedin'
        }
    else:
        return {
            "status": response.status_code,
            "message": f"Error a la hora de publicar en linkedin {response.text}"
        }