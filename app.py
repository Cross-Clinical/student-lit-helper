"""Student Lit Helper — Europe PMC search for educational citing."""

from __future__ import annotations

import requests
import gradio as gr

from input_guard import DISCLAIMER, guard_input

EUROPE_PMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def search_literature(query: str, max_results: int = 5) -> str:
    blocked = guard_input(query)
    if blocked:
        return blocked
    q = (query or "").strip()
    if not q:
        return "Enter a research question or keywords (e.g. 'nurse burnout interventions')."
    try:
        r = requests.get(
            EUROPE_PMC,
            params={
                "query": q,
                "format": "json",
                "pageSize": max(1, min(int(max_results), 10)),
                "resultType": "core",
            },
            timeout=30,
            headers={"User-Agent": "CrossClinical-StudentLitHelper/0.1 (educational)"},
        )
        r.raise_for_status()
        data = r.json()
    except Exception as exc:  # noqa: BLE001
        return f"Literature search failed: {exc}"

    results = (data.get("resultList") or {}).get("result") or []
    if not results:
        return "No results. Try simpler keywords."

    blocks = [
        f"**{DISCLAIMER}**\n\n"
        f"Query: `{q}`\n\n"
        "Use these citations in school papers. This tool does **not** interpret patient cases."
    ]
    for i, item in enumerate(results, 1):
        title = item.get("title") or "(no title)"
        authors = item.get("authorString") or "Unknown authors"
        journal = item.get("journalTitle") or item.get("bookOrReportDetails") or ""
        year = item.get("pubYear") or ""
        pmid = item.get("pmid")
        pmcid = item.get("pmcid")
        doi = item.get("doi")
        abstract = (item.get("abstractText") or "").strip()
        if len(abstract) > 600:
            abstract = abstract[:600] + "…"
        links = []
        if pmid:
            links.append(f"[PubMed {pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")
        if pmcid:
            links.append(f"[{pmcid}](https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/)")
        if doi:
            links.append(f"[doi:{doi}](https://doi.org/{doi})")
        blocks.append(
            f"### {i}. {title}\n"
            f"{authors} — *{journal}* ({year})\n\n"
            f"{abstract or '_No abstract in API response._'}\n\n"
            f"**Cite/open:** {' · '.join(links) if links else '_No PMID/DOI_'}"
        )
    return "\n\n---\n\n".join(blocks)


with gr.Blocks(title="Student Lit Helper") as demo:
    gr.Markdown(
        f"# Student Lit Helper\n\n**{DISCLAIMER}**\n\n"
        "Powered by [Europe PMC](https://europepmc.org/) open APIs.\n\n"
        "[Cross Clinical OSS](https://github.com/Cross-Clinical/suite-index) · "
        "[ProMedNet](https://crossclinical.com) · "
        "[Try Pathway Explorer](https://github.com/Cross-Clinical/health-pathway-explorer)"
    )
    query = gr.Textbox(label="Keywords / question")
    n = gr.Slider(1, 10, value=5, step=1, label="Max results")
    out = gr.Markdown()
    gr.Button("Search literature").click(search_literature, [query, n], out)
    query.submit(search_literature, [query, n], out)

if __name__ == "__main__":
    demo.launch()
