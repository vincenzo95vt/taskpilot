import requests
import os
from dotenv import load_dotenv
import time
load_dotenv()
id_business_account = os.getenv('IG_BUSINESS_ACCOUNT')
user_token = os.getenv('META_USER_TOKEN')
app_token = os.getenv('META_APP_TOKEN')

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

