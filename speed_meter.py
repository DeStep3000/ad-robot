#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_REQUESTS = 10
DEFAULT_TIMEOUT = 60
CHUNK_SIZE = 1024 * 64
BYTES_IN_MB = 1_000_000


@dataclass(frozen=True)
class RequestResult:
    elapsed_seconds: float
    downloaded_bytes: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Downloads the given URL several times sequentially and prints "
            "average request time, downloaded data volume, and speed in MB/s."
        )
    )
    parser.add_argument(
        "url", help="URL to download, for example a large image or binary file"
    )
    parser.add_argument(
        "-n",
        "--requests",
        type=int,
        default=DEFAULT_REQUESTS,
        help=f"number of sequential requests, default: {DEFAULT_REQUESTS}",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"request timeout in seconds, default: {DEFAULT_TIMEOUT}",
    )
    return parser.parse_args()


def download_once(url: str, timeout: float) -> RequestResult:
    request = Request(
        url,
        headers={
            "Accept-Encoding": "identity",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": "internet-speed-meter/1.0",
        },
    )

    started_at = time.perf_counter()
    downloaded = 0

    with urlopen(request, timeout=timeout) as response:
        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            downloaded += len(chunk)

    elapsed = time.perf_counter() - started_at
    return RequestResult(elapsed_seconds=elapsed, downloaded_bytes=downloaded)


def format_mb(byte_count: int) -> float:
    return byte_count / BYTES_IN_MB


def main() -> int:
    args = parse_args()

    if args.requests <= 0:
        print("Error: --requests must be greater than 0", file=sys.stderr)
        return 2
    if args.timeout <= 0:
        print("Error: --timeout must be greater than 0", file=sys.stderr)
        return 2

    results: list[RequestResult] = []

    try:
        for index in range(1, args.requests + 1):
            result = download_once(args.url, args.timeout)
            results.append(result)
            print(
                f"{index:02d}/{args.requests}: "
                f"{result.elapsed_seconds:.3f} s, "
                f"{format_mb(result.downloaded_bytes):.2f} MB"
            )
    except HTTPError as error:
        print(f"HTTP error: {error.code} {error.reason}", file=sys.stderr)
        return 1
    except URLError as error:
        print(f"Network error: {error.reason}", file=sys.stderr)
        return 1
    except TimeoutError:
        print("Network error: request timed out", file=sys.stderr)
        return 1

    total_time = sum(result.elapsed_seconds for result in results)
    total_bytes = sum(result.downloaded_bytes for result in results)
    average_time = total_time / len(results)
    speed_mbps = format_mb(total_bytes) / total_time if total_time > 0 else 0

    print()
    print(f"Requests: {len(results)}")
    print(f"Average request time: {average_time:.3f} s")
    print(f"Downloaded data: {format_mb(total_bytes):.2f} MB ({total_bytes} bytes)")
    print(f"Speed: {speed_mbps:.2f} MB/s")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
