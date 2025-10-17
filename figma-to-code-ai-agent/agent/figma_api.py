from __future__ import annotations
import requests
from typing import Any, Dict, List, Optional
from .config import Settings

FIGMA_BASE = "https://api.figma.com/v1"

class FigmaAPI:
    def __init__(self, token: str, timeout: int = 30):
        self._headers = { "X-Figma-Token": token }
        self._timeout = timeout

    def get_file(self, file_id: str) -> Dict[str, Any]:
        url = f"{FIGMA_BASE}/files/{file_id}"
        r = requests.get(url, headers=self._headers, timeout=self._timeout)
        r.raise_for_status()
        return r.json()

    def get_images(self, file_id: str, node_ids: List[str], scale: int = 2) -> Dict[str, Any]:
        ids = ",".join(node_ids)
        url = f"{FIGMA_BASE}/images/{file_id}"
        r = requests.get(url, params={"ids": ids, "scale": scale}, headers=self._headers, timeout=self._timeout)
        r.raise_for_status()
        return r.json()
