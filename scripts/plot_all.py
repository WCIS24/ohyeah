from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from cycler import cycler  # noqa: E402

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.utils import generate_run_id, get_git_hash  # noqa: E402

from plot_utils import (  # noqa: E402
    best_and_second,
    choose_k_values,
    data_root_from_config,
    ensure_dir,
    extract_summary_metrics,
    find_existing_file,
    format_value,
    get_role_map,
    load_json,
    load_jsonl,
    load_yaml,
    output_root_from_config,
    parse_metric_k,
    read_experiments,
    resolve_role,
    role_style,
    save_yaml,
    set_seed,
    style_dir_from_config,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate thesis figures/tables")
    parser.add_argument(
        "--config",
        default="scripts/plot_config.yaml",
        help="Plot config YAML",
    )
    parser.add_argument("--theme", default=None, help="Theme name (ThemeA/ThemeB/ThemeC)")
    parser.add_argument("--all-themes", action="store_true", help="Render all themes")
    return parser.parse_args()


def _theme_style_path(style_dir: str, theme: str) -> Optional[str]:
    direct = os.path.join(style_dir, f"{theme}.mplstyle")
    if os.path.exists(direct):
        return direct
    lowered = theme[:1].lower() + theme[1:]
    alt = os.path.join(style_dir, f"{lowered}.mplstyle")
    if os.path.exists(alt):
        return alt
    if theme.lower().startswith("theme"):
        suffix = theme[5:]
        alt2 = os.path.join(style_dir, f"theme{suffix}.mplstyle")
        if os.path.exists(alt2):
            return alt2
    return None


def apply_style(style_dir: str, theme: str, palette: Dict[str, Any], logger) -> None:
    base_style = os.path.join(style_dir, "thesis_base.mplstyle")
    theme_style = _theme_style_path(style_dir, theme)
    styles = []
    if os.path.exists(base_style):
        styles.append(base_style)
    if theme_style:
        styles.append(theme_style)
    if styles:
        plt.style.use(styles)
        logger.info("style_used=%s", styles)
    else:
        logger.warning("style_not_found base=%s theme=%s", base_style, theme_style)

    theme_cfg = palette.get("themes", {}).get(theme, {})
    colors = theme_cfg.get("colors", {})
    cycle = theme_cfg.get("cycle", [])
    if cycle:
        plt.rcParams["axes.prop_cycle"] = cycler(color=cycle)
    if colors:
        plt.rcParams["figure.facecolor"] = colors.get("background", "white")
        plt.rcParams["axes.facecolor"] = colors.get("background", "white")
        plt.rcParams["axes.edgecolor"] = colors.get("neutral", "black")
        plt.rcParams["axes.labelcolor"] = colors.get("text", "black")
        plt.rcParams["text.color"] = colors.get("text", "black")
        plt.rcParams["xtick.color"] = colors.get("text", "black")
        plt.rcParams["ytick.color"] = colors.get("text", "black")
        plt.rcParams["grid.color"] = colors.get("grid", "0.85")


def collect_table_rows(
    experiments: List[Dict[str, Any]],
    data_root: str,
    summary_filename: str,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for exp in experiments:
        run_id = exp.get("run_id")
        label = exp.get("label", run_id)
        run_dir = os.path.join(data_root, str(run_id))
        summary_path = os.path.join(run_dir, summary_filename)
        metrics = {}
        if os.path.exists(summary_path):
            summary = load_json(summary_path)
            metrics = extract_summary_metrics(summary)
        rows.append(
            {
                "label": label,
                "run_id": run_id,
                **metrics,
            }
        )
    return rows


def write_main_results_table(
    rows: List[Dict[str, Any]],
    columns: List[Dict[str, Any]],
    digits: int,
    csv_path: str,
    tex_path: str,
    logger,
) -> Dict[str, Any]:
    ensure_dir(os.path.dirname(csv_path))
    ensure_dir(os.path.dirname(tex_path))
    with open(csv_path, "w", encoding="utf-8") as f:
        headers = ["label"] + [c["key"] for c in columns]
        f.write(",".join(headers) + "\n")
        for row in rows:
            values = [row.get("label", "")]
            for col in columns:
                values.append("" if row.get(col["key"]) is None else str(row.get(col["key"])))
            f.write(",".join(values) + "\n")

    best_map: Dict[str, Optional[float]] = {}
    second_map: Dict[str, Optional[float]] = {}
    for col in columns:
        vals = [row.get(col["key"]) for row in rows]
        best_val, second_val = best_and_second(vals, col.get("higher_is_better", True))
        best_map[col["key"]] = best_val
        second_map[col["key"]] = second_val

    with open(tex_path, "w", encoding="utf-8") as f:
        f.write("\\begin{tabular}{l" + "c" * len(columns) + "}\n")
        f.write("\\toprule\n")
        header_line = "Method"
        for col in columns:
            header_line += f" & {col['label']}"
        f.write(header_line + " \\\\\n")
        f.write("\\midrule\n")
        for row in rows:
            line_parts = [row.get("label", "")]
            for col in columns:
                val = row.get(col["key"])
                formatted = format_value(val, digits)
                best_val = best_map[col["key"]]
                second_val = second_map[col["key"]]
                if isinstance(val, (int, float)) and best_val is not None:
                    if abs(val - best_val) < 1e-12:
                        formatted = f"\\textbf{{{formatted}}}"
                    elif second_val is not None and abs(val - second_val) < 1e-12:
                        formatted = f"\\underline{{{formatted}}}"
                line_parts.append(formatted)
            f.write(" & ".join(line_parts) + " \\\\\n")
        f.write("\\bottomrule\n")
        f.write("\\end{tabular}\n")
    has_metrics = False
    for row in rows:
        if any(row.get(col["key"]) is not None for col in columns):
            has_metrics = True
            break
    logger.info("table_written csv=%s tex=%s rows=%d", csv_path, tex_path, len(rows))
    return {"csv": csv_path, "tex": tex_path, "rows": len(rows), "has_metrics": has_metrics}


def _save_fig(fig, pdf_path: str, png_path: Optional[str], png_dpi: int) -> None:
    fig.savefig(pdf_path)
    if png_path:
        fig.savefig(png_path, dpi=png_dpi)


def latex_path(path: str) -> str:
    return path.replace("\\", "/")


def plot_recall_mrr_curves(
    experiments: List[Dict[str, Any]],
    data_root: str,
    metrics_filename: str,
    k_values: List[int],
    role_map: Dict[str, Any],
    palette: Dict[str, Any],
    theme: str,
    output_path: str,
    png_path: Optional[str],
    png_dpi: int,
    fig_size: List[float],
    logger,
) -> bool:
    fig, axes = plt.subplots(1, 2, figsize=fig_size)
    has_data = False
    for exp in experiments:
        run_id = exp.get("run_id")
        label = exp.get("label", run_id)
        role = resolve_role(label, exp.get("role"), role_map)
        style = role_style(role, role_map, palette, theme)
        metrics_path = os.path.join(data_root, str(run_id), metrics_filename)
        if not os.path.exists(metrics_path):
            continue
        metrics = load_json(metrics_path)
        k_list = choose_k_values(metrics, "recall", k_values)
        recall_vals = parse_metric_k(metrics, "recall")
        mrr_vals = parse_metric_k(metrics, "mrr")
        if not recall_vals and not mrr_vals:
            continue
        has_data = True
        axes[0].plot(
            k_list,
            [recall_vals.get(k) for k in k_list],
            label=label,
            color=style["color"],
            linestyle=style["linestyle"],
            marker=style["marker"],
            markevery=1,
        )
        axes[1].plot(
            k_list,
            [mrr_vals.get(k) for k in k_list],
            label=label,
            color=style["color"],
            linestyle=style["linestyle"],
            marker=style["marker"],
            markevery=1,
        )

    for ax, title in zip(axes, ["Recall@k", "MRR@k"]):
        ax.set_xlabel("k")
        ax.set_ylabel(title)
        ax.grid(True, axis="y")
    if has_data:
        axes[0].legend(loc="lower right", ncol=1)
    else:
        for ax in axes:
            ax.text(
                0.5,
                0.5,
                "TODO: missing metrics.json",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
    fig.tight_layout()
    _save_fig(fig, output_path, png_path, png_dpi)
    plt.close(fig)
    logger.info("figure_written path=%s has_data=%s", output_path, has_data)
    return has_data


def plot_delta_bar(
    experiments: List[Dict[str, Any]],
    data_root: str,
    delta_filenames: List[str],
    metrics: List[str],
    role_map: Dict[str, Any],
    palette: Dict[str, Any],
    theme: str,
    output_path: str,
    png_path: Optional[str],
    png_dpi: int,
    fig_size: List[float],
    logger,
) -> bool:
    data_rows = []
    for exp in experiments:
        run_id = exp.get("run_id")
        label = exp.get("label", run_id)
        role = resolve_role(label, exp.get("role"), role_map)
        run_dir = os.path.join(data_root, str(run_id))
        delta_path = find_existing_file(run_dir, delta_filenames)
        if not delta_path:
            continue
        payload = load_json(delta_path)
        delta = payload.get("delta", {})
        row = {"label": label, "role": role}
        for key in metrics:
            val = delta.get(key)
            row[key] = val if isinstance(val, (int, float)) else None
        data_rows.append(row)

    fig, ax = plt.subplots(figsize=fig_size)
    has_data = bool(data_rows)
    if has_data:
        x = list(range(len(metrics)))
        bar_width = 0.8 / max(len(data_rows), 1)
        for idx, row in enumerate(data_rows):
            style = role_style(row["role"], role_map, palette, theme)
            offsets = [v + idx * bar_width for v in x]
            ax.bar(
                offsets,
                [row.get(m) or 0.0 for m in metrics],
                width=bar_width,
                label=row["label"],
                color=style["color"],
                hatch=style.get("hatch"),
                edgecolor="black",
                linewidth=0.4,
            )
        ax.set_xticks([v + bar_width * (len(data_rows) - 1) / 2 for v in x])
        ax.set_xticklabels(metrics, rotation=0)
        ax.axhline(0, color="#666666", linewidth=0.8)
        ax.legend(loc="best", ncol=1)
        ax.set_ylabel("Δ vs baseline")
        ax.grid(True, axis="y")
    else:
        ax.text(
            0.5,
            0.5,
            "TODO: missing delta_vs_baseline.json",
            ha="center",
            va="center",
            transform=ax.transAxes,
        )
    fig.tight_layout()
    _save_fig(fig, output_path, png_path, png_dpi)
    plt.close(fig)
    logger.info("figure_written path=%s has_data=%s", output_path, has_data)
    return has_data


def plot_ablation_breakdown(
    experiments: List[Dict[str, Any]],
    data_root: str,
    summary_filename: str,
    metrics: List[str],
    role_map: Dict[str, Any],
    palette: Dict[str, Any],
    theme: str,
    output_path: str,
    png_path: Optional[str],
    png_dpi: int,
    fig_size: List[float],
    logger,
) -> bool:
    rows = []
    for exp in experiments:
        run_id = exp.get("run_id")
        label = exp.get("label", run_id)
        role = resolve_role(label, exp.get("role"), role_map)
        summary_path = os.path.join(data_root, str(run_id), summary_filename)
        if not os.path.exists(summary_path):
            continue
        summary = load_json(summary_path)
        metrics_row = extract_summary_metrics(summary)
        rows.append({"label": label, "role": role, **metrics_row})

    fig, ax = plt.subplots(figsize=fig_size)
    has_data = bool(rows)
    if has_data:
        x = list(range(len(metrics)))
        bar_width = 0.8 / max(len(rows), 1)
        for idx, row in enumerate(rows):
            style = role_style(row["role"], role_map, palette, theme)
            offsets = [v + idx * bar_width for v in x]
            ax.bar(
                offsets,
                [row.get(m) or 0.0 for m in metrics],
                width=bar_width,
                label=row["label"],
                color=style["color"],
                hatch=style.get("hatch"),
                edgecolor="black",
                linewidth=0.4,
            )
        ax.set_xticks([v + bar_width * (len(rows) - 1) / 2 for v in x])
        ax.set_xticklabels(metrics, rotation=0)
        ax.set_ylabel("Score")
        ax.grid(True, axis="y")
        ax.legend(loc="best", ncol=1)
    else:
        ax.text(
            0.5,
            0.5,
            "TODO: missing summary.json",
            ha="center",
            va="center",
            transform=ax.transAxes,
        )
    fig.tight_layout()
    _save_fig(fig, output_path, png_path, png_dpi)
    plt.close(fig)
    logger.info("figure_written path=%s has_data=%s", output_path, has_data)
    return has_data


def plot_numeric_error_distribution(
    run_id: Optional[str],
    data_root: str,
    per_query_filename: str,
    output_path: str,
    png_path: Optional[str],
    png_dpi: int,
    fig_size: List[float],
    logger,
) -> bool:
    fig, ax = plt.subplots(figsize=fig_size)
    has_data = False
    rel_errors: List[float] = []
    if run_id:
        per_query_path = os.path.join(data_root, str(run_id), per_query_filename)
        rows = load_jsonl(per_query_path)
        rel_errors = [row.get("rel_err") for row in rows if row.get("rel_err") is not None]
        has_data = bool(rel_errors)
    if has_data:
        ax.hist(rel_errors, bins=30, color="#4d4d4d", edgecolor="white")
        ax.set_xlabel("Relative Error")
        ax.set_ylabel("Count")
        ax.grid(True, axis="y")
    else:
        ax.text(
            0.5,
            0.5,
            "TODO: missing numeric_per_query.jsonl",
            ha="center",
            va="center",
            transform=ax.transAxes,
        )
    fig.tight_layout()
    _save_fig(fig, output_path, png_path, png_dpi)
    plt.close(fig)
    logger.info("figure_written path=%s has_data=%s", output_path, has_data)
    return has_data


def plot_multistep_trace_case(
    run_id: Optional[str],
    qid: Optional[str],
    data_root: str,
    trace_filename: str,
    output_path: str,
    png_path: Optional[str],
    png_dpi: int,
    fig_size: List[float],
    logger,
) -> bool:
    fig, ax = plt.subplots(figsize=fig_size)
    has_data = False
    steps: List[int] = []
    new_counts: List[int] = []
    topk_counts: List[int] = []
    selected = None
    if run_id:
        trace_path = os.path.join(data_root, str(run_id), trace_filename)
        rows = load_jsonl(trace_path)
        if rows:
            if qid:
                for row in rows:
                    if row.get("qid") == qid:
                        selected = row
                        break
            if selected is None:
                selected = rows[0]
            trace = selected.get("trace", [])
            steps = list(range(1, len(trace) + 1))
            new_counts = [len(t.get("newly_added_chunk_ids", [])) for t in trace]
            topk_counts = [len(t.get("topk_chunks", [])) for t in trace]
            has_data = bool(steps)
    if has_data:
        ax.plot(steps, new_counts, marker="o", label="New chunks")
        ax.plot(steps, topk_counts, marker="s", label="Top-k size")
        ax.set_xlabel("Step")
        ax.set_ylabel("Count")
        ax.grid(True, axis="y")
        ax.legend(loc="best")
        if selected is not None:
            ax.set_title(f"Trace qid={selected.get('qid')}")
    else:
        ax.text(
            0.5,
            0.5,
            "TODO: missing multistep_traces.jsonl",
            ha="center",
            va="center",
            transform=ax.transAxes,
        )
    fig.tight_layout()
    _save_fig(fig, output_path, png_path, png_dpi)
    plt.close(fig)
    logger.info("figure_written path=%s has_data=%s", output_path, has_data)
    return has_data


def write_figure_catalog(
    catalog_path: str,
    entries: List[Dict[str, Any]],
    logger,
) -> None:
    ensure_dir(os.path.dirname(catalog_path))
    with open(catalog_path, "w", encoding="utf-8") as f:
        f.write("# FIGURE_CATALOG\n\n")
        for entry in entries:
            f.write(f"## {entry['title']}\n")
            f.write(f"- 问题：{entry['question']}\n")
            f.write("- 数据源：\n")
            for src in entry.get("data_sources", []):
                f.write(f"  - {src}\n")
            f.write(f"- 生成脚本入口：`{entry['script']}`\n")
            f.write("- 输出文件：\n")
            for out in entry.get("outputs", []):
                f.write(f"  - {latex_path(out)}\n")
            f.write(f"- LaTeX 引用：\n\n```\n{entry['latex'].strip()}\n```\n\n")
            f.write(f"- 状态：{entry['status']}\n\n")
    logger.info("catalog_written path=%s entries=%d", catalog_path, len(entries))


def write_figures_auto_tex(
    tex_path: str,
    entries: List[Dict[str, Any]],
    default_theme: str,
    logger,
) -> None:
    ensure_dir(os.path.dirname(tex_path))
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write("% Auto-generated by scripts/plot_all.py\n")
        f.write(f"% Default theme: {default_theme}\n\n")
        for entry in entries:
            f.write(entry["latex"].strip() + "\n\n")
    logger.info("figures_auto_written path=%s", tex_path)


def main() -> int:
    args = parse_args()
    config = load_yaml(args.config)

    run_id = config.get("run_id") or generate_run_id()
    output_dir = config.get("output_dir", "outputs")
    run_dir = os.path.join(output_dir, run_id)
    ensure_dir(run_dir)

    log_path = os.path.join(run_dir, "logs.txt")
    logger = setup_logging(log_path)
    logger.info("command_line=%s", " ".join(sys.argv))
    logger.info("config_path=%s", args.config)

    seed = int(config.get("seed", 42))
    set_seed(seed)
    logger.info("seed=%d", seed)

    git_hash = get_git_hash()
    logger.info("git_hash=%s", git_hash)
    with open(os.path.join(run_dir, "git_commit.txt"), "w", encoding="utf-8") as f:
        f.write(f"{git_hash}\n")
    with open(os.path.join(run_dir, "seed.txt"), "w", encoding="utf-8") as f:
        f.write(f"{seed}\n")
    save_yaml(config, os.path.join(run_dir, "config.yaml"))

    style_dir = style_dir_from_config(config)
    palette = load_yaml(config.get("palettes_path", "")) or {}
    role_map = get_role_map(config.get("role_map_path", ""))

    experiments_path = config.get("experiments_path")
    experiments = read_experiments(experiments_path, config.get("experiments"))
    logger.info("experiments_loaded=%d", len(experiments))

    default_theme = args.theme or config.get("default_theme", "ThemeA")
    render_all = bool(args.all_themes or config.get("render_all_themes", False))
    themes = list(palette.get("themes", {}).keys()) if render_all else [default_theme]

    output_root = output_root_from_config(config)
    data_root = data_root_from_config(config)

    entries: List[Dict[str, Any]] = []
    today = datetime.now().strftime("%Y-%m-%d")

    for theme in themes:
        theme_dir = os.path.join(output_root, theme)
        fig_dir = os.path.join(theme_dir, "figures")
        table_dir = os.path.join(theme_dir, "tables")
        ensure_dir(fig_dir)
        ensure_dir(table_dir)
        apply_style(style_dir, theme, palette, logger)
        record_entries = theme == default_theme

        figure_cfg = config.get("figures", {})

        # 1) Main results table
        main_cfg = figure_cfg.get("main_results", {})
        if main_cfg.get("enabled", True):
            rows = collect_table_rows(
                experiments,
                data_root,
                main_cfg.get("summary_filename", "summary.json"),
            )
            columns = main_cfg.get("columns", [])
            csv_path = os.path.join(table_dir, "main_results.csv")
            tex_path = os.path.join(table_dir, "main_results.tex")
            result = write_main_results_table(
                rows,
                columns,
                int(main_cfg.get("table_digits", 4)),
                csv_path,
                tex_path,
                logger,
            )
            status = "ok" if result["has_metrics"] else "TODO: missing summary.json"
            if record_entries:
                tex_input = latex_path(tex_path)
                entries.append(
                    {
                        "title": "主结果总表",
                        "question": "不同方法在 Full/Complex 检索指标上的整体对比表现。",
                        "data_sources": [
                            f"{experiments_path} (run_id 列表)",
                            f"{data_root}/<run_id>/"
                            f"{main_cfg.get('summary_filename', 'summary.json')}",
                        ],
                        "script": "scripts/plot_all.py (main_results)",
                        "outputs": [csv_path, tex_path],
                        "latex": (
                            "\\begin{table}[t]\n"
                            "\\centering\n"
                            f"\\caption{{TODO: 主结果对比（生成日期 {today}）}}\n"
                            "\\label{tab:main_results}\n"
                            f"\\input{{{tex_input}}}\n"
                            "\\end{table}"
                        ),
                        "status": status,
                    }
                )

        # 2) Recall/MRR curves
        curve_cfg = figure_cfg.get("recall_mrr_curves", {})
        if curve_cfg.get("enabled", True):
            use_groups = set(curve_cfg.get("use_groups", []) or [])
            curve_exps = (
                [e for e in experiments if e.get("group") in use_groups]
                if use_groups
                else experiments
            )
            output_path = os.path.join(
                fig_dir, f"{curve_cfg.get('output_name', 'recall_mrr_k')}.pdf"
            )
            png_path = (
                output_path.replace(".pdf", ".png") if config.get("export_png", True) else None
            )
            has_data = plot_recall_mrr_curves(
                curve_exps,
                data_root,
                curve_cfg.get("metrics_filename", "metrics.json"),
                curve_cfg.get("k_values", [1, 5, 10]),
                role_map,
                palette,
                theme,
                output_path,
                png_path,
                int(config.get("png_dpi", 600)),
                config.get("figure_sizes", {}).get("wide", [6.2, 3.4]),
                logger,
            )
            status = "ok" if has_data else "TODO: missing metrics.json"
            if record_entries:
                fig_path = latex_path(output_path)
                entries.append(
                    {
                        "title": "Recall@k / MRR@k 曲线",
                        "question": "不同方法随 k 变化的检索召回与排序质量。",
                        "data_sources": [
                            f"{data_root}/<run_id>/"
                            f"{curve_cfg.get('metrics_filename', 'metrics.json')}"
                        ],
                        "script": "scripts/plot_all.py (recall_mrr_curves)",
                        "outputs": [
                            output_path,
                            png_path or output_path.replace(".pdf", ".png"),
                        ],
                        "latex": (
                            "\\begin{figure}[t]\n"
                            "\\centering\n"
                            f"\\includegraphics[width=0.95\\linewidth]{{{fig_path}}}\n"
                            "\\caption{TODO: Recall@k 与 MRR@k 随 k 变化曲线}\n"
                            "\\label{fig:recall_mrr_k}\n"
                            "\\end{figure}"
                        ),
                        "status": status,
                    }
                )

        # 3) Delta bar
        delta_cfg = figure_cfg.get("delta_bar", {})
        if delta_cfg.get("enabled", True):
            output_path = os.path.join(fig_dir, f"{delta_cfg.get('output_name', 'delta_bar')}.pdf")
            png_path = (
                output_path.replace(".pdf", ".png") if config.get("export_png", True) else None
            )
            has_data = plot_delta_bar(
                experiments,
                data_root,
                delta_cfg.get("delta_filenames", ["delta_vs_baseline.json"]),
                delta_cfg.get("metrics", ["recall@10", "mrr@10"]),
                role_map,
                palette,
                theme,
                output_path,
                png_path,
                int(config.get("png_dpi", 600)),
                config.get("figure_sizes", {}).get("medium", [4.8, 3.2]),
                logger,
            )
            status = "ok" if has_data else "TODO: missing delta_vs_baseline.json"
            if record_entries:
                fig_path = latex_path(output_path)
                entries.append(
                    {
                        "title": "相对 Baseline 的 Δ 指标",
                        "question": "方法相对 baseline 的提升幅度（Δ 形式）。",
                        "data_sources": [
                            f"{data_root}/<run_id>/"
                            "(delta_vs_baseline.json | delta_vs_pre.json)"
                        ],
                        "script": "scripts/plot_all.py (delta_bar)",
                        "outputs": [
                            output_path,
                            png_path or output_path.replace(".pdf", ".png"),
                        ],
                        "latex": (
                            "\\begin{figure}[t]\n"
                            "\\centering\n"
                            f"\\includegraphics[width=0.85\\linewidth]{{{fig_path}}}\n"
                            "\\caption{TODO: 相对 baseline 的指标提升}\n"
                            "\\label{fig:delta_bar}\n"
                            "\\end{figure}"
                        ),
                        "status": status,
                    }
                )

        # 4) Ablation breakdown
        ablation_cfg = figure_cfg.get("ablation_breakdown", {})
        if ablation_cfg.get("enabled", True):
            group = ablation_cfg.get("group")
            ablation_exps = (
                [e for e in experiments if e.get("group") == group]
                if group
                else experiments
            )
            output_path = os.path.join(
                fig_dir, f"{ablation_cfg.get('output_name', 'ablation_breakdown')}.pdf"
            )
            png_path = (
                output_path.replace(".pdf", ".png") if config.get("export_png", True) else None
            )
            has_data = plot_ablation_breakdown(
                ablation_exps,
                data_root,
                main_cfg.get("summary_filename", "summary.json"),
                ablation_cfg.get("metrics", []),
                role_map,
                palette,
                theme,
                output_path,
                png_path,
                int(config.get("png_dpi", 600)),
                config.get("figure_sizes", {}).get("medium", [4.8, 3.2]),
                logger,
            )
            status = "ok" if has_data else "TODO: missing summary.json"
            if record_entries:
                fig_path = latex_path(output_path)
                entries.append(
                    {
                        "title": "消融拆解图",
                        "question": "从 baseline → multistep → +calculator 的分步贡献。",
                        "data_sources": [
                            f"{data_root}/<run_id>/"
                            f"{main_cfg.get('summary_filename', 'summary.json')}"
                        ],
                        "script": "scripts/plot_all.py (ablation_breakdown)",
                        "outputs": [
                            output_path,
                            png_path or output_path.replace(".pdf", ".png"),
                        ],
                        "latex": (
                            "\\begin{figure}[t]\n"
                            "\\centering\n"
                            f"\\includegraphics[width=0.85\\linewidth]{{{fig_path}}}\n"
                            "\\caption{TODO: 消融拆解对比}\n"
                            "\\label{fig:ablation_breakdown}\n"
                            "\\end{figure}"
                        ),
                        "status": status,
                    }
                )

        # 5) Abbrev subset breakdown (optional)
        abbrev_cfg = figure_cfg.get("abbrev_breakdown", {})
        if abbrev_cfg.get("enabled", False):
            group = abbrev_cfg.get("group")
            abbrev_exps = (
                [e for e in experiments if e.get("group") == group]
                if group
                else experiments
            )
            output_path = os.path.join(
                fig_dir, f"{abbrev_cfg.get('output_name', 'abbrev_breakdown')}.pdf"
            )
            png_path = (
                output_path.replace(".pdf", ".png") if config.get("export_png", True) else None
            )
            has_data = plot_ablation_breakdown(
                abbrev_exps,
                data_root,
                main_cfg.get("summary_filename", "summary.json"),
                abbrev_cfg.get("metrics", ["abbrev_r10", "abbrev_mrr10"]),
                role_map,
                palette,
                theme,
                output_path,
                png_path,
                int(config.get("png_dpi", 600)),
                config.get("figure_sizes", {}).get("medium", [4.8, 3.2]),
                logger,
            )
            status = "ok" if has_data else "TODO: missing summary.json"
            if record_entries:
                fig_path = latex_path(output_path)
                entries.append(
                    {
                        "title": "Abbrev subset breakdown",
                        "question": "How do runs perform on abbreviation-heavy subset retrieval?",
                        "data_sources": [
                            f"{data_root}/<run_id>/"
                            f"{main_cfg.get('summary_filename', 'summary.json')}"
                        ],
                        "script": "scripts/plot_all.py (abbrev_breakdown)",
                        "outputs": [
                            output_path,
                            png_path or output_path.replace(".pdf", ".png"),
                        ],
                        "latex": (
                            "\\begin{figure}[t]\n"
                            "\\centering\n"
                            f"\\includegraphics[width=0.85\\linewidth]{{{fig_path}}}\n"
                            "\\caption{TODO: Abbrev subset retrieval comparison}\n"
                            "\\label{fig:abbrev_breakdown}\n"
                            "\\end{figure}"
                        ),
                        "status": status,
                    }
                )

        # 6) Numeric error distribution (optional)
        num_cfg = figure_cfg.get("numeric_errors", {})
        if num_cfg.get("enabled", False):
            output_path = os.path.join(
                fig_dir, f"{num_cfg.get('output_name', 'numeric_error_dist')}.pdf"
            )
            png_path = (
                output_path.replace(".pdf", ".png") if config.get("export_png", True) else None
            )
            has_data = plot_numeric_error_distribution(
                num_cfg.get("run_id"),
                data_root,
                num_cfg.get("per_query_filename", "numeric_per_query.jsonl"),
                output_path,
                png_path,
                int(config.get("png_dpi", 600)),
                config.get("figure_sizes", {}).get("medium", [4.8, 3.2]),
                logger,
            )
            status = "ok" if has_data else "TODO: missing numeric_per_query.jsonl"
            if record_entries:
                fig_path = latex_path(output_path)
                entries.append(
                    {
                        "title": "数值 QA 误差分布",
                        "question": "数值计算模块的误差分布与稳定性。",
                        "data_sources": [
                            f"{data_root}/<run_id>/"
                            f"{num_cfg.get('per_query_filename', 'numeric_per_query.jsonl')}"
                        ],
                        "script": "scripts/plot_all.py (numeric_errors)",
                        "outputs": [
                            output_path,
                            png_path or output_path.replace(".pdf", ".png"),
                        ],
                        "latex": (
                            "\\begin{figure}[t]\n"
                            "\\centering\n"
                            f"\\includegraphics[width=0.85\\linewidth]{{{fig_path}}}\n"
                            "\\caption{TODO: 数值 QA 误差分布}\n"
                            "\\label{fig:numeric_error_dist}\n"
                            "\\end{figure}"
                        ),
                        "status": status,
                    }
                )

        # 7) Multistep trace case (optional)
        trace_cfg = figure_cfg.get("multistep_trace", {})
        if trace_cfg.get("enabled", False):
            output_path = os.path.join(
                fig_dir, f"{trace_cfg.get('output_name', 'multistep_trace_case')}.pdf"
            )
            png_path = (
                output_path.replace(".pdf", ".png") if config.get("export_png", True) else None
            )
            has_data = plot_multistep_trace_case(
                trace_cfg.get("run_id"),
                trace_cfg.get("qid"),
                data_root,
                trace_cfg.get("trace_filename", "multistep_traces.jsonl"),
                output_path,
                png_path,
                int(config.get("png_dpi", 600)),
                config.get("figure_sizes", {}).get("wide", [6.2, 3.4]),
                logger,
            )
            status = "ok" if has_data else "TODO: missing multistep_traces.jsonl"
            if record_entries:
                fig_path = latex_path(output_path)
                entries.append(
                    {
                        "title": "多步检索轨迹案例",
                        "question": "展示多步检索在单样本上的步骤与收集证据变化。",
                        "data_sources": [
                            f"{data_root}/<run_id>/"
                            f"{trace_cfg.get('trace_filename', 'multistep_traces.jsonl')}"
                        ],
                        "script": "scripts/plot_all.py (multistep_trace)",
                        "outputs": [
                            output_path,
                            png_path or output_path.replace(".pdf", ".png"),
                        ],
                        "latex": (
                            "\\begin{figure}[t]\n"
                            "\\centering\n"
                            f"\\includegraphics[width=0.95\\linewidth]{{{fig_path}}}\n"
                            "\\caption{TODO: 多步检索轨迹案例}\n"
                            "\\label{fig:multistep_trace_case}\n"
                            "\\end{figure}"
                        ),
                        "status": status,
                    }
                )

    catalog_path = os.path.join(output_root, "FIGURE_CATALOG.md")
    write_figure_catalog(catalog_path, entries, logger)
    figures_tex_path = os.path.join(output_root, "figures_auto.tex")
    write_figures_auto_tex(figures_tex_path, entries, default_theme, logger)

    metrics_out = {
        "generated_entries": len(entries),
        "themes": themes,
        "output_root": output_root,
    }
    with open(os.path.join(run_dir, "metrics.json"), "w", encoding="utf-8") as f:
        import json

        json.dump(metrics_out, f, indent=2)

    logger.info("done entries=%d output_root=%s", len(entries), output_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
