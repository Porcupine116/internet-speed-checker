import argparse
import statistics
import sys
import time
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

REQUEST_COUNT = 10
CHUNK_SIZE = 64 * 1024
TIMEOUT_SECONDS = 30
USER_AGENT = "internet-speed-checker/1.0"


def validate_url(value: str) -> str:
    parsed_url = urlsplit(value)
    if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
        raise argparse.ArgumentTypeError(
            "Укажите полный URL, начинающийся с http:// или https://"
        )
    return value


def download_once(url: str) -> tuple[float, int]:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    downloaded_bytes = 0
    started_at = time.perf_counter()

    with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        if not 200 <= response.status < 300:
            raise RuntimeError(f"Сервер вернул HTTP-статус {response.status}")

        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            downloaded_bytes += len(chunk)

    elapsed_seconds = time.perf_counter() - started_at
    return elapsed_seconds, downloaded_bytes


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Последовательно скачивает один URL 10 раз и измеряет скорость."
    )
    parser.add_argument(
        "url",
        type=validate_url,
        help="Полный адрес HTTP(S)-ресурса, например https://example.com/image.jpg",
    )
    args = parser.parse_args()

    request_times: list[float] = []
    total_downloaded_bytes = 0

    print(f"Запускаю {REQUEST_COUNT} последовательных запросов: {args.url}")
    total_started_at = time.perf_counter()

    try:
        for _ in range(REQUEST_COUNT):
            elapsed_seconds, downloaded_bytes = download_once(args.url)
            request_times.append(elapsed_seconds)
            total_downloaded_bytes += downloaded_bytes
    except (URLError, TimeoutError, OSError, RuntimeError) as error:
        print(f"Ошибка при загрузке: {error}", file=sys.stderr)
        return 1

    total_elapsed_seconds = time.perf_counter() - total_started_at
    average_request_seconds = statistics.mean(request_times)

    total_megabytes = total_downloaded_bytes / 1_000_000
    speed_mbps = (
        total_downloaded_bytes * 8 / total_elapsed_seconds / 1_000_000
        if total_elapsed_seconds > 0
        else 0.0
    )

    print("\nРезультаты:")
    print(f"Количество запросов: {REQUEST_COUNT}")
    print(f"Среднее время одного запроса: {average_request_seconds:.3f} с")
    print(f"Общее время загрузки: {total_elapsed_seconds:.3f} с")
    print(f"Всего скачано: {total_megabytes:.3f} MB")
    print(f"Средняя скорость скачивания: {speed_mbps:.2f} Мбит/с")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
