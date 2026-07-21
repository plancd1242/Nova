from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import tempfile
from urllib.request import urlopen
from zipfile import ZipFile

from nova.config import ROOT_DIR, settings


@dataclass(frozen=True)
class VoskModelResult:
    ok: bool
    message: str
    path: Path


class VoskModelManager:
    def __init__(self) -> None:
        self.model_path = self._model_path()

    def ensure_model(self) -> VoskModelResult:
        if self.is_ready():
            return VoskModelResult(True, f"Vosk model is ready at {self.model_path}.", self.model_path)
        if not settings.vosk_model_auto_download:
            return VoskModelResult(False, f"Vosk model is missing at {self.model_path}.", self.model_path)
        return self.download_model()

    def download_model(self) -> VoskModelResult:
        if self.is_ready():
            return VoskModelResult(True, f"Vosk model is already installed at {self.model_path}.", self.model_path)
        if not settings.vosk_model_url:
            return VoskModelResult(False, "Vosk model URL is not configured.", self.model_path)

        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with tempfile.TemporaryDirectory(prefix="nova_vosk_") as tmp:
                tmp_path = Path(tmp)
                zip_path = tmp_path / "model.zip"
                self._download(settings.vosk_model_url, zip_path)
                extracted_root = tmp_path / "extracted"
                extracted_root.mkdir()
                with ZipFile(zip_path) as archive:
                    archive.extractall(extracted_root)
                source = self._find_model_dir(extracted_root)
                if source is None:
                    return VoskModelResult(False, "Downloaded file did not contain a recognizable Vosk model.", self.model_path)
                if self.model_path.exists():
                    shutil.rmtree(self.model_path)
                shutil.move(str(source), str(self.model_path))
            if self.is_ready():
                return VoskModelResult(True, f"Vosk model downloaded to {self.model_path}.", self.model_path)
            return VoskModelResult(False, "Vosk model download finished, but the model could not be verified.", self.model_path)
        except Exception as exc:
            return VoskModelResult(False, f"Vosk model download failed: {type(exc).__name__}.", self.model_path)

    def is_ready(self) -> bool:
        return self._looks_like_model(self.model_path)

    def _download(self, url: str, target: Path) -> None:
        with urlopen(url, timeout=60) as response:
            with target.open("wb") as handle:
                shutil.copyfileobj(response, handle)

    def _find_model_dir(self, root: Path) -> Path | None:
        for path in [root, *root.iterdir()]:
            if path.is_dir() and self._looks_like_model(path):
                return path
        for path in root.rglob("*"):
            if path.is_dir() and self._looks_like_model(path):
                return path
        return None

    def _looks_like_model(self, path: Path) -> bool:
        return path.exists() and path.is_dir() and (path / "conf").is_dir() and ((path / "am").exists() or (path / "graph").exists())

    def _model_path(self) -> Path:
        path = Path(settings.vosk_model_path)
        return path if path.is_absolute() else ROOT_DIR / path


def get_vosk_model_manager() -> VoskModelManager:
    return VoskModelManager()
