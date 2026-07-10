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

    def __init__(self, endpoint_url: str, timeout: float = 15.0):
        self.endpoint_url = endpoint_url
        self.timeout = timeout
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
        return self._send_request(payload)

    def batch_call(self, calls: List[tuple[str, List[Any]]]) -> List[Any]:
        if not calls:
            return []

        payload = []
        for method, params in calls:
            payload.append({
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": method,
                "params": params,
            })

        res = self._send_request(payload)
        if not isinstance(res, list):
            raise RpcError(f"Expected list response for batch, got: {type(res)}")

        # Sort response items to match initial call order
        items_by_id = {item["id"]: item for item in res if isinstance(item, dict) and "id" in item}
        results = []
        for req in payload:
            item = items_by_id.get(req["id"])
            if not item:
                results.append(None)
                continue
            if "error" in item:
                err = item["error"]
                results.append(RpcError(err.get("message", "Unknown error"), err.get("code")))
            else:
                results.append(item.get("result"))
        return results

    def _send_request(self, payload: Union[Dict, List]) -> Any:
        raw_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint_url,
            data=raw_data,
            headers={"Content-Type": "application/json", "User-Agent": "token-approval-checker/0.1"},
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read()
                data = json.loads(body.decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            raise RpcError(f"HTTP {e.code}: {err_body}", code=e.code) from e
        except Exception as e:
            raise RpcError(f"RPC request failed: {e}") from e

        if isinstance(data, dict) and "error" in data:
            err = data["error"]
            raise RpcError(err.get("message", "Unknown error"), err.get("code"), err.get("data"))

        if isinstance(data, dict):
            return data.get("result")
        return data
