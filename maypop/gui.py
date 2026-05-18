# gui.py  —  run from your project root:  python gui.py
#
# Folder layout expected:
#   maypop/
#     db.py, embeddings.py, push.py, search.py, pull.py, api.py  ← new
#   gui.py   ← this file

import sys, os, pathlib, tempfile
from nicegui import ui, app as ngapp
from maypop.api import api_search, api_pull, api_push, api_list_all, api_delete, api_update

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
            "w-full rounded-2xl overflow-hidden shadow flex flex-col "
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
            with ui.card_section().classes("p-4 flex flex-col gap-2"):
                with ui.row().classes("items-center justify-between w-full"):
                    ui.label(app["name"]).classes("font-semibold text-lg truncate")
                    ui.badge(f"#{app['id']}", color="gray").classes("text-sm font-mono")

                # tags
                if app.get("tags"):
                    with ui.row().classes("flex-wrap gap-1 mt-1"):
                        for tag in app["tags"]:
                            ui.badge(tag, color="teal").classes("text-sm")

                # uploader
                if app.get("uploader"):
                    ui.label(f"↑ {app['uploader']}").classes("text-sm text-gray-400")

                # dates
                uploaded = str(app["uploaded_at"])[:10] if app.get("uploaded_at") else "—"
                ui.label(f"uploaded {uploaded}").classes("text-sm text-gray-500")

                # expandable description
                desc_text = app.get("description") or ""
                if desc_text:
                    desc_label = ui.label(desc_text).classes(
                        "text-sm text-gray-400 mt-1 hidden"
                    )

                    def toggle_desc(dl=desc_label):
                        if "hidden" in dl._classes:
                            dl.classes(remove="hidden")
                        else:
                            dl.classes("hidden")

                    ui.button("Description", icon="expand_more", on_click=toggle_desc
                              ).props("flat dense size=sm").classes("mt-1 self-start")

            # ── actions ───────────────────────────────────────────────────────
            with ui.row().classes("px-4 pb-4 gap-2 mt-auto"):
                if url:
                    ui.button("Open", icon="open_in_new",
                               on_click=lambda u=url: ui.navigate.to(u, new_tab=True)
                               ).props("flat dense")
                ui.button("Pull", icon="download",
                           on_click=lambda a=app: _pull_dialog(a)
                           ).props("flat dense color=primary")
                ui.button("Edit", icon="edit",
                           on_click=lambda a=app: _edit_dialog(a)
                           ).props("flat dense color=secondary")
                ui.button("Delete", icon="delete",
                           on_click=lambda a=app: _delete_dialog(a)
                           ).props("flat dense color=negative")


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


# ── Edit dialog ───────────────────────────────────────────────────────────────
def _edit_dialog(app: dict):
    with ui.dialog() as d, ui.card().classes("p-5 gap-3 w-[560px] max-h-[90vh] overflow-y-auto"):
        ui.label(f'Edit #{app["id"]}').classes("font-bold text-lg")

        name_in  = ui.input("Name", value=app["name"]).classes("w-full")
        user_in  = ui.input("Uploader", value=app.get("uploader") or "").classes("w-full")
        tags_in  = ui.input(
            "Tags (comma-separated)",
            value=", ".join(app.get("tags") or [])
        ).classes("w-full")
        desc_in  = ui.textarea("Description", value=app.get("description") or "").classes("w-full").props("outlined rows=3")

        ui.separator()
        ui.label("HTML content (index.html)").classes("text-sm text-gray-400")
        content_in = ui.textarea(value=app.get("content") or "").classes("w-full font-mono text-xs").props("outlined rows=8")

        # load from file shortcut
        with ui.row().classes("w-full items-center gap-2"):
            path_in = ui.input("Or load from file path").classes("flex-1 text-sm")
            def load_file():
                p = pathlib.Path(path_in.value)
                if p.exists():
                    content_in.set_value(p.read_text(encoding="utf-8"))
                    ui.notify("File loaded", type="positive")
                else:
                    ui.notify(f"File not found: {p}", type="negative")
            ui.button("Load", on_click=load_file).props("flat dense size=sm")

        status = ui.label("").classes("text-sm")

        def do_save():
            tags = [t.strip() for t in tags_in.value.split(",") if t.strip()]
            try:
                api_update(
                    app["id"],
                    name=name_in.value.strip(),
                    description=desc_in.value.strip(),
                    tags=tags,
                    uploader=user_in.value.strip(),
                    content=content_in.value,
                )
                ui.notify("Saved!", type="positive")
                d.close()
                ui.navigate.reload()
            except Exception as e:
                status.set_text(f"❌ {e}")

        with ui.row():
            ui.button("Cancel", on_click=d.close).props("flat")
            ui.button("Save", icon="save", on_click=do_save).props("color=primary")
    d.open()


# ── Delete dialog ─────────────────────────────────────────────────────────────
def _delete_dialog(app: dict):
    with ui.dialog() as d, ui.card().classes("p-5 gap-3 w-80"):
        ui.label("Delete app?").classes("font-bold text-lg")
        ui.label(f'"{app["name"]}" (#{app["id"]}) will be permanently removed.').classes(
            "text-sm text-gray-400"
        )
        with ui.row():
            ui.button("Cancel", on_click=d.close).props("flat")
            def do_delete(a=app):
                api_delete(a["id"])
                ui.notify(f'Deleted "{a["name"]}"', type="positive")
                d.close()
                # reload the page to refresh the grid
                ui.navigate.reload()
            ui.button("Delete", icon="delete", on_click=do_delete).props("color=negative")
    d.open()
def _push_dialog(on_done):
    with ui.dialog() as d, ui.card().classes("p-5 gap-3 w-[560px] max-h-[90vh] overflow-y-auto"):
        ui.label("Push New App").classes("font-bold text-lg")

        name_in     = ui.input("App name").classes("w-full")
        uploader_in = ui.input("Creator").classes("w-full")
        tags_in     = ui.input("Tags (comma-separated)").classes("w-full")
        desc_in     = ui.textarea("Description").classes("w-full").props("outlined rows=3")

        ui.label("HTML content (paste your index.html)").classes("text-sm text-gray-400")
        content_in = ui.textarea().classes("w-full font-mono text-xs").props(
            'outlined rows=8'
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
            if not (name_in.value or "").strip():
                status.set_text("❌ Name is required")
                return
            if not (uploader_in.value or "").strip():
                status.set_text("❌ Creator is required")
                return
            if not (content_in.value or "").strip():
                status.set_text("❌ Content is required")
                return
            try:
                tags = [t.strip() for t in (tags_in.value or "").split(",") if t.strip()]
                app_id = api_push(
                    (name_in.value or "").strip(),
                    content_in.value or "",
                    description=(desc_in.value or "").strip(),
                    tags=tags,
                    uploader=(uploader_in.value or "").strip(),
                )
                status.set_text(f"✅ Pushed as #{app_id}")
                ui.notify(f'Pushed "{name_in.value}" as #{app_id}', type="positive")
                d.close()
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
    ui.query("body").classes("w-full")
    ui.query(".nicegui-content").classes("w-full p-0")

    # ── header ────────────────────────────────────────────────────────────────
    with ui.header().classes(
        "items-center gap-4 px-6 py-3 bg-gray-950 text-white border-b border-gray-800"
    ):
        ui.label("🌿 maypop").classes("text-2xl font-bold tracking-tight")

        search_input = (
            ui.input(placeholder="Search…")
            .classes("flex-1 max-w-md")
            .props("outlined dense dark clearable")
        )

        push_btn = ui.button("Push App", icon="upload").props("color=teal")

    # ── status bar ────────────────────────────────────────────────────────────
    with ui.row().classes("px-6 pt-4 items-center gap-3"):
        count_label = ui.label("").classes("text-sm text-gray-400")
        spinner    = ui.spinner(size="sm").classes("hidden")

    # ── card grid ─────────────────────────────────────────────────────────────
    grid_wrap = ui.element("div").classes("px-6 pb-6 w-full")

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
                "grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-5 w-full"
            )
            for app in apps:
                make_card(app, grid)

    def refresh(query: str = ""):
        spinner.classes(remove="hidden")
        try:
            if query.strip():
                apps = api_search(query)
                n = len(apps)
                count_label.set_text(
                    f'{n} result{"s" if n != 1 else ""} for "{query.strip()}"'
                )
            else:
                apps = api_list_all()
                count_label.set_text(f"{len(apps)} app{'s' if len(apps) != 1 else ''}")
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
    port=int(os.environ.get("PORT", 8080)),
    favicon="🌿",
    tailwind=True,
    host="0.0.0.0",
    show=False,
)