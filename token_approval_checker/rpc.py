import json
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Union


class RpcError(Exception):
    def __init__(self, message: str, code: Optional[int] = None, data: Any = None):
        super().__init__(message)
        self.code = code
        self.data = data


class RpcClient:
    """Minimal JSON-RPC 2.0 client using standard library http transport."""

    def __init__(self, endpoint_url: str, timeout: float = 20.0, max_retries: int = 4):
        self.endpoint_url = endpoint_url
        self.timeout = timeout
        self.max_retries = max_retries
        self._req_id = 0

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    def call(self, method: str, params: Optional[List[Any]] = None) -> Any:
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params or [],
        }
        return self._send_with_retry(payload)

    def batch_call(self, calls: List[tuple[str, List[Any]]], chunk_size: int = 100) -> List[Any]:
        if not calls:
            return []

        # Some free node providers (Infura, Ankr) drop payloads over 100 items
        all_results = []
        for i in range(0, len(calls), chunk_size):
            chunk = calls[i : i + chunk_size]
            payload = []
            for method, params in chunk:
                payload.append({
                    "jsonrpc": "2.0",
                    "id": self._next_id(),
                    "method": method,
                    "params": params,
                })

            res = self._send_with_retry(payload)
            if not isinstance(res, list):
                # QuickNode occasionally responds with a single error object instead of list
                if isinstance(res, dict) and "error" in res:
                    err = res["error"]
                    raise RpcError(err.get("message", "Unknown error"), err.get("code"))
                raise RpcError(f"Expected list response for batch, got: {type(res)}")

            items_by_id = {item["id"]: item for item in res if isinstance(item, dict) and "id" in item}
            for req in payload:
                item = items_by_id.get(req["id"])
                if not item:
                    all_results.append(None)
                    continue
                if "error" in item:
                    err = item["error"]
                    all_results.append(RpcError(err.get("message", "Unknown error"), err.get("code")))
                else:
                    all_results.append(item.get("result"))

        return all_results

    def _send_with_retry(self, payload: Union[Dict, List]) -> Any:
        attempt = 0
        backoff = 0.5

        while True:
            try:
                return self._raw_post(payload)
            except urllib.error.HTTPError as e:
                # 429 = Too Many Requests, 503 = Service Unavailable
                if e.code in (429, 503) and attempt < self.max_retries:
                    attempt += 1
                    time.sleep(backoff)
                    backoff *= 2.0
                    continue
                err_body = e.read().decode("utf-8", errors="ignore")
                raise RpcError(f"HTTP {e.code}: {err_body}", code=e.code) from e
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt < self.max_retries:
                    attempt += 1
                    time.sleep(backoff)
                    backoff *= 1.5
                    continue
                raise RpcError(f"Network error: {e}") from e

    def _raw_post(self, payload: Union[Dict, List]) -> Any:
        raw_data = json.dumps(payload).encode("utf-8")
        # print(f"DEBUG: sending {len(raw_data)} bytes")
        req = urllib.request.Request(
            self.endpoint_url,
            data=raw_data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "token-approval-checker/0.1",
                "Accept": "application/json",
            },
        )

        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            body = resp.read()
            data = json.loads(body.decode("utf-8"))

        if isinstance(data, dict) and "error" in data:
            err = data["error"]
            raise RpcError(err.get("message", "Unknown error"), err.get("code"), err.get("data"))

        if isinstance(data, dict):
            return data.get("result")
        return data
