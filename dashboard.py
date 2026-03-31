import os
import requests
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from supabase_client import get_supabase

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO  = os.getenv("GITHUB_REPO")

st.set_page_config(page_title="Autoposts Dashboard", layout="wide")
st.title("Autoposts Dashboard")

tab_prompts, tab_feeds, tab_articles, tab_actions = st.tabs([
    "Prompts", "RSS Feeds", "Artículos", "GitHub Actions"
])


# ─────────────────────────────────────────────
# TAB 1: PROMPTS
# ─────────────────────────────────────────────
with tab_prompts:
    st.header("Gestión de Prompts")

    sb = get_supabase()
    prompts = sb.table("prompts").select("*").order("name").execute().data

    if not prompts:
        st.warning("No hay prompts en la base de datos. Ejecuta schema.sql primero.")
    else:
        prompt_names = [p["name"] for p in prompts]
        selected = st.selectbox("Selecciona un prompt", prompt_names)
        prompt = next(p for p in prompts if p["name"] == selected)

        st.caption(f"Última actualización: {prompt['updated_at'][:19].replace('T', ' ')}")

        if prompt.get("system_prompt") is not None:
            new_system = st.text_area(
                "System Prompt",
                value=prompt["system_prompt"] or "",
                height=200,
                key=f"system_{selected}"
            )
        else:
            new_system = None

        new_user = st.text_area(
            "User Prompt  (usa `{content}` donde va el texto del artículo)",
            value=prompt["user_prompt"],
            height=300,
            key=f"user_{selected}"
        )

        if st.button("Guardar cambios", type="primary"):
            update = {"user_prompt": new_user}
            if new_system is not None:
                update["system_prompt"] = new_system
            sb.table("prompts").update(update).eq("name", selected).execute()
            st.success("Prompt guardado correctamente.")
            st.rerun()


# ─────────────────────────────────────────────
# TAB 2: RSS FEEDS
# ─────────────────────────────────────────────
with tab_feeds:
    st.header("Fuentes RSS")

    sb = get_supabase()
    feeds = sb.table("rss_feeds").select("*").order("name").execute().data

    for feed in feeds:
        col1, col2, col3 = st.columns([3, 1, 1])
        col1.write(f"**{feed['name']}**  \n{feed['url']}")
        active = col2.toggle("Activo", value=feed["active"], key=f"toggle_{feed['id']}")
        if active != feed["active"]:
            sb.table("rss_feeds").update({"active": active}).eq("id", feed["id"]).execute()
            st.rerun()
        if col3.button("Eliminar", key=f"del_{feed['id']}"):
            sb.table("rss_feeds").delete().eq("id", feed["id"]).execute()
            st.rerun()

    st.divider()
    st.subheader("Añadir fuente")
    col_name, col_url = st.columns([1, 2])
    new_name = col_name.text_input("Nombre")
    new_url  = col_url.text_input("URL del feed RSS")
    if st.button("Añadir"):
        if new_url:
            sb.table("rss_feeds").insert({"name": new_name, "url": new_url}).execute()
            st.success("Feed añadido.")
            st.rerun()
        else:
            st.error("La URL es obligatoria.")


# ─────────────────────────────────────────────
# TAB 3: ARTÍCULOS
# ─────────────────────────────────────────────
with tab_articles:
    st.header("Historial de Artículos")

    sb = get_supabase()

    col_filter, col_refresh = st.columns([2, 1])
    status_filter = col_filter.selectbox("Filtrar por estado", ["Todos", "pending", "published", "failed"])
    if col_refresh.button("Actualizar"):
        st.rerun()

    query = sb.table("articles").select("*").order("created_at", desc=True).limit(100)
    if status_filter != "Todos":
        query = query.eq("status", status_filter)
    articles = query.execute().data

    st.caption(f"{len(articles)} artículos")

    for a in articles:
        status_emoji = {"published": "✅", "pending": "⏳", "failed": "❌"}.get(a["status"], "❓")
        with st.expander(f"{status_emoji} {a['url'][:80]}..."):
            col1, col2, col3 = st.columns(3)
            col1.metric("Estado", a["status"])
            col2.metric("Creado", a["created_at"][:10])
            col3.metric("Publicado", a["published_at"][:10] if a.get("published_at") else "—")
            st.write(f"[Abrir artículo]({a['url']})")

            if a["status"] == "pending":
                if st.button("Marcar como publicado", key=f"pub_{a['id']}"):
                    sb.table("articles").update({
                        "status": "published",
                        "published_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    }).eq("id", a["id"]).execute()
                    st.rerun()


# ─────────────────────────────────────────────
# TAB 4: GITHUB ACTIONS
# ─────────────────────────────────────────────
with tab_actions:
    st.header("GitHub Actions")

    if not all([GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO]):
        st.warning("Configura `GITHUB_TOKEN`, `GITHUB_OWNER` y `GITHUB_REPO` en el `.env` para usar esta sección.")
    else:
        gh_headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
        }
        base_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"

        col_trigger, col_refresh = st.columns([2, 1])

        with col_trigger:
            if st.button("▶ Lanzar workflow manualmente", type="primary"):
                resp = requests.post(
                    f"{base_url}/actions/workflows/autoposts.yml/dispatches",
                    headers=gh_headers,
                    json={"ref": "main"},
                )
                if resp.status_code == 204:
                    st.success("Workflow lanzado. Aparecerá en la lista en unos segundos.")
                else:
                    st.error(f"Error {resp.status_code}: {resp.text}")

        with col_refresh:
            if st.button("Actualizar"):
                st.rerun()

        resp = requests.get(
            f"{base_url}/actions/runs",
            headers=gh_headers,
            params={"per_page": 15, "workflow_id": "autoposts.yml"},
        )

        if resp.status_code != 200:
            st.error(f"Error al obtener runs: {resp.status_code} - {resp.text}")
        else:
            runs = resp.json().get("workflow_runs", [])

            if not runs:
                st.info("No hay ejecuciones recientes.")

            for run in runs:
                conclusion = run.get("conclusion") or run.get("status", "unknown")
                emoji = {
                    "success": "✅", "failure": "❌", "cancelled": "⛔",
                    "in_progress": "🔄", "queued": "⏳"
                }.get(conclusion, "❓")

                started = run["created_at"][:16].replace("T", " ")
                with st.expander(f"{emoji} #{run['run_number']} — {started}  |  {conclusion}"):
                    col1, col2 = st.columns(2)
                    col1.write(f"**Trigger:** {run['event']}")
                    col1.write(f"**Branch:** {run['head_branch']}")
                    col2.write(f"**Duración:** {run.get('run_duration_ms', 0) // 1000}s")
                    col2.write(f"**Commit:** {run['head_sha'][:7]}")

                    st.write(f"[Ver en GitHub]({run['html_url']})")

                    if st.button("Ver logs", key=f"logs_{run['id']}"):
                        logs_resp = requests.get(
                            f"{base_url}/actions/runs/{run['id']}/jobs",
                            headers=gh_headers,
                        )
                        if logs_resp.status_code == 200:
                            jobs = logs_resp.json().get("jobs", [])
                            for job in jobs:
                                st.subheader(f"Job: {job['name']}")
                                for step in job.get("steps", []):
                                    step_emoji = "✅" if step["conclusion"] == "success" else "❌" if step["conclusion"] == "failure" else "⏭"
                                    st.write(f"{step_emoji} {step['name']}")
