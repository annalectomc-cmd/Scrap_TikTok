"""Administración en memoria de trabajos de scraping interactivos.

Esta primera versión trabaja con un único navegador/display, así que ejecuta
un solo trabajo a la vez. Para múltiples réplicas se debe reemplazar por una
cola persistente y un almacén compartido (por ejemplo Redis y Celery/RQ).
"""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
import os
from threading import RLock
from typing import Any
from uuid import uuid4

from app.scrap.service import ScrapingService


class ScrapingJobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}
        self._lock = RLock()
        # Un display noVNC representa un navegador; dos trabajos simultáneos
        # mezclarían sus pantallas y no serían seguros.
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="scraping")

    def create(self, parameters: dict[str, Any]) -> dict[str, Any]:
        job_id = str(uuid4())
        job = {
            "id": job_id,
            "status": "queued",
            "created_at": self._now(),
            "updated_at": self._now(),
            "parameters": parameters,
            "error": None,
            "comments": None,
            "videos": None,
        }
        with self._lock:
            self._jobs[job_id] = job

        self._executor.submit(self._run, job_id)
        return self.get(job_id)

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            result = deepcopy(job)

        # La pantalla se comparte por noVNC sólo mientras este trabajo espera
        # una acción humana. Nunca se devuelve para otro estado.
        if result["status"] == "captcha_required":
            result["browser_url"] = os.getenv(
                "NOVNC_PUBLIC_URL",
                "http://localhost:6080/vnc.html?autoconnect=true&resize=scale",
            )
        return result

    def _run(self, job_id: str) -> None:
        self._update(job_id, status="running")
        parameters = self._parameters_for(job_id)
        if parameters is None:
            return

        try:
            comments, videos = ScrapingService.scrape(
                **parameters,
                captcha_callback=lambda detected: self._captcha_changed(job_id, detected),
            )
        except Exception as error:  # El mensaje se presenta al cliente, sin traceback interno.
            self._update(job_id, status="failed", error=str(error))
        else:
            self._update(
                job_id,
                status="completed",
                comments=comments,
                videos=videos,
            )

    def _captcha_changed(self, job_id: str, detected: bool) -> None:
        self._update(job_id, status="captcha_required" if detected else "running")

    def _parameters_for(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return deepcopy(job["parameters"]) if job else None

    def _update(self, job_id: str, **fields: Any) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is not None:
                job.update(fields)
                job["updated_at"] = self._now()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()


scraping_jobs = ScrapingJobManager()
