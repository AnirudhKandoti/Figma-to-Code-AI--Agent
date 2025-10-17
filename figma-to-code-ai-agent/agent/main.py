from __future__ import annotations
import json
import os
from typing import Optional, Dict, Any, List
import typer

from .config import Settings
from .figma_api import FigmaAPI
from .schema import UISchema, Node, Bounds, Color, TextStyle
from .codegen import CodeGen
from .writers.react_writer import init_scaffold, write_llm_files
from .utils.logging import log

app = typer.Typer(add_completion=False)

def _figma_to_schema(figma_json: Dict[str, Any]) -> UISchema:
    doc = figma_json.get("document", {})
    file_name = figma_json.get("name", "Untitled")
    # A *very* small subset mapping for demo purposes
    def walk(node) -> Node:
        ntype = node.get("type", "GROUP")
        name = node.get("name", ntype)
        bounds = None
        absolute = node.get("absoluteBoundingBox")
        if absolute:
            bounds = Bounds(x=absolute.get("x",0), y=absolute.get("y",0),
                            width=absolute.get("width",0), height=absolute.get("height",0))
        fill = None
        fills = node.get("fills") or []
        if fills and fills[0].get("type") == "SOLID":
            c = fills[0].get("color", {})
            fill = Color(r=c.get("r",0), g=c.get("g",0), b=c.get("b",0), a=fills[0].get("opacity",1))
        text = node.get("characters")
        text_style = None
        if "style" in node and node["type"] == "TEXT":
            st = node["style"]
            text_style = TextStyle(
                font_family=st.get("fontFamily"),
                font_size=st.get("fontSize"),
                font_weight=int(st.get("fontWeight", 400)) if st.get("fontWeight") else None,
                line_height=st.get("lineHeightPx"),
                letter_spacing=st.get("letterSpacing"),
                text_align=st.get("textAlignHorizontal"),
            )
        children = [walk(c) for c in node.get("children", [])]
        return Node(
            id=node.get("id",""),
            name=name,
            type=ntype,
            bounds=bounds,
            fill=fill,
            text=text,
            text_style=text_style,
            children=children
        )
    # Top level frames
    frames: List[Node] = []
    for child in doc.get("children", []):
        if child.get("type") in ("FRAME","GROUP","COMPONENT","COMPONENT_SET","PAGE"):
            for sub in child.get("children", []):
                if sub.get("type") == "FRAME":
                    frames.append(walk(sub))
    return UISchema(file_name=file_name, root_frames=frames, tokens={"spacing":{"md":16,"lg":24}})

@app.command(help="Run end-to-end generation from Figma or sample schema.")
def run(
    file_id: Optional[str] = typer.Option(None, "--file-id", help="Figma file key"),
    out: str = typer.Option("generated-ui", "--out", help="Output directory"),
    framework: str = typer.Option("react", "--framework", help="Target framework (react)"),
    sample: bool = typer.Option(False, "--sample", help="Use bundled sample schema instead of Figma API"),
):
    os.makedirs(out, exist_ok=True)

    # Prepare scaffold
    init_scaffold(out)

    # Prepare schema
    if sample:
        with open(os.path.join(os.path.dirname(__file__), "..", "samples", "figma_sample.json"), "r", encoding="utf-8") as f:
            figma_json = json.load(f)
    else:
        settings = Settings.validate()
        if file_id is None:
            file_id = settings.figma_file_id or ""
        if not settings.figma_token or not file_id:
            raise RuntimeError("FIGMA_TOKEN and a file id are required (pass --file-id or set FIGMA_FILE_ID).")
        api = FigmaAPI(settings.figma_token, timeout=settings.http_timeout)
        figma_json = api.get_file(file_id)

    schema = _figma_to_schema(figma_json).model_dump()

    # Generate code via Gemini
    if sample and not os.getenv("GEMINI_API_KEY"):
        # Offline safe fallback (writes a tiny hand-crafted component)
        log("[yellow]No GEMINI_API_KEY found; writing a fallback sample component[/yellow]")
        files = [
            ("src/components/Hero.tsx", """export default function Hero() {
  return (
    <section className="bg-white rounded-2xl shadow p-10">
      <h1 className="text-3xl font-bold mb-2">Sample Landing</h1>
      <p className="opacity-70">Replace this with LLM generated components.</p>
      <button className="mt-4 px-4 py-2 bg-black text-white rounded">Get Started</button>
    </section>
  )
}
"""),
            ("src/App.tsx", """import Hero from "./components/Hero";
export default function App(){
  return (
    <main className="min-h-screen bg-gray-50 p-10">
      <div className="max-w-5xl mx-auto space-y-8">
        <Hero />
      </div>
    </main>
  );
}
"""),
        ]
    else:
        settings = Settings.validate()
        cg = CodeGen(settings.model_name, settings.gemini_api_key)
        llm_text = cg.generate(schema)
        files = cg.parse_fenced_files(llm_text)
        if not files:
            log("[red]LLM did not return fenced files; falling back to a default App[/red]")
            files = [("src/App.tsx", "export default function App(){return <div>LLM output empty</div>}")]

    # Write files
    write_llm_files(out, files)
    log(f"[green]Done. Open {out} and run npm install && npm run dev[/green]")

if __name__ == "__main__":
    app()
