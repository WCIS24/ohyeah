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
        "rag_survey_cn_2025",
        [
            "https://gthjjs.spacejournal.cn/en/article/pdf/preview/10.19304/J.ISSN1000-7180.2025.0652.pdf",
            "https://mc.spacejournal.cn/article/doi/10.19304/J.ISSN1000-7180.2025.0652",
            "https://doi.org/10.19304/J.ISSN1000-7180.2025.0652",
        ],
    ),
    Entry(
        "02",
        "privacy_rag_survey_cn_2025",
        [
            "https://www.arocmag.cn/abs/2025.09.0308",
            "https://doi.org/10.19734/j.issn.1001-3695.2025.09.0308",
        ],
    ),
    Entry(
        "03",
        "topic_reasoning_rag_cn_2025",
        [
            "https://www.arocmag.cn/abs/2025.03.0059",
            "https://doi.org/10.19734/j.issn.1001-3695.2025.03.0059",
        ],
    ),
    Entry(
        "04",
        "rl_query_optimization_rag_cn_2025",
        [
            "https://jns.nju.edu.cn/CN/abstract/article/0469-5097/1758",
            "https://doi.org/10.13232/j.cnki.jnju.2025.06.002",
        ],
    ),
    Entry(
        "05",
        "semantic_dense_retrieval_cn_2024",
        [
            "https://www.arocmag.cn/abs/2023.09.0412",
            "https://doi.org/10.19734/j.issn.1001-3695.2023.09.0412",
        ],
    ),
    Entry(
        "06",
        "ir_in_the_era_of_llm_ccl_2024",
        ["https://aclanthology.org/2024.ccl-2.6/"],
    ),
    Entry(
        "07",
        "policy_text_rag_cn_2025",
        [
            "https://doi.org/10.11925/infotech.2096-3467.2024.0670",
            "https://manu44.magtech.com.cn/Jwk_infotech_wk3/CN/searchresult",
        ],
    ),
    Entry(
        "08",
        "campus_qa_intent_rag_cn_2024",
        [
            "https://www.joconline.com.cn/zh/article/doi/10.11959/j.issn.1000-436x.2024245",
            "https://doi.org/10.11959/j.issn.1000-436x.2024245",
        ],
    ),
    Entry(
        "09",
        "knowledge_empowered_info_system_cn_2023",
        [
            "https://doi.org/10.13328/j.cnki.jos.006884",
            "https://www.jos.org.cn/jos/article/issue/2023_34_10",
        ],
    ),
    Entry(
        "10",
        "rag_for_knowledge_intensive_nlp_2020",
        [
            "https://arxiv.org/pdf/2005.11401.pdf",
            "https://doi.org/10.48550/arXiv.2005.11401",
            "https://nlp.cs.ucl.ac.uk/publications/2020-05-retrieval-augmented-generation-for-knowledge-intensive-nlp-tasks/",
        ],
    ),
    Entry(
        "11",
        "dense_passage_retrieval_2020",
        [
            "https://aclanthology.org/2020.emnlp-main.550.pdf",
            "https://aclanthology.org/2020.emnlp-main.550/",
            "https://doi.org/10.18653/v1/2020.emnlp-main.550",
        ],
    ),
    Entry(
        "12",
        "bm25_and_beyond_2009",
        [
            "https://doi.org/10.1561/1500000019",
            "https://colab.ws/articles/10.1561%2F1500000019",
            "https://api.crossref.org/works/10.1561/1500000019",
        ],
    ),
    Entry(
        "13",
        "relevance_based_language_models_2001",
        [
            "https://ciir-publications.cs.umass.edu/getpdf.php?id=429",
            "https://dl.acm.org/doi/pdf/10.1145/383952.383972",
            "https://doi.org/10.1145/383952.383972",
            "https://api.crossref.org/works/10.1145/383952.383972",
        ],
    ),
    Entry(
        "14",
        "reciprocal_rank_fusion_2009",
        [
            "https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf",
            "https://doi.org/10.1145/1571941.1572114",
            "https://colab.ws/articles/10.1145/1571941.1572114",
            "https://api.crossref.org/works/10.1145/1571941.1572114",
        ],
    ),
    Entry(
        "15",
        "sentence_bert_2019",
        [
            "https://arxiv.org/pdf/1908.10084.pdf",
            "https://doi.org/10.48550/arXiv.1908.10084",
        ],
    ),
    Entry(
        "16",
        "colbert_2020",
        [
            "https://doi.org/10.1145/3397271.3401075",
            "https://arxiv.org/pdf/2004.12832.pdf",
        ],
    ),
    Entry(
        "17",
        "fid_2021",
        [
            "https://aclanthology.org/2021.eacl-main.74.pdf",
            "https://aclanthology.org/2021.eacl-main.74/",
            "https://arxiv.org/pdf/2007.01282.pdf",
        ],
    ),
    Entry(
        "18",
        "realm_2020",
        [
            "https://arxiv.org/pdf/2002.08909.pdf",
            "https://arxiv.org/abs/2002.08909",
        ],
    ),
    Entry(
        "19",
        "retro_2022",
        [
            "https://arxiv.org/pdf/2112.04426.pdf",
            "https://doi.org/10.48550/arXiv.2112.04426",
        ],
    ),
    Entry(
        "20",
        "finqa_2021",
        [
            "https://aclanthology.org/2021.emnlp-main.300.pdf",
            "https://aclanthology.org/2021.emnlp-main.300/",
            "https://doi.org/10.18653/v1/2021.emnlp-main.300",
        ],
    ),
    Entry(
        "21",
        "tat_qa_2021",
        [
            "https://aclanthology.org/2021.acl-long.254.pdf",
            "https://aclanthology.org/2021.acl-long.254/",
            "https://doi.org/10.18653/v1/2021.acl-long.254",
        ],
    ),
    Entry(
        "22",
        "finder_2025",
        [
            "https://arxiv.org/pdf/2504.15800.pdf",
            "https://doi.org/10.48550/arXiv.2504.15800",
            "https://huggingface.co/datasets/Linq-AI-Research/FinDER",
        ],
    ),
    Entry(
        "23",
        "t2_ragbench_2025",
        [
            "https://arxiv.org/pdf/2506.12071.pdf",
            "https://doi.org/10.48550/arXiv.2506.12071",
        ],
    ),
    Entry(
        "24",
        "survey_on_rag_with_llms_2024",
        [
            "https://doi.org/10.1016/j.procs.2024.09.178",
            "https://www.fmread.com/pdfshare/4w4puxd",
        ],
    ),
    Entry(
        "25",
        "toolformer_2023",
        [
            "https://arxiv.org/pdf/2302.04761.pdf",
            "https://doi.org/10.48550/arXiv.2302.04761",
            "https://www.scixplorer.org/abs/2023arXiv230204761S/abstract",
        ],
    ),
    Entry(
        "26",
        "react_2022",
        [
            "https://arxiv.org/pdf/2210.03629.pdf",
            "https://doi.org/10.48550/arXiv.2210.03629",
            "https://bohrium.dp.tech/paper/arxiv/2210.03629",
        ],
    ),
    Entry(
        "27",
        "pal_2023",
        [
            "https://proceedings.mlr.press/v202/gao23f/gao23f.pdf",
            "https://proceedings.mlr.press/v202/gao23f.html",
            "https://proceedings.mlr.press/v202/gao23f/",
        ],
    ),
    Entry(
        "28",
        "investor_gov_form_10k",
        [
            "https://www.investor.gov/additional-resources/general-resources/glossary/form-10-k",
        ],
    ),
    Entry(
        "29",
        "sec_how_to_read_10k",
        [
            "https://r.jina.ai/http://www.sec.gov/answers/reada10k.htm",
            "https://www.sec.gov/answers/reada10k.htm",
        ],
    ),
]


def sanitize_filename(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", name).strip("_")


def fetch_url(url: str, timeout: int = 45) -> tuple[bytes, str, str]:
    parts = urlsplit(url)
    normalized_url = urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            quote(unquote(parts.path), safe="/%:@+~!$&'()*,;=-._"),
            quote(unquote(parts.query), safe="=&/?%:@+~!$'()*,;,-._"),
            "",
        )
    )
    request = Request(
        normalized_url,
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
    return candidates[:8]


def write_binary(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


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
                file_name = f"{entry.ref_id}_{sanitize_filename(entry.name)}.pdf"
                file_path = output_dir / file_name
                write_binary(file_path, data)
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

            pdf_links = extract_pdf_links(data, final_url)
            for pdf_link in pdf_links:
                try:
                    pdf_data, pdf_type, pdf_final = fetch_url(pdf_link)
                    if looks_like_pdf(pdf_data, pdf_type, pdf_final, pdf_link):
                        file_name = f"{entry.ref_id}_{sanitize_filename(entry.name)}.pdf"
                        file_path = output_dir / file_name
                        write_binary(file_path, pdf_data)
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

            if "application/json" in content_type:
                extension = "json"
                status = "ok_json"
            elif "text/plain" in content_type:
                extension = "txt"
                status = "ok_text"
            else:
                extension = "html"
                status = "ok_html"

            file_name = f"{entry.ref_id}_{sanitize_filename(entry.name)}.{extension}"
            file_path = output_dir / file_name
            write_binary(file_path, data)
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


def write_manifest(rows: Iterable[dict[str, str]], output_dir: Path) -> tuple[Path, Path]:
    manifest_path = output_dir / "download_manifest.csv"
    failure_path = output_dir / "download_failures.txt"
    rows = list(rows)

    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["ref_id", "name", "status", "source_url", "final_url", "file", "error"],
        )
        writer.writeheader()
        writer.writerows(rows)

    failures = [r for r in rows if not r["status"].startswith("ok_")]
    with failure_path.open("w", encoding="utf-8") as f:
        for item in failures:
            f.write(
                f"[{item['ref_id']}] {item['name']} | {item['error'] or 'unknown error'}\n"
            )
    return manifest_path, failure_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Download reference papers and pages.")
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory for downloaded files and manifest outputs.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    results = [try_download_entry(entry, output_dir) for entry in ENTRIES]
    manifest_path, failure_path = write_manifest(results, output_dir)

    success = sum(1 for item in results if item["status"].startswith("ok_"))
    failures = len(results) - success
    print(f"Downloaded entries: {success}/{len(results)}")
    print(f"Manifest: {manifest_path}")
    print(f"Failures: {failure_path} ({failures} entries)")


if __name__ == "__main__":
    main()
