"""Single atomic write class: pass any args; it performs the save."""

import json
import os
import threading
from pathlib import Path


class AtomicWriter:
    def __init__(self, encoding: str = "utf-8") -> None:
        self.encoding = encoding

    def write_text(self, path, text: str) -> None:
        self._atomic_replace(Path(path), text)

    def write_json(self, path, data,indent: int = 2) -> None:
        self._atomic_replace(Path(path), json.dumps(data, indent=indent))

    def _atomic_replace(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_file = path.with_name(path.name + f".{threading.get_ident()}.tmp")
        try:
            with open(temp_file, "w", encoding=self.encoding) as f:
                f.write(text)
            os.replace(temp_file, path)
        except OSError:
            try:
                os.unlink(temp_file)
            except OSError:
                pass
            raise
