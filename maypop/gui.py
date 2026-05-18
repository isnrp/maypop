# gui.py  —  run from your project root:  python gui.py
#
# Folder layout expected:
#   maypop/
#     db.py, embeddings.py, push.py, search.py, pull.py, api.py  ← new
#   gui.py   ← this file

import pathlib, tempfile
from nicegui import ui, app as ngapp
from maypop.api import api_search, api_pull, api_push, api_list_all

# ── Serve each app's HTML through NiceGUI's static file router ───────────────
PREVIEW_DIR = pathlib.Path(tempfile.mkdtemp(prefix="maypop_previews_"))
ngapp.add_static_files("/previews", str(PREVIEW_DIR))


def _preview_url(app: dict) -> str:
    """Write the app's content to a temp file and return its URL."""
    html: str = app.get("content") or ""
    if not html.strip():
        return ""
    dest = PREVIEW_DIR / str(app["id"])
    dest.mkdir(exist_ok=True)
    (dest / "index.html").write_text(html, encoding="utf-8")
    return f"/previews/{app['id']}/index.html"


# ── Card ──────────────────────────────────────────────────────────────────────
def make_card(app: dict, container):
    url = _preview_url(app)

    with container:
        with ui.card().classes(
            "w-72 rounded-2xl overflow-hidden shadow "
            "hover:shadow-xl transition-all duration-200 cursor-pointer"
        ):
            # ── live iframe thumbnail ─────────────────────────────────────────
            if url:
                ui.html(f"""
                    <iframe
                        src="{url}"
                        style="width:100%;height:180px;border:none;
                               pointer-events:none;overflow:hidden;
                               background:#fff;"
                        sandbox="allow-scripts allow-same-origin"
                        scrolling="no">
                    </iframe>
                """)
            else:
                ui.label("no preview").classes(
                    "flex items-center justify-center h-44 w-full "
                    "text-gray-500 bg-gray-800 text-sm"
                )

            # ── meta ──────────────────────────────────────────────────────────
            with ui.card_section().classes("p-3 flex flex-col gap-1"):
                with ui.row().classes("items-center justify-between w-full"):
                    ui.label(app["name"]).classes("font-semibold text-base truncate")
                    ui.badge(f"#{app['id']}", color="gray").classes("text-xs font-mono")

                # tags
                if app.get("tags"):
                    with ui.row().classes("flex-wrap gap-1 mt-1"):
                        for tag in app["tags"]:
                            ui.badge(tag, color="teal").classes("text-xs")

                # uploader
                if app.get("uploader"):
                    ui.label(f"↑ {app['uploader']}").classes("text-xs text-gray-400 mt-1")

                # dates
                created  = str(app["created_at"])[:10]  if app.get("created_at")  else "—"
                uploaded = str(app["uploaded_at"])[:10] if app.get("uploaded_at") else "—"
                ui.label(f"created {created} · uploaded {uploaded}").classes("text-xs text-gray-500")

            # ── actions ───────────────────────────────────────────────────────
            with ui.row().classes("px-3 pb-3 gap-2"):
                if url:
                    ui.button("Open", icon="open_in_new",
                               on_click=lambda u=url: ui.navigate.to(u, new_tab=True)
                               ).props("flat dense size=sm")
                ui.button("Pull", icon="download",
                           on_click=lambda a=app: _pull_dialog(a)
                           ).props("flat dense size=sm color=primary")


# ── Pull dialog ───────────────────────────────────────────────────────────────
def _pull_dialog(app: dict):
    with ui.dialog() as d, ui.card().classes("p-5 gap-3 w-[480px]"):
        ui.label(f'App #{app["id"]} — {app["name"]}').classes("font-bold text-lg")

        dest = ui.input(
            "Save path", value=f'./{app["name"]}.html'
        ).classes("w-full font-mono text-sm")

        status = ui.label("").classes("text-sm")

        def do_save():
            p = pathlib.Path(dest.value)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(app["content"] or "", encoding="utf-8")
            status.set_text(f"✅ Saved to {p}")
            ui.notify(f"Pulled to {p}", type="positive")

        with ui.row():
            ui.button("Cancel", on_click=d.close).props("flat")
            ui.button("Save HTML", on_click=do_save).props("color=primary")
    d.open()


# ── Push dialog ───────────────────────────────────────────────────────────────
def _push_dialog(on_done):
    with ui.dialog() as d, ui.card().classes("p-5 gap-3 w-[560px]"):
        ui.label("Push New App").classes("font-bold text-lg")

        name_in     = ui.input("App name").classes("w-full")
        uploader_in = ui.input("Your name").classes("w-full")
        tags_in     = ui.input("Tags (comma-separated)").classes("w-full")

        ui.label("HTML content (paste your index.html)").classes("text-sm text-gray-400")
        content_in = ui.textarea().classes("w-full font-mono text-xs h-48").props(
            'outlined autogrow'
        )

        # — OR — load from a local file path
        ui.separator()
        ui.label("— or load from a local file —").classes("text-xs text-gray-500")
        with ui.row().classes("w-full items-center gap-2"):
            path_in = ui.input("File path  (e.g. ./myapp/index.html)").classes("flex-1 text-sm")

            def load_file():
                p = pathlib.Path(path_in.value)
                if p.exists():
                    content_in.set_value(p.read_text(encoding="utf-8"))
                    if not name_in.value:
                        name_in.set_value(p.parent.name or p.stem)
                    ui.notify("File loaded", type="positive")
                else:
                    ui.notify(f"File not found: {p}", type="negative")

            ui.button("Load", on_click=load_file).props("flat dense size=sm")

        status = ui.label("").classes("text-sm")

        def do_push():
            if not name_in.value.strip():
                status.set_text("❌ Name is required")
                return
            if not content_in.value.strip():
                status.set_text("❌ Content is required")
                return
            try:
                tags = [t.strip() for t in tags_in.value.split(",") if t.strip()]
                app_id = api_push(
                    name_in.value.strip(),
                    content_in.value,
                    tags=tags,
                    uploader=uploader_in.value.strip(),
                )
                status.set_text(f"✅ Pushed as #{app_id}")
                ui.notify(f'Pushed "{name_in.value}" as #{app_id}', type="positive")
                on_done()        # refresh the grid
            except Exception as e:
                status.set_text(f"❌ {e}")

        with ui.row():
            ui.button("Cancel", on_click=d.close).props("flat")
            ui.button("Push", on_click=do_push).props("color=teal")
    d.open()


# ── Main page ─────────────────────────────────────────────────────────────────
@ui.page("/")
def main_page():

    # ── header ────────────────────────────────────────────────────────────────
    with ui.header().classes(
        "items-center gap-4 px-6 py-3 bg-gray-950 text-white border-b border-gray-800"
    ):
        ui.label("🌿 maypop").classes("text-2xl font-bold tracking-tight")

        search_input = (
            ui.input(placeholder="Semantic search…")
            .classes("flex-1 max-w-md")
            .props("outlined dense dark clearable")
        )

        push_btn = ui.button("Push App", icon="upload").props("color=teal")

    # ── status bar ────────────────────────────────────────────────────────────
    with ui.row().classes("px-6 pt-4 items-center gap-3"):
        count_label = ui.label("").classes("text-sm text-gray-400")
        spinner    = ui.spinner(size="sm").classes("hidden")

    # ── card grid ─────────────────────────────────────────────────────────────
    grid_wrap = ui.element("div").classes("px-6 pb-6")

    def render_grid(apps: list[dict]):
        grid_wrap.clear()
        count_label.set_text(f"{len(apps)} app{'s' if len(apps) != 1 else ''}")
        if not apps:
            with grid_wrap:
                ui.label("Nothing here yet.").classes(
                    "text-gray-500 mt-20 text-center w-full text-lg"
                )
            return
        with grid_wrap:
            grid = ui.element("div").classes(
                "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5"
            )
            for app in apps:
                make_card(app, grid)

    def refresh(query: str = ""):
        spinner.classes(remove="hidden")
        try:
            if query.strip():
                apps = api_search(query)
            else:
                apps = api_list_all()
            render_grid(apps)
        except Exception as e:
            ui.notify(f"Error: {e}", type="negative")
        finally:
            spinner.classes("hidden")

    # ── wire up controls ──────────────────────────────────────────────────────
    search_input.on("keyup.enter", lambda: refresh(search_input.value))
    # clear button resets to full list
    search_input.on("clear", lambda: refresh(""))

    push_btn.on("click", lambda: _push_dialog(on_done=lambda: refresh(search_input.value)))

    # initial load
    refresh()


ui.run(
    title="maypop",
    dark=True,
    port=8080,
    favicon="🌿",
    tailwind=True,
)