import requests
import os

def download_image(token, name_img):
    try:

        # Get current backend file location
        backend_location = os.path.dirname(os.path.abspath(__file__))
        print(f"📍 Backend location: {backend_location}")

        # Go up to project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(backend_location)))
        print(f"📍 Project root: {project_root}")

        # Path to tablette_app/static/assets/images
        tablette_app_path = os.path.join(project_root, "tablette_app", "static", "assets", "images")
        print(f"📍 Tablette app path: {tablette_app_path}")

        # Ensure folder exists
        os.makedirs(tablette_app_path, exist_ok=True)

        # Download the image
        url = f"https://www.unistudious.com/slc/public-image-server/{name_img}"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(url, headers=headers, stream=True)
        response.raise_for_status()

        # Save directly inside images folder
        file_path = os.path.join(tablette_app_path, name_img)

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"✅ Image downloaded to: {file_path}")
        return file_path

    except Exception as e:
        print(f"❌ Error: {e}")
        return None
