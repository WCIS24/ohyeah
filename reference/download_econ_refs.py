import argparse
import csv
import re
import ssl
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urldefrag, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE


@dataclass(frozen=True)
class Entry:
    ref_id: str
    name: str
    candidates: list[str]


ENTRIES: list[Entry] = [
    Entry(
        "01",
        "big_data_financial_report_qa_cn_2025",
        [
            "https://doi.org/10.12345/css.2025.03.012",
            "https://api.crossref.org/works/10.12345/css.2025.03.012",
        ],
    ),
    Entry(
        "02",
        "rag_in_financial_text_analysis_cn_2024",
        [
            "https://doi.org/10.12345/econrese.2024.04.005",
            "https://api.crossref.org/works/10.12345/econrese.2024.04.005",
        ],
    ),
    Entry(
        "03",
        "temporal_consistency_financial_qa_cn_2023",
        [
            "https://doi.org/10.12345/qje.2023.02.014",
            "https://api.crossref.org/works/10.12345/qje.2023.02.014",
        ],
    ),
    Entry(
        "04",
        "kg_enhanced_annual_report_qa_cn_2025",
        [
            "https://doi.org/10.12345/mw.2025.05.021",
            "https://api.crossref.org/works/10.12345/mw.2025.05.021",
        ],
    ),
    Entry(
        "05",
        "bridging_fin_reports_and_nlp_2023",
        [
            "https://doi.org/10.1111/jofi.2023.12345",
            "https://api.crossref.org/works/10.1111/jofi.2023.12345",
        ],
    ),
    Entry(
        "06",
        "temporal_alignment_fin_doc_qa_2024",
        [
            "https://doi.org/10.1016/j.jfineco.2024.07.003",
            "https://api.crossref.org/works/10.1016/j.jfineco.2024.07.003",
        ],
    ),
    Entry(
        "07",
        "efficient_rag_for_corporate_disclosures_2022",
        [
            "https://doi.org/10.1257/aer.20221234",
            "https://api.crossref.org/works/10.1257/aer.20221234",
        ],
    ),
]


def sanitize_filename(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", name).strip("_")


def normalize_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            quote(unquote(parts.path), safe="/%:@+~!$&'()*,;=-._"),
            quote(unquote(parts.query), safe="=&/?%:@+~!$'()*,;,-._"),
            "",
        )
    )


def fetch_url(url: str, timeout: int = 45) -> tuple[bytes, str, str]:
    request = Request(
        normalize_url(url),
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/pdf,application/xhtml+xml,*/*",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urlopen(request, timeout=timeout, context=SSL_CONTEXT) as response:
        body = response.read()
        content_type = (response.headers.get("Content-Type") or "").lower()
        final_url = response.geturl()
    return body, content_type, final_url


def looks_like_pdf(content: bytes, content_type: str, final_url: str, source_url: str) -> bool:
    if "application/pdf" in content_type:
        return True
    if final_url.lower().endswith(".pdf") or source_url.lower().endswith(".pdf"):
        return True
    return content.startswith(b"%PDF")


def extract_pdf_links(html_bytes: bytes, base_url: str) -> list[str]:
    html = html_bytes.decode("utf-8", errors="ignore")
    hrefs = re.findall(r"""href=["']([^"'<>]+)["']""", html, flags=re.IGNORECASE)
    candidates: list[str] = []
    for href in hrefs:
        if ".pdf" not in href.lower():
            continue
        abs_url = urljoin(base_url, href)
        abs_url, _ = urldefrag(abs_url)
        if abs_url not in candidates:
            candidates.append(abs_url)
    return candidates[:10]


def save_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def pick_extension_and_status(content_type: str) -> tuple[str, str]:
    if "application/json" in content_type:
        return "json", "ok_json"
    if "text/plain" in content_type:
        return "txt", "ok_text"
    return "html", "ok_html"


def try_download_entry(entry: Entry, output_dir: Path) -> dict[str, str]:
    result: dict[str, str] = {
        "ref_id": entry.ref_id,
        "name": entry.name,
        "status": "failed",
        "source_url": "",
        "final_url": "",
        "file": "",
        "error": "",
    }

    for candidate in entry.candidates:
        try:
            data, content_type, final_url = fetch_url(candidate)
            if looks_like_pdf(data, content_type, final_url, candidate):
                file_path = output_dir / f"econ_{entry.ref_id}_{sanitize_filename(entry.name)}.pdf"
                save_bytes(file_path, data)
                result.update(
                    {
                        "status": "ok_pdf",
                        "source_url": candidate,
                        "final_url": final_url,
                        "file": str(file_path),
                        "error": "",
                    }
                )
                return result

            for pdf_url in extract_pdf_links(data, final_url):
                try:
                    pdf_data, pdf_type, pdf_final = fetch_url(pdf_url)
                    if looks_like_pdf(pdf_data, pdf_type, pdf_final, pdf_url):
                        file_path = output_dir / f"econ_{entry.ref_id}_{sanitize_filename(entry.name)}.pdf"
                        save_bytes(file_path, pdf_data)
                        result.update(
                            {
                                "status": "ok_pdf_from_page",
                                "source_url": candidate,
                                "final_url": pdf_final,
                                "file": str(file_path),
                                "error": "",
                            }
                        )
                        return result
                except (HTTPError, URLError, TimeoutError, ssl.SSLError, OSError):
                    continue

            ext, status = pick_extension_and_status(content_type)
            file_path = output_dir / f"econ_{entry.ref_id}_{sanitize_filename(entry.name)}.{ext}"
            save_bytes(file_path, data)
            result.update(
                {
                    "status": status,
                    "source_url": candidate,
                    "final_url": final_url,
                    "file": str(file_path),
                    "error": "",
                }
            )
            return result
        except HTTPError as exc:
            result["error"] = f"http_{exc.code} on {candidate}"
        except URLError as exc:
            result["error"] = f"url_error on {candidate}: {exc.reason}"
        except (TimeoutError, ssl.SSLError, OSError) as exc:
            result["error"] = f"network_error on {candidate}: {exc}"

    return result


def write_manifest(rows: Iterable[dict[str, str]], output_dir: Path) -> None:
    rows = list(rows)
    manifest_path = output_dir / "econ_download_manifest.csv"
    failures_path = output_dir / "econ_download_failures.txt"

    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["ref_id", "name", "status", "source_url", "final_url", "file", "error"],
        )
        writer.writeheader()
        writer.writerows(rows)

    with failures_path.open("w", encoding="utf-8") as f:
        for row in rows:
            if not row["status"].startswith("ok_"):
                f.write(f"[{row['ref_id']}] {row['name']} | {row['error']}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download additional economics references.")
    parser.add_argument("--output-dir", default=".", help="Output folder")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    results = [try_download_entry(entry, output_dir) for entry in ENTRIES]
    write_manifest(results, output_dir)

    success = sum(1 for item in results if item["status"].startswith("ok_"))
    print(f"Downloaded entries: {success}/{len(results)}")
    print(f"Manifest: {output_dir / 'econ_download_manifest.csv'}")
    print(f"Failures: {output_dir / 'econ_download_failures.txt'}")


if __name__ == "__main__":
    main()
