import requests
from pathlib import Path

class GraphClient:
    def __init__(self, token: str, email: str = ""):
        self.token = token
        self.email = email.strip()

    def _base_url(self):
        return f"https://graph.microsoft.com/v1.0/users/{self.email}" if self.email else "https://graph.microsoft.com/v1.0/me"

    def list_notebooks(self):
        url = f"{self._base_url()}/onenote/notebooks"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("value", [])

    def list_sections(self, notebook_id):
        url = f"{self._base_url()}/onenote/notebooks/{notebook_id}/sections"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("value", [])

    def upload_page(self, section_id, xml_path: Path, html_path: Path):
        url = f"{self._base_url()}/onenote/sections/{section_id}/pages"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        with open(xml_path, 'rb') as xml_file, open(html_path, 'rb') as html_file:
            # Must attach files in this order
            files = {
                "presentation-onenote-inkml": (xml_path.name, xml_file, "application/inkml+xml"),
                "presentation": (html_path.name, html_file, "text/html")
            }
            response = requests.post(url, headers=headers, files=files)
            response.raise_for_status()