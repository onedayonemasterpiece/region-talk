from __future__ import annotations

"""Region Talk compatibility layer for the proven events-bot Kaggle runtime.

The API shapes and failure handling are adapted from:
`onedayonemasterpiece/events-bot-new@5bbdb681623d5e4e0bff2133e487a6663c1a838a`
`video_announce/kaggle_client.py`, blob
`9c552e12b001f7a1a3b213369a74da8ebd7a0b32`.

This module is the only place in Region Talk allowed to import the Kaggle SDK.
It deliberately contains no Event/Video domain scoring.
"""

import asyncio
import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any

KaggleApi = None  # type: ignore[assignment]
_KAGGLE_IMPORT_ERROR: Exception | None = None

try:  # pragma: no cover - optional dependency in contract-only environments
    from kaggle.api.kaggle_api_extended import KaggleApi as ImportedKaggleApi
except SystemExit as exc:  # pragma: no cover
    _KAGGLE_IMPORT_ERROR = exc
except Exception as exc:  # pragma: no cover
    _KAGGLE_IMPORT_ERROR = exc
else:
    KaggleApi = ImportedKaggleApi  # type: ignore[assignment]


logger = logging.getLogger(__name__)


def _response_error_suffix(exc: Exception) -> str:
    response = getattr(exc, "response", None)
    if response is None:
        return ""
    status_code = getattr(response, "status_code", None)
    try:
        body = str(response.text or "").strip()
    except Exception:
        body = ""
    parts: list[str] = []
    if status_code is not None:
        parts.append(f"status={status_code}")
    if body:
        parts.append(body[:800])
    return f" ({'; '.join(parts)})" if parts else ""


def _normalize_kernel_status(response: Any) -> dict[str, Any]:
    if hasattr(response, "to_dict"):
        raw = response.to_dict()
        result = dict(raw) if isinstance(raw, dict) else {}
    else:
        try:
            parsed = json.loads(str(response))
        except (json.JSONDecodeError, TypeError, ValueError):
            parsed = {}
        result = dict(parsed) if isinstance(parsed, dict) else {}

    if not result.get("status"):
        status_value = getattr(response, "status", None)
        if status_value is not None:
            result["status"] = (
                status_value.name if hasattr(status_value, "name") else str(status_value)
            )
    if not result.get("failureMessage"):
        failure = getattr(response, "failure_message", None) or getattr(
            response, "failureMessage", None
        )
        if failure:
            result["failureMessage"] = str(failure)
    return result


class KaggleRuntimeClient:
    """Single Region Talk adapter over the official Kaggle client.

    An injected ``api`` is supported for deterministic tests. Production uses
    the same lazy authentication pattern as events-bot.
    """

    def __init__(self, api: Any | None = None) -> None:
        self._api = api

    def _get_api(self) -> Any:
        if self._api is None:
            if KaggleApi is None:
                raise RuntimeError(
                    "Kaggle API is unavailable. Install the runtime extra and configure credentials."
                ) from _KAGGLE_IMPORT_ERROR
            api = KaggleApi()
            api.authenticate()
            self._api = api
        return self._api

    def create_dataset(
        self,
        folder: str | Path,
        *,
        public: bool = False,
        quiet: bool = True,
        convert_to_csv: bool = False,
        dir_mode: str = "zip",
    ) -> None:
        api = self._get_api()
        logger.info("kaggle: creating dataset from folder=%s", folder)
        try:
            api.dataset_create_new(
                str(folder),
                public=public,
                quiet=quiet,
                convert_to_csv=convert_to_csv,
                dir_mode=dir_mode,
            )
        except Exception as exc:
            raise RuntimeError(
                "Kaggle dataset_create_new failed" + _response_error_suffix(exc)
            ) from exc

    def create_dataset_version(
        self,
        folder: str | Path,
        *,
        version_notes: str = "update",
        quiet: bool = True,
        convert_to_csv: bool = False,
        delete_old_versions: bool = False,
        dir_mode: str = "zip",
    ) -> None:
        api = self._get_api()
        try:
            api.dataset_create_version(
                str(folder),
                version_notes=version_notes,
                quiet=quiet,
                convert_to_csv=convert_to_csv,
                delete_old_versions=delete_old_versions,
                dir_mode=dir_mode,
            )
        except Exception as exc:
            raise RuntimeError(
                "Kaggle dataset_create_version failed" + _response_error_suffix(exc)
            ) from exc

    def dataset_status(self, dataset: str) -> str:
        return str(self._get_api().dataset_status(dataset))

    def dataset_list_files(
        self, dataset: str, *, page_size: int = 20
    ) -> list[dict[str, Any]]:
        api = self._get_api()
        result: list[dict[str, Any]] = []
        seen_names: set[str] = set()
        next_page_token: str | None = None
        while True:
            response = api.dataset_list_files(
                dataset,
                page_token=next_page_token,
                page_size=page_size,
            )
            files = getattr(response, "files", None)
            if files is None and isinstance(response, list):
                files = response
            for item in files or []:
                name = getattr(item, "name", None) or (
                    item.get("name") if isinstance(item, dict) else str(item)
                )
                name = str(name or "").strip()
                if not name or name in seen_names:
                    continue
                seen_names.add(name)
                result.append(
                    {
                        "name": name,
                        "totalBytes": getattr(item, "totalBytes", None),
                        "creationDate": getattr(item, "creationDate", None),
                    }
                )
            next_page_token = (
                getattr(response, "nextPageToken", None)
                or getattr(response, "next_page_token", None)
                or None
            )
            if not next_page_token or isinstance(response, list):
                break
        return result

    def delete_dataset(self, dataset: str, *, no_confirm: bool = True) -> None:
        api = self._get_api()
        if "/" in dataset:
            owner, slug = dataset.split("/", 1)
        else:
            owner = (os.getenv("KAGGLE_USERNAME") or "").strip()
            slug = dataset
        if not owner or not slug:
            raise ValueError(f"Invalid Kaggle dataset ref: {dataset!r}")
        try:
            api.dataset_delete(owner, slug, no_confirm=no_confirm)
        except Exception as exc:
            raise RuntimeError(
                f"Kaggle dataset_delete failed for {owner}/{slug}"
                + _response_error_suffix(exc)
            ) from exc

    def kernels_list(self, user: str, *, page_size: int = 20) -> list[dict[str, Any]]:
        kernels = self._get_api().kernels_list(user=user, page_size=page_size)
        return [
            {
                "ref": getattr(item, "ref", ""),
                "title": getattr(item, "title", ""),
                "slug": getattr(item, "slug", ""),
                "lastRunTime": getattr(item, "lastRunTime", None),
            }
            for item in kernels or []
        ]

    def kernels_pull(
        self, kernel_ref: str, path: str | Path, *, metadata: bool = True
    ) -> None:
        self._get_api().kernels_pull(kernel_ref, path=str(path), metadata=metadata)

    def get_kernel_status(self, kernel_ref: str) -> dict[str, Any]:
        response = self._get_api().kernels_status(kernel_ref)
        result = _normalize_kernel_status(response)
        logger.info(
            "kaggle: kernel status kernel=%s status=%s failure=%s",
            kernel_ref,
            result.get("status"),
            result.get("failureMessage") or result.get("failure_message"),
        )
        return result

    def kernel_has_dataset_sources(
        self, kernel_ref: str, expected_sources: list[str]
    ) -> tuple[bool, dict[str, Any]]:
        expected = [str(item).strip() for item in expected_sources if str(item).strip()]
        if not expected:
            return True, {"dataset_sources": []}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.kernels_pull(kernel_ref, root, metadata=True)
            metadata_path = root / "kernel-metadata.json"
            if not metadata_path.exists():
                raise FileNotFoundError(
                    f"kernel-metadata.json not found after pulling {kernel_ref}"
                )
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        actual = [
            str(item).strip()
            for item in (metadata.get("dataset_sources") or [])
            if str(item).strip()
        ]
        metadata["dataset_sources"] = actual
        return all(item in actual for item in expected), metadata

    def download_kernel_output(
        self,
        kernel_ref: str,
        *,
        path: str | Path,
        force: bool = True,
        quiet: bool = False,
    ) -> list[str]:
        files, _ = self._get_api().kernels_output(
            kernel_ref,
            path=str(path),
            force=force,
            quiet=quiet,
        )
        return [str(item) for item in files or []]


async def await_dataset_ready(
    client: KaggleRuntimeClient,
    dataset_ref: str,
    *,
    timeout_seconds: int = 180,
    poll_interval_seconds: int = 5,
    expected_files: list[str] | None = None,
) -> dict[str, Any]:
    expected = [str(item).strip() for item in (expected_files or []) if str(item).strip()]
    deadline = time.monotonic() + max(1, int(timeout_seconds))
    last_status = ""
    last_files: list[str] = []
    last_error = ""
    while time.monotonic() < deadline:
        try:
            last_status = await asyncio.to_thread(client.dataset_status, dataset_ref)
            files = await asyncio.to_thread(
                client.dataset_list_files,
                dataset_ref,
                page_size=max(20, len(expected) + 5),
            )
            last_files = [str(item.get("name") or "") for item in files]
            if last_status.strip().lower() == "ready" and all(
                item in last_files for item in expected
            ):
                return {"status": last_status, "files": last_files}
            last_error = ""
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        await asyncio.sleep(max(1, int(poll_interval_seconds)))
    raise TimeoutError(
        "Kaggle dataset did not become ready "
        f"dataset={dataset_ref} status={last_status or '-'} files={last_files} "
        f"expected={expected} last_error={last_error or '-'}"
    )


async def await_kernel_dataset_sources(
    client: KaggleRuntimeClient,
    kernel_ref: str,
    expected_sources: list[str],
    *,
    timeout_seconds: int = 120,
    poll_interval_seconds: int = 10,
) -> dict[str, Any]:
    expected = [str(item).strip() for item in expected_sources if str(item).strip()]
    if not expected:
        return {"dataset_sources": []}
    deadline = time.monotonic() + max(1, int(timeout_seconds))
    last_metadata: dict[str, Any] = {}
    last_error = ""
    while time.monotonic() < deadline:
        try:
            matched, last_metadata = await asyncio.to_thread(
                client.kernel_has_dataset_sources, kernel_ref, expected
            )
            if matched:
                return last_metadata
            last_error = ""
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        await asyncio.sleep(max(1, int(poll_interval_seconds)))
    raise TimeoutError(
        "Kaggle kernel metadata did not bind expected datasets "
        f"kernel={kernel_ref} expected={expected} "
        f"actual={last_metadata.get('dataset_sources') or []} "
        f"last_error={last_error or '-'}"
    )
