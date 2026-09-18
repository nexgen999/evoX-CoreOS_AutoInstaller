#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evoX CoreOS & WebUI Manager
Application graphique moderne Tkinter pour la gestion multi-dépôts,
flux OPML (/feed/ apps, payloads, ffpfsc, pkg), configuration WebUI (/web/data/config.json),
synchronisation GitHub et système de versioning robuste.

Auteur: evoX Scene Community
"""

import os
import sys
import json
import shutil
import zipfile
import datetime
import threading
import urllib.request
import urllib.error
import re
import webbrowser
import subprocess
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Import Tkinter modules
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog, scrolledtext
except ImportError:
    print("Erreur: Le module Tkinter est requis pour exécuter cette application.")
    print("Sur Ubuntu/Debian: sudo apt-get install python3-tk")
    print("Sur Fedora: sudo dnf install python3-tkinter")
    print("Sur Windows/macOS: Tkinter est inclus par défaut avec l'installateur Python standard.")
    sys.exit(1)


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Default paths & configurations (démarrage à blanc obligatoire)
DEFAULT_CONFIG = {
    "githubUser": "",
    "coreosRepo": "",
    "webuiRepo": "",
    "workspaceDir": os.path.join(SCRIPT_DIR, "workspace"),
    "backupsDir": os.path.join(SCRIPT_DIR, "workspace", "backup"),
    "logsDir": os.path.join(SCRIPT_DIR, "workspace", "log"),
    "exportsDir": os.path.join(SCRIPT_DIR, "workspace", "exports"),
    "githubToken": "",
    "autoBackup": True,
    "theme": "dark",
    "hasSynchronized": False
}

CONFIG_FILE = os.path.join(SCRIPT_DIR, "evox_local_config.json")



# ==========================================
# MODULE ÉDITEUR CONFIGURATION WEBUI (INTÉGRÉ & STANDALONE)
# ==========================================
def build_config_general_tab(app, parent):
    """Onglet Général & GitHub : Paramètres du site, thèmes et dépôts."""
    inner = tk.Frame(parent, bg=app.colors["bg_card"], padx=20, pady=20)
    inner.pack(fill=tk.BOTH, expand=True)

    tk.Label(inner, text="🌐 Paramètres Généraux du Site WebUI",
             font=("Segoe UI", 12, "bold"), fg=app.colors["accent"], bg=app.colors["bg_card"]).pack(anchor="w", pady=(0, 4))
    tk.Label(inner, text="Modifiez le titre, la description, les dépôts GitHub associés et le thème de base.",
             font=("Segoe UI", 9), fg=app.colors["text_muted"], bg=app.colors["bg_card"]).pack(anchor="w", pady=(0, 15))

    form = tk.Frame(inner, bg=app.colors["bg_card"])
    form.pack(fill=tk.X)

    # Titre du site
    tk.Label(form, text="Titre du Site Web :", font=("Segoe UI", 9, "bold"),
             fg=app.colors["text_main"], bg=app.colors["bg_card"]).pack(anchor="w", pady=(4, 2))
    app.entry_site_title = tk.Entry(form, font=("Segoe UI", 10), bg=app.colors["bg_input"],
                                    fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat")
    app.entry_site_title.insert(0, app.webui_config.get("siteTitle", "evoX-CoreOS WebUI"))
    app.entry_site_title.pack(fill=tk.X, pady=(0, 10))

    # Description du site
    tk.Label(form, text="Description du Site :", font=("Segoe UI", 9, "bold"),
             fg=app.colors["text_main"], bg=app.colors["bg_card"]).pack(anchor="w", pady=(4, 2))
    app.entry_site_desc = tk.Entry(form, font=("Segoe UI", 10), bg=app.colors["bg_input"],
                                   fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat")
    app.entry_site_desc.insert(0, app.webui_config.get("description", "Portail WebUI pour evoX PS5"))
    app.entry_site_desc.pack(fill=tk.X, pady=(0, 10))

    gh_info = app.webui_config.get("github", {})

    # Utilisateur GitHub
    tk.Label(form, text="Utilisateur GitHub propriétaire :", font=("Segoe UI", 9, "bold"),
             fg=app.colors["text_main"], bg=app.colors["bg_card"]).pack(anchor="w", pady=(4, 2))
    app.entry_gh_user = tk.Entry(form, font=("Segoe UI", 10), bg=app.colors["bg_input"],
                                 fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat")
    app.entry_gh_user.insert(0, gh_info.get("user", app.config.get("githubUser", "")))
    app.entry_gh_user.pack(fill=tk.X, pady=(0, 10))

    # Dépôt Données (CoreOS)
    tk.Label(form, text="Dépôt GitHub Données (CoreOS) :", font=("Segoe UI", 9, "bold"),
             fg=app.colors["text_main"], bg=app.colors["bg_card"]).pack(anchor="w", pady=(4, 2))
    app.entry_data_repo = tk.Entry(form, font=("Segoe UI", 10), bg=app.colors["bg_input"],
                                   fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat")
    app.entry_data_repo.insert(0, gh_info.get("dataRepository", app.config.get("coreosRepo", "")))
    app.entry_data_repo.pack(fill=tk.X, pady=(0, 10))

    # Dépôt WebUI
    tk.Label(form, text="Dépôt GitHub WebUI :", font=("Segoe UI", 9, "bold"),
             fg=app.colors["text_main"], bg=app.colors["bg_card"]).pack(anchor="w", pady=(4, 2))
    app.entry_webui_repo = tk.Entry(form, font=("Segoe UI", 10), bg=app.colors["bg_input"],
                                    fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat")
    app.entry_webui_repo.insert(0, gh_info.get("webuiRepository", app.config.get("webuiRepo", "")))
    app.entry_webui_repo.pack(fill=tk.X, pady=(0, 15))

    btn_row = tk.Frame(inner, bg=app.colors["bg_card"])
    btn_row.pack(fill=tk.X, pady=(10, 0))

    def apply_general():
        app.webui_config["siteTitle"] = app.entry_site_title.get().strip()
        app.webui_config["description"] = app.entry_site_desc.get().strip()
        if "github" not in app.webui_config:
            app.webui_config["github"] = {}
        app.webui_config["github"]["user"] = app.entry_gh_user.get().strip()
        app.webui_config["github"]["dataRepository"] = app.clean_repo_name(app.entry_data_repo.get().strip())
        app.webui_config["github"]["webuiRepository"] = app.clean_repo_name(app.entry_webui_repo.get().strip())
        app.save_webui_config_to_disk()

    tk.Button(btn_row, text="💾 Enregistrer les Paramètres Généraux", font=("Segoe UI", 10, "bold"),
              bg=app.colors["accent"], fg="#ffffff", relief="flat", padx=16, pady=8, cursor="hand2",
              command=apply_general).pack(side=tk.LEFT)


def build_config_sources_tab(app, parent):
    """Onglet Sources : URLs principales et catalogues JSON / Pegasus distants."""
    inner = tk.Frame(parent, bg=app.colors["bg_card"], padx=15, pady=15)
    inner.pack(fill=tk.BOTH, expand=True)

    sources_cfg = app.webui_config.setdefault("sources", {})
    json_list = sources_cfg.setdefault("json", [])
    pegasus_list = sources_cfg.setdefault("pegasus", [])

    # Top URLs
    top_box = tk.Frame(inner, bg=app.colors["bg_card"])
    top_box.pack(fill=tk.X, pady=(0, 10))

    tk.Label(top_box, text="Source Payload Manager (pldmgr) :", font=("Segoe UI", 9, "bold"),
             fg=app.colors["text_main"], bg=app.colors["bg_card"]).pack(anchor="w", pady=(2, 2))
    app.entry_src_pldmgr = tk.Entry(top_box, font=("Segoe UI", 9), bg=app.colors["bg_input"],
                                    fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat")
    app.entry_src_pldmgr.insert(0, sources_cfg.get("pldmgr", ""))
    app.entry_src_pldmgr.pack(fill=tk.X, pady=(0, 6))

    tk.Label(top_box, text="Source Changelog :", font=("Segoe UI", 9, "bold"),
             fg=app.colors["text_main"], bg=app.colors["bg_card"]).pack(anchor="w", pady=(2, 2))
    app.entry_src_changelog = tk.Entry(top_box, font=("Segoe UI", 9), bg=app.colors["bg_input"],
                                       fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat")
    app.entry_src_changelog.insert(0, sources_cfg.get("changelog", ""))
    app.entry_src_changelog.pack(fill=tk.X, pady=(0, 8))

    # Splitter / Treeview
    tk.Label(inner, text="Catalogues JSON & Métadonnées Pegasus :", font=("Segoe UI", 10, "bold"),
             fg=app.colors["accent"], bg=app.colors["bg_card"]).pack(anchor="w", pady=(4, 4))

    table_frame = tk.Frame(inner, bg=app.colors["bg_card"])
    table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    columns = ("type", "name", "url")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=7)
    tree.heading("type", text="Type")
    tree.heading("name", text="Nom du Catalogue")
    tree.heading("url", text="URL Complète")
    tree.column("type", width=140, anchor="w")
    tree.column("name", width=220, anchor="w")
    tree.column("url", width=450, anchor="w")

    sb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=sb.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.pack(side=tk.RIGHT, fill=tk.Y)

    # Form
    form_frame = tk.Frame(inner, bg=app.colors["bg_input"], padx=12, pady=10,
                          highlightbackground=app.colors["border"], highlightthickness=1)
    form_frame.pack(fill=tk.X)

    f_row1 = tk.Frame(form_frame, bg=app.colors["bg_input"])
    f_row1.pack(fill=tk.X, pady=(0, 6))

    tk.Label(f_row1, text="Type :", font=("Segoe UI", 9, "bold"),
             fg=app.colors["text_muted"], bg=app.colors["bg_input"]).pack(side=tk.LEFT, padx=(0, 6))
    var_type = tk.StringVar(value="Catalogue JSON (json)")
    combo_type = ttk.Combobox(f_row1, textvariable=var_type, values=["Catalogue JSON (json)", "Métadonnées Pegasus (pegasus)"],
                              state="readonly", width=30)
    combo_type.pack(side=tk.LEFT, padx=(0, 15))

    tk.Label(f_row1, text="Nom :", font=("Segoe UI", 9, "bold"),
             fg=app.colors["text_muted"], bg=app.colors["bg_input"]).pack(side=tk.LEFT, padx=(0, 6))
    var_name = tk.StringVar()
    ent_name = tk.Entry(f_row1, textvariable=var_name, font=("Segoe UI", 9), bg=app.colors["bg_card"],
                        fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat")
    ent_name.pack(side=tk.LEFT, fill=tk.X, expand=True)

    f_row2 = tk.Frame(form_frame, bg=app.colors["bg_input"])
    f_row2.pack(fill=tk.X, pady=(0, 8))

    tk.Label(f_row2, text="URL :", font=("Segoe UI", 9, "bold"),
             fg=app.colors["text_muted"], bg=app.colors["bg_input"]).pack(side=tk.LEFT, padx=(0, 12))
    var_url = tk.StringVar()
    ent_url = tk.Entry(f_row2, textvariable=var_url, font=("Segoe UI", 9), bg=app.colors["bg_card"],
                       fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat")
    ent_url.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def refresh_tree():
        for item in tree.get_children():
            tree.delete(item)
        for i, item in enumerate(sources_cfg.get("json", [])):
            tree.insert("", tk.END, iid=f"json_{i}", values=("Catalogue JSON", item.get("name", ""), item.get("url", "")))
        for i, item in enumerate(sources_cfg.get("pegasus", [])):
            tree.insert("", tk.END, iid=f"pegasus_{i}", values=("Pegasus Meta", item.get("name", ""), item.get("url", "")))

    refresh_tree()

    def on_select(event):
        sel = tree.selection()
        if not sel:
            return
        item_id = sel[0]
        vals = tree.item(item_id, "values")
        if vals:
            var_type.set("Catalogue JSON (json)" if "JSON" in vals[0] else "Métadonnées Pegasus (pegasus)")
            var_name.set(vals[1])
            var_url.set(vals[2])

    tree.bind("<<TreeviewSelect>>", on_select)

    def add_item():
        n = var_name.get().strip()
        u = var_url.get().strip()
        if not n or not u:
            messagebox.showwarning("Champs requis", "Veuillez spécifier le nom et l'URL du catalogue.")
            return
        target = "json" if "json" in var_type.get().lower() else "pegasus"
        sources_cfg.setdefault(target, []).append({"name": n, "url": u})
        refresh_tree()
        clear_fields()
        app.log(f"Catalogue ajouté : {n} ({target})", "SUCCESS")

    def edit_item():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Sélection requise", "Veuillez sélectionner un élément dans la liste à modifier.")
            return
        item_id = sel[0]
        prefix, idx = item_id.split("_")
        idx = int(idx)
        n = var_name.get().strip()
        u = var_url.get().strip()
        if not n or not u:
            messagebox.showwarning("Champs requis", "Veuillez renseigner le nom et l'URL.")
            return
        new_target = "json" if "json" in var_type.get().lower() else "pegasus"
        if prefix == new_target:
            sources_cfg[prefix][idx] = {"name": n, "url": u}
        else:
            sources_cfg[prefix].pop(idx)
            sources_cfg.setdefault(new_target, []).append({"name": n, "url": u})
        refresh_tree()
        app.log(f"Catalogue modifié : {n}", "SUCCESS")

    def delete_item():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Sélection requise", "Veuillez sélectionner un élément à supprimer.")
            return
        item_id = sel[0]
        prefix, idx = item_id.split("_")
        idx = int(idx)
        item_name = sources_cfg[prefix][idx].get("name", "")
        if messagebox.askyesno("Confirmer", f"Supprimer le catalogue '{item_name}' ?"):
            sources_cfg[prefix].pop(idx)
            refresh_tree()
            clear_fields()
            app.log(f"Catalogue supprimé : {item_name}", "INFO")

    def clear_fields():
        var_name.set("")
        var_url.set("")
        if tree.selection():
            tree.selection_remove(tree.selection())

    btn_bar = tk.Frame(form_frame, bg=app.colors["bg_input"])
    btn_bar.pack(fill=tk.X)

    tk.Button(btn_bar, text="➕ Ajouter Catalogue", font=("Segoe UI", 9, "bold"),
              bg=app.colors["accent"], fg="#ffffff", relief="flat", padx=12, pady=5, cursor="hand2",
              command=add_item).pack(side=tk.LEFT, padx=(0, 6))

    tk.Button(btn_bar, text="✏️ Modifier la sélection", font=("Segoe UI", 9, "bold"),
              bg="#8b5cf6", fg="#ffffff", relief="flat", padx=12, pady=5, cursor="hand2",
              command=edit_item).pack(side=tk.LEFT, padx=6)

    tk.Button(btn_bar, text="🗑️ Supprimer la sélection", font=("Segoe UI", 9),
              bg="#dc2626", fg="#ffffff", relief="flat", padx=12, pady=5, cursor="hand2",
              command=delete_item).pack(side=tk.LEFT, padx=6)

    tk.Button(btn_bar, text="🧹 Vider", font=("Segoe UI", 9),
              bg=app.colors["bg_card"], fg=app.colors["text_muted"], relief="flat", padx=10, pady=5, cursor="hand2",
              command=clear_fields).pack(side=tk.LEFT, padx=6)


def build_config_webkit_tab(app, parent):
    """Onglet WebKit Exploits : Gestion des hôtes d'exploits PS5."""
    inner = tk.Frame(parent, bg=app.colors["bg_card"], padx=15, pady=15)
    inner.pack(fill=tk.BOTH, expand=True)

    webkit_list = app.webui_config.setdefault("webkit", [])

    tk.Label(inner, text="🧭 Hôtes d'Exploits WebKit PS5 Pris en Charge",
             font=("Segoe UI", 12, "bold"), fg=app.colors["accent"], bg=app.colors["bg_card"]).pack(anchor="w", pady=(0, 4))
    tk.Label(inner, text="Ajoutez, modifiez ou retirez des hôtes d'exploit injectés ou proposés dans l'interface WebUI.",
             font=("Segoe UI", 9), fg=app.colors["text_muted"], bg=app.colors["bg_card"]).pack(anchor="w", pady=(0, 10))

    # Table
    table_frame = tk.Frame(inner, bg=app.colors["bg_card"])
    table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    columns = ("name", "url", "version", "description")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)
    tree.heading("name", text="Nom de l'Hôte")
    tree.heading("url", text="Adresse URL")
    tree.heading("version", text="Firmware PS5")
    tree.heading("description", text="Description / Note")
    tree.column("name", width=180)
    tree.column("url", width=320)
    tree.column("version", width=120)
    tree.column("description", width=260)

    sb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=sb.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.pack(side=tk.RIGHT, fill=tk.Y)

    # Form
    form_frame = tk.Frame(inner, bg=app.colors["bg_input"], padx=12, pady=10,
                          highlightbackground=app.colors["border"], highlightthickness=1)
    form_frame.pack(fill=tk.X)

    f_grid = tk.Frame(form_frame, bg=app.colors["bg_input"])
    f_grid.pack(fill=tk.X, pady=(0, 8))

    var_name = tk.StringVar()
    var_url = tk.StringVar()
    var_ver = tk.StringVar(value="FW 3.00 - 4.51")
    var_desc = tk.StringVar()

    # Inputs grid
    tk.Label(f_grid, text="Nom :", font=("Segoe UI", 9, "bold"), fg=app.colors["text_muted"], bg=app.colors["bg_input"]).grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
    tk.Entry(f_grid, textvariable=var_name, font=("Segoe UI", 9), bg=app.colors["bg_card"], fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat", width=25).grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=2)

    tk.Label(f_grid, text="Firmware :", font=("Segoe UI", 9, "bold"), fg=app.colors["text_muted"], bg=app.colors["bg_input"]).grid(row=0, column=2, sticky="w", padx=(0, 4), pady=2)
    tk.Entry(f_grid, textvariable=var_ver, font=("Segoe UI", 9), bg=app.colors["bg_card"], fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat", width=18).grid(row=0, column=3, sticky="ew", pady=2)

    tk.Label(f_grid, text="URL :", font=("Segoe UI", 9, "bold"), fg=app.colors["text_muted"], bg=app.colors["bg_input"]).grid(row=1, column=0, sticky="w", padx=(0, 4), pady=2)
    tk.Entry(f_grid, textvariable=var_url, font=("Segoe UI", 9), bg=app.colors["bg_card"], fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat").grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=2)

    tk.Label(f_grid, text="Description :", font=("Segoe UI", 9, "bold"), fg=app.colors["text_muted"], bg=app.colors["bg_input"]).grid(row=1, column=2, sticky="w", padx=(0, 4), pady=2)
    tk.Entry(f_grid, textvariable=var_desc, font=("Segoe UI", 9), bg=app.colors["bg_card"], fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat").grid(row=1, column=3, sticky="ew", pady=2)

    f_grid.columnconfigure(1, weight=2)
    f_grid.columnconfigure(3, weight=3)

    def refresh_tree():
        for item in tree.get_children():
            tree.delete(item)
        for i, item in enumerate(webkit_list):
            tree.insert("", tk.END, iid=str(i), values=(
                item.get("name", ""), item.get("url", ""), item.get("version", ""), item.get("description", "")
            ))

    refresh_tree()

    def on_select(event):
        sel = tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        item = webkit_list[idx]
        var_name.set(item.get("name", ""))
        var_url.set(item.get("url", ""))
        var_ver.set(item.get("version", ""))
        var_desc.set(item.get("description", ""))

    tree.bind("<<TreeviewSelect>>", on_select)

    def add_item():
        n = var_name.get().strip()
        u = var_url.get().strip()
        if not n or not u:
            messagebox.showwarning("Champs requis", "Veuillez renseigner au moins le nom et l'URL de l'hôte.")
            return
        webkit_list.append({"name": n, "url": u, "version": var_ver.get().strip(), "description": var_desc.get().strip()})
        refresh_tree()
        clear_fields()
        app.log(f"Hôte WebKit ajouté : {n}", "SUCCESS")

    def edit_item():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Sélection requise", "Sélectionnez un hôte à modifier.")
            return
        idx = int(sel[0])
        n = var_name.get().strip()
        u = var_url.get().strip()
        if not n or not u:
            messagebox.showwarning("Champs requis", "Le nom et l'URL sont obligatoires.")
            return
        webkit_list[idx] = {"name": n, "url": u, "version": var_ver.get().strip(), "description": var_desc.get().strip()}
        refresh_tree()
        app.log(f"Hôte WebKit mis à jour : {n}", "SUCCESS")

    def delete_item():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Sélection requise", "Sélectionnez un hôte à supprimer.")
            return
        idx = int(sel[0])
        name = webkit_list[idx].get("name", "")
        if messagebox.askyesno("Confirmer", f"Supprimer l'hôte '{name}' ?"):
            webkit_list.pop(idx)
            refresh_tree()
            clear_fields()
            app.log(f"Hôte WebKit supprimé : {name}", "INFO")

    def clear_fields():
        var_name.set("")
        var_url.set("")
        var_ver.set("FW 3.00 - 4.51")
        var_desc.set("")
        if tree.selection():
            tree.selection_remove(tree.selection())

    def apply_preset(n, u, v, d):
        var_name.set(n)
        var_url.set(u)
        var_ver.set(v)
        var_desc.set(d)

    # Preset Chips
    chip_bar = tk.Frame(form_frame, bg=app.colors["bg_input"])
    chip_bar.pack(fill=tk.X, pady=(0, 6))

    tk.Label(chip_bar, text="Présélections :", font=("Segoe UI", 8, "bold"),
             fg=app.colors["text_muted"], bg=app.colors["bg_input"]).pack(side=tk.LEFT, padx=(0, 6))

    presets = [
        ("Idlesauce", "https://idlesauce.github.io/ps5-jb/", "FW 3.00 - 4.51", "Exploit WebKit & ELF Loader"),
        ("EchoStretch", "https://echostretch.github.io/ps5-jb/", "FW 3.00 - 4.51", "Host PS5 complet avec cache"),
        ("Kameleon", "https://kameleonre.github.io/ps5/", "FW 3.00 - 4.51", "Host multi-payloads"),
        ("Al-Azif", "https://es7in1.site/", "FW 3.00 - 4.51", "Host & DNS Exploit"),
    ]
    for p_name, p_url, p_ver, p_desc in presets:
        tk.Button(chip_bar, text=f"+ {p_name}", font=("Segoe UI", 8), bg=app.colors["bg_card"],
                  fg=app.colors["text_main"], relief="flat", padx=6, pady=2, cursor="hand2",
                  command=lambda n=p_name, u=p_url, v=p_ver, d=p_desc: apply_preset(n, u, v, d)).pack(side=tk.LEFT, padx=3)

    # Action buttons
    btn_bar = tk.Frame(form_frame, bg=app.colors["bg_input"])
    btn_bar.pack(fill=tk.X)

    tk.Button(btn_bar, text="➕ Ajouter Hôte", font=("Segoe UI", 9, "bold"),
              bg=app.colors["accent"], fg="#ffffff", relief="flat", padx=12, pady=5, cursor="hand2",
              command=add_item).pack(side=tk.LEFT, padx=(0, 6))

    tk.Button(btn_bar, text="✏️ Modifier la sélection", font=("Segoe UI", 9, "bold"),
              bg="#8b5cf6", fg="#ffffff", relief="flat", padx=12, pady=5, cursor="hand2",
              command=edit_item).pack(side=tk.LEFT, padx=6)

    tk.Button(btn_bar, text="🗑️ Supprimer la sélection", font=("Segoe UI", 9),
              bg="#dc2626", fg="#ffffff", relief="flat", padx=12, pady=5, cursor="hand2",
              command=delete_item).pack(side=tk.LEFT, padx=6)

    tk.Button(btn_bar, text="🧹 Vider", font=("Segoe UI", 9),
              bg=app.colors["bg_card"], fg=app.colors["text_muted"], relief="flat", padx=10, pady=5, cursor="hand2",
              command=clear_fields).pack(side=tk.LEFT, padx=6)


def build_config_services_tab(app, parent):
    """Onglet Services PS5 : Payload Manager, ports et services locaux."""
    inner = tk.Frame(parent, bg=app.colors["bg_card"], padx=15, pady=15)
    inner.pack(fill=tk.BOTH, expand=True)

    services_list = app.webui_config.setdefault("ps5_webui", [])

    tk.Label(inner, text="🖥️ Services PS5 & Serveurs WebUI Locaux",
             font=("Segoe UI", 12, "bold"), fg=app.colors["accent"], bg=app.colors["bg_card"]).pack(anchor="w", pady=(0, 4))
    tk.Label(inner, text="Configurez les serveurs et démons PS5 accessibles depuis la console (PLDMGR, Klog, FTP...).",
             font=("Segoe UI", 9), fg=app.colors["text_muted"], bg=app.colors["bg_card"]).pack(anchor="w", pady=(0, 10))

    table_frame = tk.Frame(inner, bg=app.colors["bg_card"])
    table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    columns = ("name", "port", "icon", "description")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)
    tree.heading("name", text="Nom du Service")
    tree.heading("port", text="Port PS5")
    tree.heading("icon", text="Classe Icône FontAwesome")
    tree.heading("description", text="Description")
    tree.column("name", width=220)
    tree.column("port", width=100, anchor="center")
    tree.column("icon", width=180)
    tree.column("description", width=380)

    sb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=sb.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.pack(side=tk.RIGHT, fill=tk.Y)

    # Form
    form_frame = tk.Frame(inner, bg=app.colors["bg_input"], padx=12, pady=10,
                          highlightbackground=app.colors["border"], highlightthickness=1)
    form_frame.pack(fill=tk.X)

    f_grid = tk.Frame(form_frame, bg=app.colors["bg_input"])
    f_grid.pack(fill=tk.X, pady=(0, 8))

    var_name = tk.StringVar()
    var_port = tk.StringVar(value="9020")
    var_icon = tk.StringVar(value="fa-solid fa-server")
    var_desc = tk.StringVar()

    tk.Label(f_grid, text="Nom Service :", font=("Segoe UI", 9, "bold"), fg=app.colors["text_muted"], bg=app.colors["bg_input"]).grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
    tk.Entry(f_grid, textvariable=var_name, font=("Segoe UI", 9), bg=app.colors["bg_card"], fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat", width=25).grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=2)

    tk.Label(f_grid, text="Port :", font=("Segoe UI", 9, "bold"), fg=app.colors["text_muted"], bg=app.colors["bg_input"]).grid(row=0, column=2, sticky="w", padx=(0, 4), pady=2)
    tk.Entry(f_grid, textvariable=var_port, font=("Segoe UI", 9), bg=app.colors["bg_card"], fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat", width=12).grid(row=0, column=3, sticky="ew", pady=2)

    tk.Label(f_grid, text="Icône FA :", font=("Segoe UI", 9, "bold"), fg=app.colors["text_muted"], bg=app.colors["bg_input"]).grid(row=1, column=0, sticky="w", padx=(0, 4), pady=2)
    tk.Entry(f_grid, textvariable=var_icon, font=("Segoe UI", 9), bg=app.colors["bg_card"], fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat").grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=2)

    tk.Label(f_grid, text="Description :", font=("Segoe UI", 9, "bold"), fg=app.colors["text_muted"], bg=app.colors["bg_input"]).grid(row=1, column=2, sticky="w", padx=(0, 4), pady=2)
    tk.Entry(f_grid, textvariable=var_desc, font=("Segoe UI", 9), bg=app.colors["bg_card"], fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat").grid(row=1, column=3, sticky="ew", pady=2)

    f_grid.columnconfigure(1, weight=2)
    f_grid.columnconfigure(3, weight=3)

    def refresh_tree():
        for item in tree.get_children():
            tree.delete(item)
        for i, item in enumerate(services_list):
            tree.insert("", tk.END, iid=str(i), values=(
                item.get("name", ""), item.get("port", ""), item.get("icon", ""), item.get("description", "")
            ))

    refresh_tree()

    def on_select(event):
        sel = tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        item = services_list[idx]
        var_name.set(item.get("name", ""))
        var_port.set(item.get("port", ""))
        var_icon.set(item.get("icon", ""))
        var_desc.set(item.get("description", ""))

    tree.bind("<<TreeviewSelect>>", on_select)

    def add_item():
        n = var_name.get().strip()
        if not n:
            messagebox.showwarning("Nom requis", "Veuillez renseigner le nom du service.")
            return
        services_list.append({"name": n, "port": var_port.get().strip(), "icon": var_icon.get().strip(), "description": var_desc.get().strip()})
        refresh_tree()
        clear_fields()
        app.log(f"Service PS5 ajouté : {n}", "SUCCESS")

    def edit_item():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Sélection requise", "Sélectionnez un service à modifier.")
            return
        idx = int(sel[0])
        n = var_name.get().strip()
        if not n:
            messagebox.showwarning("Nom requis", "Le nom est obligatoire.")
            return
        services_list[idx] = {"name": n, "port": var_port.get().strip(), "icon": var_icon.get().strip(), "description": var_desc.get().strip()}
        refresh_tree()
        app.log(f"Service PS5 mis à jour : {n}", "SUCCESS")

    def delete_item():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Sélection requise", "Sélectionnez un service à supprimer.")
            return
        idx = int(sel[0])
        name = services_list[idx].get("name", "")
        if messagebox.askyesno("Confirmer", f"Supprimer le service '{name}' ?"):
            services_list.pop(idx)
            refresh_tree()
            clear_fields()
            app.log(f"Service supprimé : {name}", "INFO")

    def clear_fields():
        var_name.set("")
        var_port.set("9020")
        var_icon.set("fa-solid fa-server")
        var_desc.set("")
        if tree.selection():
            tree.selection_remove(tree.selection())

    def apply_preset(n, p, ic, d):
        var_name.set(n)
        var_port.set(p)
        var_icon.set(ic)
        var_desc.set(d)

    chip_bar = tk.Frame(form_frame, bg=app.colors["bg_input"])
    chip_bar.pack(fill=tk.X, pady=(0, 6))

    tk.Label(chip_bar, text="Présélections :", font=("Segoe UI", 8, "bold"),
             fg=app.colors["text_muted"], bg=app.colors["bg_input"]).pack(side=tk.LEFT, padx=(0, 6))

    presets = [
        ("Payload Manager", "9020", "fa-solid fa-server", "Gestionnaire et chargeur de payloads PS5"),
        ("Klog Server", "9998", "fa-solid fa-terminal", "Console et journalisation kernel live"),
        ("FTP Server", "2121", "fa-solid fa-folder-open", "Transfert direct de fichiers PS5"),
        ("WebSDR Server", "8080", "fa-solid fa-globe", "Interface d'administration Web locale"),
    ]
    for p_name, p_port, p_icon, p_desc in presets:
        tk.Button(chip_bar, text=f"+ {p_name} ({p_port})", font=("Segoe UI", 8), bg=app.colors["bg_card"],
                  fg=app.colors["text_main"], relief="flat", padx=6, pady=2, cursor="hand2",
                  command=lambda n=p_name, p=p_port, ic=p_icon, d=p_desc: apply_preset(n, p, ic, d)).pack(side=tk.LEFT, padx=3)

    btn_bar = tk.Frame(form_frame, bg=app.colors["bg_input"])
    btn_bar.pack(fill=tk.X)

    tk.Button(btn_bar, text="➕ Ajouter Service", font=("Segoe UI", 9, "bold"),
              bg=app.colors["accent"], fg="#ffffff", relief="flat", padx=12, pady=5, cursor="hand2",
              command=add_item).pack(side=tk.LEFT, padx=(0, 6))

    tk.Button(btn_bar, text="✏️ Modifier la sélection", font=("Segoe UI", 9, "bold"),
              bg="#8b5cf6", fg="#ffffff", relief="flat", padx=12, pady=5, cursor="hand2",
              command=edit_item).pack(side=tk.LEFT, padx=6)

    tk.Button(btn_bar, text="🗑️ Supprimer la sélection", font=("Segoe UI", 9),
              bg="#dc2626", fg="#ffffff", relief="flat", padx=12, pady=5, cursor="hand2",
              command=delete_item).pack(side=tk.LEFT, padx=6)

    tk.Button(btn_bar, text="🧹 Vider", font=("Segoe UI", 9),
              bg=app.colors["bg_card"], fg=app.colors["text_muted"], relief="flat", padx=10, pady=5, cursor="hand2",
              command=clear_fields).pack(side=tk.LEFT, padx=6)


def build_config_creators_tab(app, parent):
    """Onglet Créateurs YouTube : Chaînes et créateurs de contenu de la scène."""
    inner = tk.Frame(parent, bg=app.colors["bg_card"], padx=15, pady=15)
    inner.pack(fill=tk.BOTH, expand=True)

    creators_list = app.webui_config.setdefault("youtube_creators", [])

    tk.Label(inner, text="📺 Créateurs YouTube & Guides Vidéos PS5",
             font=("Segoe UI", 12, "bold"), fg=app.colors["accent"], bg=app.colors["bg_card"]).pack(anchor="w", pady=(0, 4))
    tk.Label(inner, text="Gérez les chaînes partenaires et créateurs affichés dans l'onglet communautaire de la WebUI.",
             font=("Segoe UI", 9), fg=app.colors["text_muted"], bg=app.colors["bg_card"]).pack(anchor="w", pady=(0, 10))

    table_frame = tk.Frame(inner, bg=app.colors["bg_card"])
    table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    columns = ("name", "handle", "description")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)
    tree.heading("name", text="Nom du Créateur")
    tree.heading("handle", text="Handle / ID YouTube")
    tree.heading("description", text="Description")
    tree.column("name", width=220)
    tree.column("handle", width=200)
    tree.column("description", width=460)

    sb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=sb.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.pack(side=tk.RIGHT, fill=tk.Y)

    # Form
    form_frame = tk.Frame(inner, bg=app.colors["bg_input"], padx=12, pady=10,
                          highlightbackground=app.colors["border"], highlightthickness=1)
    form_frame.pack(fill=tk.X)

    f_grid = tk.Frame(form_frame, bg=app.colors["bg_input"])
    f_grid.pack(fill=tk.X, pady=(0, 8))

    var_name = tk.StringVar()
    var_handle = tk.StringVar()
    var_desc = tk.StringVar()

    tk.Label(f_grid, text="Nom Créateur :", font=("Segoe UI", 9, "bold"), fg=app.colors["text_muted"], bg=app.colors["bg_input"]).grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
    tk.Entry(f_grid, textvariable=var_name, font=("Segoe UI", 9), bg=app.colors["bg_card"], fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat", width=25).grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=2)

    tk.Label(f_grid, text="Handle YouTube :", font=("Segoe UI", 9, "bold"), fg=app.colors["text_muted"], bg=app.colors["bg_input"]).grid(row=0, column=2, sticky="w", padx=(0, 4), pady=2)
    tk.Entry(f_grid, textvariable=var_handle, font=("Segoe UI", 9), bg=app.colors["bg_card"], fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat", width=20).grid(row=0, column=3, sticky="ew", pady=2)

    tk.Label(f_grid, text="Description :", font=("Segoe UI", 9, "bold"), fg=app.colors["text_muted"], bg=app.colors["bg_input"]).grid(row=1, column=0, sticky="w", padx=(0, 4), pady=2)
    tk.Entry(f_grid, textvariable=var_desc, font=("Segoe UI", 9), bg=app.colors["bg_card"], fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat").grid(row=1, column=1, columnspan=3, sticky="ew", pady=2)

    f_grid.columnconfigure(1, weight=2)
    f_grid.columnconfigure(3, weight=2)

    def refresh_tree():
        for item in tree.get_children():
            tree.delete(item)
        for i, item in enumerate(creators_list):
            tree.insert("", tk.END, iid=str(i), values=(
                item.get("name", ""), item.get("handle", ""), item.get("description", "")
            ))

    refresh_tree()

    def on_select(event):
        sel = tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        item = creators_list[idx]
        var_name.set(item.get("name", ""))
        var_handle.set(item.get("handle", ""))
        var_desc.set(item.get("description", ""))

    tree.bind("<<TreeviewSelect>>", on_select)

    def add_item():
        n = var_name.get().strip()
        h = var_handle.get().strip()
        if not n or not h:
            messagebox.showwarning("Champs requis", "Veuillez renseigner le nom et le handle YouTube.")
            return
        creators_list.append({"name": n, "handle": h, "description": var_desc.get().strip()})
        refresh_tree()
        clear_fields()
        app.log(f"Créateur YouTube ajouté : {n}", "SUCCESS")

    def edit_item():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Sélection requise", "Sélectionnez un créateur à modifier.")
            return
        idx = int(sel[0])
        n = var_name.get().strip()
        h = var_handle.get().strip()
        if not n or not h:
            messagebox.showwarning("Champs requis", "Le nom et le handle sont obligatoires.")
            return
        creators_list[idx] = {"name": n, "handle": h, "description": var_desc.get().strip()}
        refresh_tree()
        app.log(f"Créateur mis à jour : {n}", "SUCCESS")

    def delete_item():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Sélection requise", "Sélectionnez un créateur à supprimer.")
            return
        idx = int(sel[0])
        name = creators_list[idx].get("name", "")
        if messagebox.askyesno("Confirmer", f"Supprimer le créateur '{name}' ?"):
            creators_list.pop(idx)
            refresh_tree()
            clear_fields()
            app.log(f"Créateur supprimé : {name}", "INFO")

    def clear_fields():
        var_name.set("")
        var_handle.set("")
        var_desc.set("")
        if tree.selection():
            tree.selection_remove(tree.selection())

    def apply_preset(n, h, d):
        var_name.set(n)
        var_handle.set(h)
        var_desc.set(d)

    chip_bar = tk.Frame(form_frame, bg=app.colors["bg_input"])
    chip_bar.pack(fill=tk.X, pady=(0, 6))

    tk.Label(chip_bar, text="Présélections :", font=("Segoe UI", 8, "bold"),
             fg=app.colors["text_muted"], bg=app.colors["bg_input"]).pack(side=tk.LEFT, padx=(0, 6))

    presets = [
        ("Modded Warfare", "ModdedWarfare", "Tutoriels vidéos complets PS5 Jailbreak"),
        ("Echo Stretch", "EchoStretch", "Actualités, tests exploits et firmwares PS5"),
        ("Michael Crump", "MichaelCrump", "Guides de développement et tutoriels PS5"),
        ("Modern Warfare", "ModernWarfare", "Démonstrations et analyses techniques"),
    ]
    for p_name, p_handle, p_desc in presets:
        tk.Button(chip_bar, text=f"+ {p_name}", font=("Segoe UI", 8), bg=app.colors["bg_card"],
                  fg=app.colors["text_main"], relief="flat", padx=6, pady=2, cursor="hand2",
                  command=lambda n=p_name, h=p_handle, d=p_desc: apply_preset(n, h, d)).pack(side=tk.LEFT, padx=3)

    btn_bar = tk.Frame(form_frame, bg=app.colors["bg_input"])
    btn_bar.pack(fill=tk.X)

    tk.Button(btn_bar, text="➕ Ajouter Créateur", font=("Segoe UI", 9, "bold"),
              bg=app.colors["accent"], fg="#ffffff", relief="flat", padx=12, pady=5, cursor="hand2",
              command=add_item).pack(side=tk.LEFT, padx=(0, 6))

    tk.Button(btn_bar, text="✏️ Modifier la sélection", font=("Segoe UI", 9, "bold"),
              bg="#8b5cf6", fg="#ffffff", relief="flat", padx=12, pady=5, cursor="hand2",
              command=edit_item).pack(side=tk.LEFT, padx=6)

    tk.Button(btn_bar, text="🗑️ Supprimer la sélection", font=("Segoe UI", 9),
              bg="#dc2626", fg="#ffffff", relief="flat", padx=12, pady=5, cursor="hand2",
              command=delete_item).pack(side=tk.LEFT, padx=6)

    tk.Button(btn_bar, text="🧹 Vider", font=("Segoe UI", 9),
              bg=app.colors["bg_card"], fg=app.colors["text_muted"], relief="flat", padx=10, pady=5, cursor="hand2",
              command=clear_fields).pack(side=tk.LEFT, padx=6)


def build_config_packs_tab(app, parent):
    """Onglet Packs AIO & Releases : Téléchargements et archives officielles."""
    inner = tk.Frame(parent, bg=app.colors["bg_card"], padx=15, pady=15)
    inner.pack(fill=tk.BOTH, expand=True)

    rel_cfg = app.webui_config.setdefault("releases", {})
    packs_list = rel_cfg.setdefault("packs", [])

    # Base URL
    top_box = tk.Frame(inner, bg=app.colors["bg_card"])
    top_box.pack(fill=tk.X, pady=(0, 10))

    tk.Label(top_box, text="URL de Base des Releases (baseUrl) :", font=("Segoe UI", 9, "bold"),
             fg=app.colors["text_main"], bg=app.colors["bg_card"]).pack(anchor="w", pady=(2, 2))
    app.entry_releases_base = tk.Entry(top_box, font=("Segoe UI", 9), bg=app.colors["bg_input"],
                                       fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat")
    app.entry_releases_base.insert(0, rel_cfg.get("baseUrl", ""))
    app.entry_releases_base.pack(fill=tk.X, pady=(0, 4))

    # Table
    table_frame = tk.Frame(inner, bg=app.colors["bg_card"])
    table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    columns = ("name", "file", "icon", "description")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)
    tree.heading("name", text="Nom du Pack AIO")
    tree.heading("file", text="Fichier Archive (.zip, .7z)")
    tree.heading("icon", text="Classe Icône FA")
    tree.heading("description", text="Description")
    tree.column("name", width=220)
    tree.column("file", width=260)
    tree.column("icon", width=160)
    tree.column("description", width=260)

    sb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=sb.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.pack(side=tk.RIGHT, fill=tk.Y)

    # Form
    form_frame = tk.Frame(inner, bg=app.colors["bg_input"], padx=12, pady=10,
                          highlightbackground=app.colors["border"], highlightthickness=1)
    form_frame.pack(fill=tk.X)

    f_grid = tk.Frame(form_frame, bg=app.colors["bg_input"])
    f_grid.pack(fill=tk.X, pady=(0, 8))

    var_name = tk.StringVar()
    var_file = tk.StringVar()
    var_icon = tk.StringVar(value="fa-solid fa-file-zipper")
    var_desc = tk.StringVar()

    tk.Label(f_grid, text="Nom Pack :", font=("Segoe UI", 9, "bold"), fg=app.colors["text_muted"], bg=app.colors["bg_input"]).grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
    tk.Entry(f_grid, textvariable=var_name, font=("Segoe UI", 9), bg=app.colors["bg_card"], fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat", width=25).grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=2)

    tk.Label(f_grid, text="Fichier Archive :", font=("Segoe UI", 9, "bold"), fg=app.colors["text_muted"], bg=app.colors["bg_input"]).grid(row=0, column=2, sticky="w", padx=(0, 4), pady=2)
    tk.Entry(f_grid, textvariable=var_file, font=("Segoe UI", 9), bg=app.colors["bg_card"], fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat", width=25).grid(row=0, column=3, sticky="ew", pady=2)

    tk.Label(f_grid, text="Icône FA :", font=("Segoe UI", 9, "bold"), fg=app.colors["text_muted"], bg=app.colors["bg_input"]).grid(row=1, column=0, sticky="w", padx=(0, 4), pady=2)
    tk.Entry(f_grid, textvariable=var_icon, font=("Segoe UI", 9), bg=app.colors["bg_card"], fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat").grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=2)

    tk.Label(f_grid, text="Description :", font=("Segoe UI", 9, "bold"), fg=app.colors["text_muted"], bg=app.colors["bg_input"]).grid(row=1, column=2, sticky="w", padx=(0, 4), pady=2)
    tk.Entry(f_grid, textvariable=var_desc, font=("Segoe UI", 9), bg=app.colors["bg_card"], fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat").grid(row=1, column=3, sticky="ew", pady=2)

    f_grid.columnconfigure(1, weight=2)
    f_grid.columnconfigure(3, weight=2)

    def refresh_tree():
        for item in tree.get_children():
            tree.delete(item)
        for i, item in enumerate(packs_list):
            tree.insert("", tk.END, iid=str(i), values=(
                item.get("name", ""), item.get("file", ""), item.get("icon", ""), item.get("description", "")
            ))

    refresh_tree()

    def on_select(event):
        sel = tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        item = packs_list[idx]
        var_name.set(item.get("name", ""))
        var_file.set(item.get("file", ""))
        var_icon.set(item.get("icon", ""))
        var_desc.set(item.get("description", ""))

    tree.bind("<<TreeviewSelect>>", on_select)

    def add_item():
        n = var_name.get().strip()
        f = var_file.get().strip()
        if not n or not f:
            messagebox.showwarning("Champs requis", "Veuillez renseigner le nom et le fichier archive.")
            return
        packs_list.append({"name": n, "file": f, "icon": var_icon.get().strip(), "description": var_desc.get().strip()})
        refresh_tree()
        clear_fields()
        app.log(f"Pack AIO ajouté : {n}", "SUCCESS")

    def edit_item():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Sélection requise", "Sélectionnez un pack à modifier.")
            return
        idx = int(sel[0])
        n = var_name.get().strip()
        f = var_file.get().strip()
        if not n or not f:
            messagebox.showwarning("Champs requis", "Le nom et le fichier sont obligatoires.")
            return
        packs_list[idx] = {"name": n, "file": f, "icon": var_icon.get().strip(), "description": var_desc.get().strip()}
        refresh_tree()
        app.log(f"Pack AIO mis à jour : {n}", "SUCCESS")

    def delete_item():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Sélection requise", "Sélectionnez un pack à supprimer.")
            return
        idx = int(sel[0])
        name = packs_list[idx].get("name", "")
        if messagebox.askyesno("Confirmer", f"Supprimer le pack '{name}' ?"):
            packs_list.pop(idx)
            refresh_tree()
            clear_fields()
            app.log(f"Pack supprimé : {name}", "INFO")

    def clear_fields():
        var_name.set("")
        var_file.set("")
        var_icon.set("fa-solid fa-file-zipper")
        var_desc.set("")
        if tree.selection():
            tree.selection_remove(tree.selection())

    def apply_preset(n, f, ic, d):
        var_name.set(n)
        var_file.set(f)
        var_icon.set(ic)
        var_desc.set(d)

    chip_bar = tk.Frame(form_frame, bg=app.colors["bg_input"])
    chip_bar.pack(fill=tk.X, pady=(0, 6))

    tk.Label(chip_bar, text="Présélections :", font=("Segoe UI", 8, "bold"),
             fg=app.colors["text_muted"], bg=app.colors["bg_input"]).pack(side=tk.LEFT, padx=(0, 6))

    presets = [
        ("Pack evoX AIO Full", "evoX-CoreOS-v2.6-AIO.zip", "fa-solid fa-box-archive", "Archive complète flux + webui + payloads"),
        ("Pack Payloads Only", "evoX-Payloads-v2.6.zip", "fa-solid fa-file-zipper", "Collection intégrale des payloads PS5"),
        ("Pack Pegasus Offline", "evoX-Pegasus-v2.6.zip", "fa-solid fa-gamepad", "Métadonnées et icônes pour Pegasus"),
    ]
    for p_name, p_file, p_icon, p_desc in presets:
        tk.Button(chip_bar, text=f"+ {p_name}", font=("Segoe UI", 8), bg=app.colors["bg_card"],
                  fg=app.colors["text_main"], relief="flat", padx=6, pady=2, cursor="hand2",
                  command=lambda n=p_name, f=p_file, ic=p_icon, d=p_desc: apply_preset(n, f, ic, d)).pack(side=tk.LEFT, padx=3)

    btn_bar = tk.Frame(form_frame, bg=app.colors["bg_input"])
    btn_bar.pack(fill=tk.X)

    tk.Button(btn_bar, text="➕ Ajouter Pack", font=("Segoe UI", 9, "bold"),
              bg=app.colors["accent"], fg="#ffffff", relief="flat", padx=12, pady=5, cursor="hand2",
              command=add_item).pack(side=tk.LEFT, padx=(0, 6))

    tk.Button(btn_bar, text="✏️ Modifier la sélection", font=("Segoe UI", 9, "bold"),
              bg="#8b5cf6", fg="#ffffff", relief="flat", padx=12, pady=5, cursor="hand2",
              command=edit_item).pack(side=tk.LEFT, padx=6)

    tk.Button(btn_bar, text="🗑️ Supprimer la sélection", font=("Segoe UI", 9),
              bg="#dc2626", fg="#ffffff", relief="flat", padx=12, pady=5, cursor="hand2",
              command=delete_item).pack(side=tk.LEFT, padx=6)

    tk.Button(btn_bar, text="🧹 Vider", font=("Segoe UI", 9),
              bg=app.colors["bg_card"], fg=app.colors["text_muted"], relief="flat", padx=10, pady=5, cursor="hand2",
              command=clear_fields).pack(side=tk.LEFT, padx=6)


def build_config_credits_tab(app, parent):
    """Onglet Crédits : Remerciements aux développeurs et projets."""
    inner = tk.Frame(parent, bg=app.colors["bg_card"], padx=15, pady=15)
    inner.pack(fill=tk.BOTH, expand=True)

    credits_raw = app.webui_config.setdefault("credits", [])

    tk.Label(inner, text="❤️ Crédits & Remerciements Communautaires",
             font=("Segoe UI", 12, "bold"), fg=app.colors["accent"], bg=app.colors["bg_card"]).pack(anchor="w", pady=(0, 4))
    tk.Label(inner, text="Développeurs, chercheurs en sécurité et contributeurs crédités dans le pied de page WebUI.",
             font=("Segoe UI", 9), fg=app.colors["text_muted"], bg=app.colors["bg_card"]).pack(anchor="w", pady=(0, 10))

    table_frame = tk.Frame(inner, bg=app.colors["bg_card"])
    table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    columns = ("num", "name", "role")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)
    tree.heading("num", text="#")
    tree.heading("name", text="Nom / Développeur / Projet")
    tree.heading("role", text="Rôle / Contribution")
    tree.column("num", width=50, anchor="center")
    tree.column("name", width=280)
    tree.column("role", width=480)

    sb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=sb.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.pack(side=tk.RIGHT, fill=tk.Y)

    # Form
    form_frame = tk.Frame(inner, bg=app.colors["bg_input"], padx=12, pady=10,
                          highlightbackground=app.colors["border"], highlightthickness=1)
    form_frame.pack(fill=tk.X)

    f_grid = tk.Frame(form_frame, bg=app.colors["bg_input"])
    f_grid.pack(fill=tk.X, pady=(0, 8))

    var_name = tk.StringVar()
    var_role = tk.StringVar()

    tk.Label(f_grid, text="Nom / Projet :", font=("Segoe UI", 9, "bold"), fg=app.colors["text_muted"], bg=app.colors["bg_input"]).grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
    tk.Entry(f_grid, textvariable=var_name, font=("Segoe UI", 9), bg=app.colors["bg_card"], fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat", width=28).grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=2)

    tk.Label(f_grid, text="Rôle / Contribution :", font=("Segoe UI", 9, "bold"), fg=app.colors["text_muted"], bg=app.colors["bg_input"]).grid(row=0, column=2, sticky="w", padx=(0, 4), pady=2)
    tk.Entry(f_grid, textvariable=var_role, font=("Segoe UI", 9), bg=app.colors["bg_card"], fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat").grid(row=0, column=3, sticky="ew", pady=2)

    f_grid.columnconfigure(1, weight=2)
    f_grid.columnconfigure(3, weight=3)

    def _get_credit_tuple(item):
        if isinstance(item, dict):
            return item.get("name", ""), item.get("role", "")
        return str(item), ""

    def refresh_tree():
        for item in tree.get_children():
            tree.delete(item)
        for i, item in enumerate(credits_raw, start=1):
            n, r = _get_credit_tuple(item)
            tree.insert("", tk.END, iid=str(i - 1), values=(i, n, r))

    refresh_tree()

    def on_select(event):
        sel = tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        n, r = _get_credit_tuple(credits_raw[idx])
        var_name.set(n)
        var_role.set(r)

    tree.bind("<<TreeviewSelect>>", on_select)

    def add_item():
        n = var_name.get().strip()
        r = var_role.get().strip()
        if not n:
            messagebox.showwarning("Nom requis", "Veuillez renseigner le nom ou le projet crédité.")
            return
        credits_raw.append({"name": n, "role": r} if r else n)
        refresh_tree()
        clear_fields()
        app.log(f"Crédit ajouté : {n}", "SUCCESS")

    def edit_item():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Sélection requise", "Sélectionnez un crédit à modifier.")
            return
        idx = int(sel[0])
        n = var_name.get().strip()
        r = var_role.get().strip()
        if not n:
            messagebox.showwarning("Nom requis", "Le nom est obligatoire.")
            return
        credits_raw[idx] = {"name": n, "role": r} if r else n
        refresh_tree()
        app.log(f"Crédit mis à jour : {n}", "SUCCESS")

    def delete_item():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Sélection requise", "Sélectionnez un crédit à supprimer.")
            return
        idx = int(sel[0])
        n, _ = _get_credit_tuple(credits_raw[idx])
        if messagebox.askyesno("Confirmer", f"Supprimer le crédit '{n}' ?"):
            credits_raw.pop(idx)
            refresh_tree()
            clear_fields()
            app.log(f"Crédit supprimé : {n}", "INFO")

    def clear_fields():
        var_name.set("")
        var_role.set("")
        if tree.selection():
            tree.selection_remove(tree.selection())

    def apply_preset(n, r):
        var_name.set(n)
        var_role.set(r)

    chip_bar = tk.Frame(form_frame, bg=app.colors["bg_input"])
    chip_bar.pack(fill=tk.X, pady=(0, 6))

    tk.Label(chip_bar, text="Présélections :", font=("Segoe UI", 8, "bold"),
             fg=app.colors["text_muted"], bg=app.colors["bg_input"]).pack(side=tk.LEFT, padx=(0, 6))

    presets = [
        ("SpecterDev", "PS5 Kernel Exploit Lead"),
        ("ChendoChap", "PS5 Kernel Port & Stability"),
        ("TheFloW", "BD-J & WebKit Vulnerability Research"),
        ("Al-Azif", "PS5 Host, Cache & Delivery"),
        ("Sleirsgoevy", "WebKit Exploit & Payloads"),
        ("ItsPLK", "PLDMGR Developer"),
    ]
    for p_name, p_role in presets:
        tk.Button(chip_bar, text=f"+ {p_name}", font=("Segoe UI", 8), bg=app.colors["bg_card"],
                  fg=app.colors["text_main"], relief="flat", padx=6, pady=2, cursor="hand2",
                  command=lambda n=p_name, r=p_role: apply_preset(n, r)).pack(side=tk.LEFT, padx=3)

    btn_bar = tk.Frame(form_frame, bg=app.colors["bg_input"])
    btn_bar.pack(fill=tk.X)

    tk.Button(btn_bar, text="➕ Ajouter Crédit", font=("Segoe UI", 9, "bold"),
              bg=app.colors["accent"], fg="#ffffff", relief="flat", padx=12, pady=5, cursor="hand2",
              command=add_item).pack(side=tk.LEFT, padx=(0, 6))

    tk.Button(btn_bar, text="✏️ Modifier la sélection", font=("Segoe UI", 9, "bold"),
              bg="#8b5cf6", fg="#ffffff", relief="flat", padx=12, pady=5, cursor="hand2",
              command=edit_item).pack(side=tk.LEFT, padx=6)

    tk.Button(btn_bar, text="🗑️ Supprimer la sélection", font=("Segoe UI", 9),
              bg="#dc2626", fg="#ffffff", relief="flat", padx=12, pady=5, cursor="hand2",
              command=delete_item).pack(side=tk.LEFT, padx=6)

    tk.Button(btn_bar, text="🧹 Vider", font=("Segoe UI", 9),
              bg=app.colors["bg_card"], fg=app.colors["text_muted"], relief="flat", padx=10, pady=5, cursor="hand2",
              command=clear_fields).pack(side=tk.LEFT, padx=6)


def build_config_socials_tab(app, parent):
    """Onglet Réseaux Sociaux : Liens communautaires et profils officiels."""
    inner = tk.Frame(parent, bg=app.colors["bg_card"], padx=15, pady=15)
    inner.pack(fill=tk.BOTH, expand=True)

    socials_list = app.webui_config.setdefault("socials", [])

    tk.Label(inner, text="🔗 Liens Communautaires & Réseaux Sociaux",
             font=("Segoe UI", 12, "bold"), fg=app.colors["accent"], bg=app.colors["bg_card"]).pack(anchor="w", pady=(0, 4))
    tk.Label(inner, text="Configurez vos liens officiels (Bluesky, Discord, GitHub, X, YouTube...).",
             font=("Segoe UI", 9), fg=app.colors["text_muted"], bg=app.colors["bg_card"]).pack(anchor="w", pady=(0, 10))

    table_frame = tk.Frame(inner, bg=app.colors["bg_card"])
    table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    columns = ("platform", "url", "icon")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)
    tree.heading("platform", text="Plateforme")
    tree.heading("url", text="Adresse URL Complète")
    tree.heading("icon", text="Classe Icône FontAwesome")
    tree.column("platform", width=180)
    tree.column("url", width=420)
    tree.column("icon", width=220)

    sb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=sb.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.pack(side=tk.RIGHT, fill=tk.Y)

    # Form
    form_frame = tk.Frame(inner, bg=app.colors["bg_input"], padx=12, pady=10,
                          highlightbackground=app.colors["border"], highlightthickness=1)
    form_frame.pack(fill=tk.X)

    f_grid = tk.Frame(form_frame, bg=app.colors["bg_input"])
    f_grid.pack(fill=tk.X, pady=(0, 8))

    var_plat = tk.StringVar()
    var_url = tk.StringVar()
    var_icon = tk.StringVar(value="fa-brands fa-github")

    tk.Label(f_grid, text="Plateforme :", font=("Segoe UI", 9, "bold"), fg=app.colors["text_muted"], bg=app.colors["bg_input"]).grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
    tk.Entry(f_grid, textvariable=var_plat, font=("Segoe UI", 9), bg=app.colors["bg_card"], fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat", width=20).grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=2)

    tk.Label(f_grid, text="Icône FA :", font=("Segoe UI", 9, "bold"), fg=app.colors["text_muted"], bg=app.colors["bg_input"]).grid(row=0, column=2, sticky="w", padx=(0, 4), pady=2)
    tk.Entry(f_grid, textvariable=var_icon, font=("Segoe UI", 9), bg=app.colors["bg_card"], fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat", width=22).grid(row=0, column=3, sticky="ew", pady=2)

    tk.Label(f_grid, text="URL :", font=("Segoe UI", 9, "bold"), fg=app.colors["text_muted"], bg=app.colors["bg_input"]).grid(row=1, column=0, sticky="w", padx=(0, 4), pady=2)
    tk.Entry(f_grid, textvariable=var_url, font=("Segoe UI", 9), bg=app.colors["bg_card"], fg=app.colors["text_main"], insertbackground="#ffffff", relief="flat").grid(row=1, column=1, columnspan=3, sticky="ew", pady=2)

    f_grid.columnconfigure(1, weight=2)
    f_grid.columnconfigure(3, weight=2)

    def refresh_tree():
        for item in tree.get_children():
            tree.delete(item)
        for i, item in enumerate(socials_list):
            tree.insert("", tk.END, iid=str(i), values=(
                item.get("platform", ""), item.get("url", ""), item.get("icon", "")
            ))

    refresh_tree()

    def on_select(event):
        sel = tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        item = socials_list[idx]
        var_plat.set(item.get("platform", ""))
        var_url.set(item.get("url", ""))
        var_icon.set(item.get("icon", ""))

    tree.bind("<<TreeviewSelect>>", on_select)

    def add_item():
        p = var_plat.get().strip()
        u = var_url.get().strip()
        if not p or not u:
            messagebox.showwarning("Champs requis", "Veuillez renseigner le nom de la plateforme et l'URL.")
            return
        socials_list.append({"platform": p, "url": u, "icon": var_icon.get().strip()})
        refresh_tree()
        clear_fields()
        app.log(f"Lien social ajouté : {p}", "SUCCESS")

    def edit_item():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Sélection requise", "Sélectionnez un lien à modifier.")
            return
        idx = int(sel[0])
        p = var_plat.get().strip()
        u = var_url.get().strip()
        if not p or not u:
            messagebox.showwarning("Champs requis", "La plateforme et l'URL sont obligatoires.")
            return
        socials_list[idx] = {"platform": p, "url": u, "icon": var_icon.get().strip()}
        refresh_tree()
        app.log(f"Lien social mis à jour : {p}", "SUCCESS")

    def delete_item():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Sélection requise", "Sélectionnez un lien à supprimer.")
            return
        idx = int(sel[0])
        plat = socials_list[idx].get("platform", "")
        if messagebox.askyesno("Confirmer", f"Supprimer le lien '{plat}' ?"):
            socials_list.pop(idx)
            refresh_tree()
            clear_fields()
            app.log(f"Lien supprimé : {plat}", "INFO")

    def clear_fields():
        var_plat.set("")
        var_url.set("")
        var_icon.set("fa-brands fa-github")
        if tree.selection():
            tree.selection_remove(tree.selection())

    def apply_preset(p, u, ic):
        var_plat.set(p)
        var_url.set(u)
        var_icon.set(ic)

    chip_bar = tk.Frame(form_frame, bg=app.colors["bg_input"])
    chip_bar.pack(fill=tk.X, pady=(0, 6))

    tk.Label(chip_bar, text="Présélections :", font=("Segoe UI", 8, "bold"),
             fg=app.colors["text_muted"], bg=app.colors["bg_input"]).pack(side=tk.LEFT, padx=(0, 6))

    presets = [
        ("Bluesky", "https://bsky.app/profile/votre-compte.bsky.social", "fa-brands fa-bluesky"),
        ("Discord", "https://discord.gg/votre-serveur", "fa-brands fa-discord"),
        ("GitHub", "https://github.com/votre-profil", "fa-brands fa-github"),
        ("X / Twitter", "https://x.com/votre-compte", "fa-brands fa-x-twitter"),
        ("YouTube", "https://youtube.com/@votre-chaine", "fa-brands fa-youtube"),
    ]
    for p_name, p_url, p_icon in presets:
        tk.Button(chip_bar, text=f"+ {p_name}", font=("Segoe UI", 8), bg=app.colors["bg_card"],
                  fg=app.colors["text_main"], relief="flat", padx=6, pady=2, cursor="hand2",
                  command=lambda p=p_name, u=p_url, ic=p_icon: apply_preset(p, u, ic)).pack(side=tk.LEFT, padx=3)

    btn_bar = tk.Frame(form_frame, bg=app.colors["bg_input"])
    btn_bar.pack(fill=tk.X)

    tk.Button(btn_bar, text="➕ Ajouter Réseau", font=("Segoe UI", 9, "bold"),
              bg=app.colors["accent"], fg="#ffffff", relief="flat", padx=12, pady=5, cursor="hand2",
              command=add_item).pack(side=tk.LEFT, padx=(0, 6))

    tk.Button(btn_bar, text="✏️ Modifier la sélection", font=("Segoe UI", 9, "bold"),
              bg="#8b5cf6", fg="#ffffff", relief="flat", padx=12, pady=5, cursor="hand2",
              command=edit_item).pack(side=tk.LEFT, padx=6)

    tk.Button(btn_bar, text="🗑️ Supprimer la sélection", font=("Segoe UI", 9),
              bg="#dc2626", fg="#ffffff", relief="flat", padx=12, pady=5, cursor="hand2",
              command=delete_item).pack(side=tk.LEFT, padx=6)

    tk.Button(btn_bar, text="🧹 Vider", font=("Segoe UI", 9),
              bg=app.colors["bg_card"], fg=app.colors["text_muted"], relief="flat", padx=10, pady=5, cursor="hand2",
              command=clear_fields).pack(side=tk.LEFT, padx=6)


def build_config_raw_tab(app, parent):
    """Onglet Éditeur Brut JSON : Vérification syntaxique et modification directe."""
    inner = tk.Frame(parent, bg=app.colors["bg_card"], padx=15, pady=15)
    inner.pack(fill=tk.BOTH, expand=True)

    tk.Label(inner, text="📝 Éditeur Brut de la Configuration WebUI (JSON)",
             font=("Segoe UI", 12, "bold"), fg=app.colors["accent"], bg=app.colors["bg_card"]).pack(anchor="w", pady=(0, 4))
    tk.Label(inner, text="Éditez directement la structure complète. La validation vérifie la syntaxe JSON avant application.",
             font=("Segoe UI", 9), fg=app.colors["text_muted"], bg=app.colors["bg_card"]).pack(anchor="w", pady=(0, 8))

    app.txt_raw_json = scrolledtext.ScrolledText(
        inner, bg="#05070d", fg="#38bdf8", insertbackground="#ffffff",
        font=("Consolas", 10), relief="flat", height=18
    )
    app.txt_raw_json.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    def load_json_to_editor():
        app.txt_raw_json.delete("1.0", tk.END)
        app.txt_raw_json.insert(tk.END, json.dumps(app.webui_config, indent=2, ensure_ascii=False))

    load_json_to_editor()

    def validate_and_apply():
        raw_text = app.txt_raw_json.get("1.0", tk.END).strip()
        try:
            parsed = json.loads(raw_text)
            app.webui_config = parsed
            messagebox.showinfo("JSON Valide", "La structure JSON a été validée et enregistrée en mémoire.")
            app.log("Configuration JSON brute validée avec succès.", "SUCCESS")
        except json.JSONDecodeError as err:
            messagebox.showerror("Erreur JSON", f"Erreur de syntaxe JSON à la ligne {err.lineno}, colonne {err.colno} :\n{err.msg}")
            app.log(f"Erreur validation JSON: {err}", "ERROR")

    def format_json():
        raw_text = app.txt_raw_json.get("1.0", tk.END).strip()
        try:
            parsed = json.loads(raw_text)
            app.txt_raw_json.delete("1.0", tk.END)
            app.txt_raw_json.insert(tk.END, json.dumps(parsed, indent=2, ensure_ascii=False))
        except json.JSONDecodeError as err:
            messagebox.showerror("Erreur", f"Impossible de formater : JSON invalide.\n{err}")

    btn_bar = tk.Frame(inner, bg=app.colors["bg_card"])
    btn_bar.pack(fill=tk.X)

    tk.Button(btn_bar, text="💾 Valider & Sauvegarder en Mémoire", font=("Segoe UI", 9, "bold"),
              bg=app.colors["accent"], fg="#ffffff", relief="flat", padx=14, pady=6, cursor="hand2",
              command=validate_and_apply).pack(side=tk.LEFT, padx=(0, 8))

    tk.Button(btn_bar, text="🧹 Réindenter JSON (2 espaces)", font=("Segoe UI", 9),
              bg=app.colors["bg_input"], fg=app.colors["text_main"], relief="flat", padx=12, pady=6, cursor="hand2",
              command=format_json).pack(side=tk.LEFT, padx=6)

    tk.Button(btn_bar, text="🔄 Recharger depuis la mémoire", font=("Segoe UI", 9),
              bg=app.colors["bg_input"], fg=app.colors["text_muted"], relief="flat", padx=12, pady=6, cursor="hand2",
              command=load_json_to_editor).pack(side=tk.LEFT, padx=6)

    tk.Button(btn_bar, text="💾 Écrire sur le disque (config.json)", font=("Segoe UI", 9, "bold"),
              bg="#8b5cf6", fg="#ffffff", relief="flat", padx=14, pady=6, cursor="hand2",
              command=lambda: (validate_and_apply(), app.save_webui_config_to_disk())).pack(side=tk.RIGHT)


class EvoXManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("evoX CoreOS & WebUI Manager — Multi-Repo & OPML Hub")
        self.root.geometry("1280x820")
        self.root.minsize(1050, 700)

        # Palette de couleurs moderne evoX (Dark + Crimson / Magenta)
        self.colors = {
            "bg_main": "#0b0f19",
            "bg_sidebar": "#070a12",
            "bg_card": "#111827",
            "bg_input": "#1f2937",
            "border": "#374151",
            "accent": "#ff2a5f",
            "accent_hover": "#e11d48",
            "accent_purple": "#8b5cf6",
            "text_main": "#f9fafb",
            "text_muted": "#9ca3af",
            "success": "#10b981",
            "warning": "#f59e0b",
            "error": "#ef4444"
        }

        self.root.configure(bg=self.colors["bg_main"])
        self.load_preferences()
        self.ensure_directories()

        # In-memory datasets
        self.feed_data = {"apps": [], "payloads": [], "ffpfsc": [], "pkg": []}
        self.webui_config = {}
        self.backups_list = []
        self.active_category = "payloads"
        self.active_file = None
        self.pegasus_items_list = []
        self.pegasus_metadata = {}
        coreos_repo = self.clean_repo_name(self.config.get("coreosRepo", ""))
        coreos_dir = self.get_repo_dir(coreos_repo) if coreos_repo else ""
        self.pegasus_catalog_path = os.path.join(coreos_dir, "json", "pegasus-dl", "catalog.json") if coreos_dir else ""
        self.pegasus_icon_dir = os.path.join(coreos_dir, "assets", "icon") if coreos_dir else ""
        self.pegasus_metadata_path = os.path.join(self.pegasus_icon_dir, "pegasus_metadata.json") if self.pegasus_icon_dir else ""
        self.pegasus_legacy_path = os.path.join(self.pegasus_icon_dir, "pegasus_icons.json") if self.pegasus_icon_dir else ""

        # Configure custom TTK styles
        self.setup_styles()

        # Navigation state (Header & Sidebar synchronization)
        self.current_section = "home"
        self.active_tab_key = "dashboard"
        self.active_webui_category = "general"
        self.header_buttons = {}
        self.nav_buttons = {}

        # Setup right-click context menu (Couper / Copier / Coller / Tout sélectionner) globally
        self._setup_context_menu()

        # Build UI layout
        self.create_header()
        self.create_main_container()

        # Seed data and refresh
        self.load_local_data()
        self.load_pegasus_data()
        self.log("Démarrage de evoX CoreOS & WebUI Manager", "INFO")
        self.log(f"Espace de travail initialisé dans {self.config['workspaceDir']}", "SUCCESS")

        # Si l'utilisateur n'a pas encore configuré et synchronisé les 2 dépôts, verrouiller et afficher la vue obligatoire
        if not self.is_ready_to_edit():
            self.show_repos_required_view()

    def is_ready_to_edit(self) -> bool:
        """Vérifie si les deux dépôts GitHub sont renseignés et qu'une synchronisation a été effectuée."""
        coreos = self.clean_repo_name(self.config.get("coreosRepo", ""))
        webui = self.clean_repo_name(self.config.get("webuiRepo", ""))
        if not coreos or not webui:
            return False
        if not self.config.get("hasSynchronized", False):
            return False
        return True

    def _setup_context_menu(self):
        """Menu contextuel clic droit pour couper, copier, coller, tout sélectionner sur tous les champs texte."""
        self.context_menu = tk.Menu(
            self.root, tearoff=0,
            bg=self.colors["bg_card"], fg=self.colors["text_main"],
            activebackground=self.colors["accent"], activeforeground="#ffffff",
            relief="flat", bd=1
        )
        self.context_menu.add_command(label="✂️ Couper", command=self._ctx_cut)
        self.context_menu.add_command(label="📋 Copier", command=self._ctx_copy)
        self.context_menu.add_command(label="📥 Coller", command=self._ctx_paste)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🔘 Tout sélectionner", command=self._ctx_select_all)

        def popup_event(event):
            w = event.widget
            self._ctx_widget = w
            try:
                w.focus_set()
                if isinstance(w, (tk.Entry, ttk.Entry)) or w.winfo_class() in ("Entry", "TEntry"):
                    if not w.selection_present():
                        idx = w.index(f"@{event.x}")
                        w.icursor(idx)

                has_sel = False
                try:
                    has_sel = bool(w.selection_get())
                except Exception:
                    has_sel = False

                self.context_menu.entryconfigure("✂️ Couper", state=tk.NORMAL if has_sel else tk.DISABLED)
                self.context_menu.entryconfigure("📋 Copier", state=tk.NORMAL if has_sel else tk.DISABLED)

                has_clip = False
                try:
                    has_clip = bool(self.root.clipboard_get())
                except Exception:
                    has_clip = False
                self.context_menu.entryconfigure("📥 Coller", state=tk.NORMAL if has_clip else tk.DISABLED)

                self.context_menu.tk_popup(event.x_root, event.y_root)
            except Exception:
                pass
            finally:
                try:
                    self.context_menu.grab_release()
                except Exception:
                    pass

        # Lier à toutes les classes de saisie Tkinter & TTK
        for cls_name in ("Entry", "Text", "TEntry", "ScrolledText"):
            self.root.bind_class(cls_name, "<Button-3>", popup_event)
            if sys.platform == "darwin":
                self.root.bind_class(cls_name, "<Button-2>", popup_event)

    def _ctx_cut(self):
        w = getattr(self, "_ctx_widget", None)
        if not w:
            return
        try:
            sel = w.selection_get()
            if sel:
                self.root.clipboard_clear()
                self.root.clipboard_append(sel)
                if isinstance(w, (tk.Entry, ttk.Entry)) or w.winfo_class() in ("Entry", "TEntry"):
                    w.delete(tk.SEL_FIRST, tk.SEL_LAST)
                elif isinstance(w, tk.Text) or w.winfo_class() in ("Text", "ScrolledText"):
                    w.delete("sel.first", "sel.last")
        except Exception:
            try:
                w.event_generate("<<Cut>>")
            except Exception:
                pass

    def _ctx_copy(self):
        w = getattr(self, "_ctx_widget", None)
        if not w:
            return
        try:
            sel = w.selection_get()
            if sel:
                self.root.clipboard_clear()
                self.root.clipboard_append(sel)
        except Exception:
            try:
                w.event_generate("<<Copy>>")
            except Exception:
                pass

    def _ctx_paste(self):
        w = getattr(self, "_ctx_widget", None)
        if not w:
            return
        try:
            text = self.root.clipboard_get()
            if text:
                if isinstance(w, (tk.Entry, ttk.Entry)) or w.winfo_class() in ("Entry", "TEntry"):
                    try:
                        w.delete(tk.SEL_FIRST, tk.SEL_LAST)
                    except Exception:
                        pass
                    w.insert(tk.INSERT, text)
                elif isinstance(w, tk.Text) or w.winfo_class() in ("Text", "ScrolledText"):
                    try:
                        w.delete("sel.first", "sel.last")
                    except Exception:
                        pass
                    w.insert(tk.INSERT, text)
        except Exception:
            try:
                w.event_generate("<<Paste>>")
            except Exception:
                pass

    def _ctx_select_all(self):
        w = getattr(self, "_ctx_widget", None)
        if not w:
            return
        try:
            if isinstance(w, (tk.Entry, ttk.Entry)) or w.winfo_class() in ("Entry", "TEntry"):
                w.select_range(0, tk.END)
                w.icursor(tk.END)
            elif isinstance(w, tk.Text) or w.winfo_class() in ("Text", "ScrolledText"):
                w.tag_add("sel", "1.0", "end")
        except Exception:
            pass

    def load_preferences(self):
        self.config = DEFAULT_CONFIG.copy()
        # Charger preferences.json ou evox_local_config.json
        candidate_paths = [
            CONFIG_FILE,
            os.path.join(self.config["workspaceDir"], "preferences.json")
        ]
        for p in candidate_paths:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        loaded = json.load(f)
                        self.config.update(loaded)
                        break
                except Exception as e:
                    print(f"Erreur chargement config: {e}")

        # Nettoyage des anciennes valeurs d'exemples si jamais synchronisé
        if not self.config.get("hasSynchronized", False):
            if self.config.get("coreosRepo") == "":
                self.config["coreosRepo"] = ""
                self.config["githubUser"] = ""
            if self.config.get("webuiRepo") == "":
                self.config["webuiRepo"] = ""

    def save_preferences(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            self.log("Préférences locales enregistrées avec succès.", "SUCCESS")
        except Exception as e:
            self.log(f"Erreur sauvegarde préférences: {e}", "ERROR")

    @staticmethod
    def clean_repo_name(repo_str: str) -> str:
        if not repo_str or not isinstance(repo_str, str):
            return ""
        s = repo_str.strip()
        s = re.sub(r"^https?://(www\.)?github\.com/", "", s, flags=re.IGNORECASE)
        s = re.sub(r"^git@github\.com:", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\.git$", "", s, flags=re.IGNORECASE)
        return s.strip("/")

    def get_repo_short_name(self, repo_str: str) -> str:
        clean = self.clean_repo_name(repo_str)
        if "/" in clean:
            return clean.split("/")[-1]
        return clean or "repo"

    def get_repo_dir(self, repo_str: str) -> str:
        cleaned = self.clean_repo_name(repo_str)
        if not cleaned:
            return ""
        short = self.get_repo_short_name(cleaned).lower()
        if "webui" in short:
            p1 = os.path.join(self.config["workspaceDir"], "evoX-CoreOS-webui")
            p2 = os.path.join(self.config["workspaceDir"], "evoX-CoreOS-WebUI")
            if os.path.exists(p1):
                return p1
            if os.path.exists(p2):
                return p2
            return p1
        elif "coreos" in short:
            p1 = os.path.join(self.config["workspaceDir"], "evoX-CoreOS")
            p2 = os.path.join(self.config["workspaceDir"], "evox-coreos")
            if os.path.exists(p2):
                return p2
            return p1
        else:
            return os.path.join(self.config["workspaceDir"], self.get_repo_short_name(cleaned))

    def get_github_headers(self):
        headers = {
            "User-Agent": "evoXManager/2.6 (Tkinter; Linux; x86_64)",
            "Accept": "application/vnd.github.v3+json"
        }
        token = self.config.get("githubToken", "").strip() or os.environ.get("GITHUB_TOKEN", "").strip()
        if token:
            if not token.startswith("Bearer ") and not token.startswith("token "):
                headers["Authorization"] = f"Bearer {token}"
            else:
                headers["Authorization"] = token
        return headers

    def ensure_directories(self):
        coreos_master = os.path.join(self.config["workspaceDir"], "evoX-CoreOS")
        webui_master = os.path.join(self.config["workspaceDir"], "evoX-CoreOS-webui")
        backup_dir = self.config.get("backupsDir", os.path.join(self.config["workspaceDir"], "backup"))
        log_dir = self.config.get("logsDir", os.path.join(self.config["workspaceDir"], "log"))
        exports_dir = self.config.get("exportsDir", os.path.join(self.config["workspaceDir"], "exports"))

        dirs_to_create = [
            self.config["workspaceDir"],
            backup_dir,
            log_dir,
            exports_dir,
            coreos_master,
            webui_master,
        ]
        for sub in [os.path.join("feed", "apps"), os.path.join("feed", "payloads"),
                    os.path.join("feed", "ffpfsc"), os.path.join("feed", "pkg"),
                    os.path.join("json", "pegasus-dl"), os.path.join("assets", "icon")]:
            dirs_to_create.append(os.path.join(coreos_master, sub))

        dirs_to_create.append(os.path.join(webui_master, "web", "data"))

        for path in dirs_to_create:
            try:
                os.makedirs(path, exist_ok=True)
            except Exception:
                pass

        self._cleanup_and_migrate_messy_folders()

    def _cleanup_and_migrate_messy_folders(self):
        """Nettoie automatiquement les dossiers parasites et unifie vers l'arborescence maîtresse:
        - /workspace/evoX-CoreOS/
        - /workspace/evoX-CoreOS-webui/
        - /workspace/backup/
        - /workspace/log/
        - En racine: UNIQUEMENT evox_manager.py et evox_local_config.json
        """
        try:
            ws_dir = self.config["workspaceDir"]
            coreos_master = os.path.join(ws_dir, "evoX-CoreOS")
            webui_master = os.path.join(ws_dir, "evoX-CoreOS-webui")
            target_cfg_json = os.path.join(webui_master, "web", "data", "config.json")
            backup_dir = self.config.get("backupsDir", os.path.join(ws_dir, "backup"))
            log_dir = self.config.get("logsDir", os.path.join(ws_dir, "log"))

            os.makedirs(os.path.dirname(target_cfg_json), exist_ok=True)
            os.makedirs(coreos_master, exist_ok=True)
            os.makedirs(backup_dir, exist_ok=True)
            os.makedirs(log_dir, exist_ok=True)

            # 1. Nettoyage du dossier parasite en racine ./web (si présent)
            root_web = os.path.join(SCRIPT_DIR, "web")
            if os.path.isdir(root_web):
                stray_cfg = os.path.join(root_web, "data", "config.json")
                if os.path.isfile(stray_cfg) and not os.path.exists(target_cfg_json):
                    try:
                        shutil.copy2(stray_cfg, target_cfg_json)
                    except Exception:
                        pass
                try:
                    shutil.rmtree(root_web, ignore_errors=True)
                    self.log("Dossier parasite en racine ./web supprimé avec succès.", "INFO")
                except Exception:
                    pass

            # 2. Nettoyage de /workspace/web (si présent)
            ws_web = os.path.join(ws_dir, "web")
            if os.path.isdir(ws_web):
                stray_cfg = os.path.join(ws_web, "data", "config.json")
                if os.path.isfile(stray_cfg) and not os.path.exists(target_cfg_json):
                    try:
                        shutil.copy2(stray_cfg, target_cfg_json)
                    except Exception:
                        pass
                try:
                    shutil.rmtree(ws_web, ignore_errors=True)
                except Exception:
                    pass

            # 3. Migration et suppression de /workspace/repos (si présent)
            ws_repos = os.path.join(ws_dir, "repos")
            if os.path.isdir(ws_repos):
                for item in os.listdir(ws_repos):
                    item_path = os.path.join(ws_repos, item)
                    if os.path.isdir(item_path):
                        if "webui" in item.lower():
                            cfg_sub = os.path.join(item_path, "web", "data", "config.json")
                            if os.path.isfile(cfg_sub) and not os.path.exists(target_cfg_json):
                                try:
                                    shutil.copy2(cfg_sub, target_cfg_json)
                                except Exception:
                                    pass
                        elif "coreos" in item.lower():
                            for sub in ["feed", "json", "assets"]:
                                src_sub = os.path.join(item_path, sub)
                                dst_sub = os.path.join(coreos_master, sub)
                                if os.path.isdir(src_sub):
                                    shutil.copytree(src_sub, dst_sub, dirs_exist_ok=True)
                try:
                    shutil.rmtree(ws_repos, ignore_errors=True)
                    self.log("Dossier /workspace/repos migré vers les dossiers maîtres et supprimé.", "INFO")
                except Exception:
                    pass

            # 4. Migration de /workspace/backups vers /workspace/backup
            old_backups = os.path.join(ws_dir, "backups")
            if os.path.isdir(old_backups) and old_backups != backup_dir:
                for f in os.listdir(old_backups):
                    src_f = os.path.join(old_backups, f)
                    dst_f = os.path.join(backup_dir, f)
                    if os.path.isfile(src_f) and not os.path.exists(dst_f):
                        shutil.move(src_f, dst_f)
                try:
                    shutil.rmtree(old_backups, ignore_errors=True)
                except Exception:
                    pass

            # 5. Migration de /workspace/logs vers /workspace/log
            old_logs = os.path.join(ws_dir, "logs")
            if os.path.isdir(old_logs) and old_logs != log_dir:
                for f in os.listdir(old_logs):
                    src_f = os.path.join(old_logs, f)
                    dst_f = os.path.join(log_dir, f)
                    if os.path.isfile(src_f) and not os.path.exists(dst_f):
                        shutil.move(src_f, dst_f)
                try:
                    shutil.rmtree(old_logs, ignore_errors=True)
                except Exception:
                    pass

            # 6. Suppression du fichier accidentel /workspace/evox_manager.py
            accidental_script = os.path.join(ws_dir, "evox_manager.py")
            if os.path.isfile(accidental_script):
                try:
                    os.remove(accidental_script)
                    self.log("Fichier parasite /workspace/evox_manager.py supprimé.", "INFO")
                except Exception:
                    pass

            # 7. Migration de preferences.json vers evox_local_config.json
            old_pref = os.path.join(ws_dir, "preferences.json")
            if os.path.isfile(old_pref):
                try:
                    if not os.path.isfile(CONFIG_FILE):
                        shutil.copy2(old_pref, CONFIG_FILE)
                    os.remove(old_pref)
                    self.log("Ancien preferences.json migré vers evox_local_config.json et nettoyé.", "INFO")
                except Exception:
                    pass

            # 8. Unification de evoX-CoreOS-WebUI vers evoX-CoreOS-webui
            alt_webui = os.path.join(ws_dir, "evoX-CoreOS-WebUI")
            if os.path.isdir(alt_webui) and alt_webui != webui_master:
                alt_cfg = os.path.join(alt_webui, "web", "data", "config.json")
                if os.path.isfile(alt_cfg) and not os.path.isfile(target_cfg_json):
                    try:
                        shutil.copy2(alt_cfg, target_cfg_json)
                    except Exception:
                        pass
                try:
                    shutil.rmtree(alt_webui, ignore_errors=True)
                except Exception:
                    pass

            # 9. Nettoyage des OPML parasites générés/dupliqués (apps.opml, ffpfsc.opml, payloads.opml, pkg.opml, source_aio.opml)
            unwanted_names = {"apps.opml", "ffpfsc.opml", "payloads.opml", "pkg.opml", "source_aio.opml", "sourceaio.opml"}
            feed_dir = os.path.join(coreos_master, "feed")
            if os.path.isdir(feed_dir):
                for r, _, files in os.walk(feed_dir):
                    for f in files:
                        if f.lower() in unwanted_names:
                            try:
                                os.remove(os.path.join(r, f))
                                self.log(f"Fichier OPML parasite supprimé : {f}", "INFO")
                            except Exception:
                                pass
        except Exception as e:
            self.log(f"Avertissement nettoyage dossiers: {e}", "WARN")
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Treeview styling
        style.configure("Treeview",
                        background=self.colors["bg_card"],
                        foreground=self.colors["text_main"],
                        fieldbackground=self.colors["bg_card"],
                        rowheight=28,
                        borderwidth=0)
        style.configure("Treeview.Heading",
                        background=self.colors["bg_input"],
                        foreground=self.colors["text_main"],
                        relief="flat",
                        font=("Segoe UI", 9, "bold"))
        style.map("Treeview",
                  background=[("selected", self.colors["accent"])],
                  foreground=[("selected", "#ffffff")])

        # Notebook tabs
        style.configure("TNotebook", background=self.colors["bg_main"], borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=self.colors["bg_card"],
                        foreground=self.colors["text_muted"],
                        padding=[12, 6],
                        font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", self.colors["accent"])],
                  foreground=[("selected", "#ffffff")])

    def create_header(self):
        header_frame = tk.Frame(self.root, bg=self.colors["bg_sidebar"], height=62)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)

        # Logo evoX CoreOS (cliquable -> Home)
        logo_frame = tk.Frame(header_frame, bg=self.colors["bg_sidebar"], cursor="hand2")
        logo_frame.pack(side=tk.LEFT, padx=16, pady=12)
        logo_frame.bind("<Button-1>", lambda e: self.select_section("home"))

        lbl_evo = tk.Label(logo_frame, text="evoX", font=("Segoe UI", 16, "bold"),
                           fg=self.colors["text_main"], bg=self.colors["bg_sidebar"])
        lbl_evo.pack(side=tk.LEFT)
        lbl_evo.bind("<Button-1>", lambda e: self.select_section("home"))

        lbl_core = tk.Label(logo_frame, text=" CoreOS", font=("Segoe UI", 16, "bold"),
                            fg=self.colors["accent"], bg=self.colors["bg_sidebar"])
        lbl_core.pack(side=tk.LEFT)
        lbl_core.bind("<Button-1>", lambda e: self.select_section("home"))

        lbl_badge = tk.Label(logo_frame, text="HUB V0.1", font=("Segoe UI", 8, "bold"),
                             fg="#a78bfa", bg="#1e1533", padx=6, pady=1)
        lbl_badge.pack(side=tk.LEFT, padx=8)

        # 5 Menus Principaux au centre
        self.main_nav_frame = tk.Frame(header_frame, bg=self.colors["bg_sidebar"])
        self.main_nav_frame.pack(side=tk.LEFT, padx=10, pady=10)

        main_sections = [
            ("home", "🏠 Home"),
            ("config", "⚙️ Configuration"),
            ("coreos", "💻 evoX-CoreOS"),
            ("webui", "🌐 evoX-CoreOS WebUI"),
            ("tools", "🛠️ Tools"),
        ]

        self.header_buttons = {}
        for sec_id, sec_label in main_sections:
            btn = tk.Button(
                self.main_nav_frame, text=sec_label, font=("Segoe UI", 9, "bold"),
                relief="flat", padx=12, pady=6, cursor="hand2",
                bg=self.colors["bg_sidebar"], fg=self.colors["text_muted"],
                activebackground=self.colors["bg_card"], activeforeground=self.colors["text_main"],
                command=lambda s=sec_id: self.select_section(s)
            )
            btn.pack(side=tk.LEFT, padx=3)
            self.header_buttons[sec_id] = btn

        # Actions rapides à droite
        actions_frame = tk.Frame(header_frame, bg=self.colors["bg_sidebar"])
        actions_frame.pack(side=tk.RIGHT, padx=16, pady=12)

        btn_sync = tk.Button(actions_frame, text="⚡ Sync", font=("Segoe UI", 9, "bold"),
                             bg=self.colors["accent"], fg="#ffffff", activebackground=self.colors["accent_hover"],
                             activeforeground="#ffffff", relief="flat", padx=12, pady=4, cursor="hand2",
                             command=self.sync_from_github_thread)
        btn_sync.pack(side=tk.LEFT, padx=4)

        btn_backup = tk.Button(actions_frame, text="💾 Sauvegarde", font=("Segoe UI", 9),
                               bg=self.colors["bg_input"], fg=self.colors["text_main"],
                               activebackground=self.colors["border"], activeforeground="#ffffff",
                               relief="flat", padx=10, pady=4, cursor="hand2", command=self.create_snapshot)
        btn_backup.pack(side=tk.LEFT, padx=4)

        user_display = self.config.get("githubUser") or "Non configuré"
        self.lbl_user_header = tk.Label(actions_frame, text=f"🐙 {user_display}",
                                        font=("Segoe UI", 9, "bold"), fg=self.colors["text_main"],
                                        bg=self.colors["bg_input"], padx=10, pady=4, relief="flat", cursor="hand2")
        self.lbl_user_header.pack(side=tk.LEFT, padx=4)
        self.lbl_user_header.bind("<Button-1>", lambda e: self.open_github_profile())

    def open_github_profile(self):
        user = self.config.get("githubUser")
        if not user and self.config.get("coreosRepo") and "/" in self.config.get("coreosRepo"):
            user = self.config.get("coreosRepo").split("/")[0]
        if user:
            url = f"https://github.com/{user}"
            try:
                webbrowser.open(url)
            except Exception:
                pass

    def create_main_container(self):
        container = tk.Frame(self.root, bg=self.colors["bg_main"])
        container.pack(fill=tk.BOTH, expand=True)

        # Sidebar à gauche
        self.sidebar_frame = tk.Frame(container, bg=self.colors["bg_sidebar"], width=240)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_frame.pack_propagate(False)

        # Zone de contenu principal à droite
        self.content_frame = tk.Frame(container, bg=self.colors["bg_main"])
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Initialiser avec la section 'home'
        self.select_section("home")

    def select_section(self, section_id):
        self.current_section = section_id

        # Mettre à jour les boutons du Header
        for s_id, btn in self.header_buttons.items():
            if s_id == section_id:
                fg_color = "#c084fc" if s_id == "webui" else self.colors["accent"]
                btn.configure(bg=self.colors["bg_card"], fg=fg_color, font=("Segoe UI", 9, "bold"))
            else:
                btn.configure(bg=self.colors["bg_sidebar"], fg=self.colors["text_muted"], font=("Segoe UI", 9))

        # Reconstruire la Sidebar pour n'afficher que les sous-menus de cette section
        self.update_sidebar()

        # Vérification pré-requis : Dépôts obligatoires et synchronisation avant édition
        if section_id in ("coreos", "webui") and not self.is_ready_to_edit():
            self.show_repos_required_view(redirect_section=section_id)
            return

        # Naviguer vers la vue par défaut de la section
        if section_id == "home":
            self.navigate_to("dashboard", self.show_dashboard_view)
        elif section_id == "config":
            self.navigate_to("preferences", self.show_preferences_view)
        elif section_id == "coreos":
            self.navigate_to("opml_feed", self.show_opml_view)
        elif section_id == "webui":
            self.active_webui_category = "general"
            self.navigate_to("webui_general", lambda: self.show_webui_subview("general"))
        elif section_id == "tools":
            self.navigate_to("icons_browser", self.show_icons_view)

    def update_sidebar(self):
        # Nettoyer la sidebar existante
        for widget in self.sidebar_frame.winfo_children():
            widget.destroy()

        # Bannière de section active
        section_meta = {
            "home": ("SECTION ACTIVE", "Accueil & Hub", "Tableau de Bord"),
            "config": ("SECTION ACTIVE", "Configuration", "Paramètres & Maintenance"),
            "coreos": ("SECTION ACTIVE", "evoX-CoreOS", "Flux OPML & Données"),
            "webui": ("SECTION ACTIVE", "evoX-CoreOS WebUI", "Configuration JSON"),
            "tools": ("SECTION ACTIVE", "Tools", "Outils & Scripts"),
        }
        sec_tag, sec_title, sec_sub = section_meta.get(self.current_section, ("SECTION", "Menu", ""))

        banner_frame = tk.Frame(self.sidebar_frame, bg=self.colors["bg_input"], padx=12, pady=10,
                                highlightbackground=self.colors["border"], highlightthickness=1)
        banner_frame.pack(fill=tk.X, padx=10, pady=(12, 8))

        tk.Label(banner_frame, text=sec_tag, font=("Segoe UI", 8, "bold"),
                 fg=self.colors["accent"], bg=self.colors["bg_input"]).pack(anchor="w")
        tk.Label(banner_frame, text=sec_title, font=("Segoe UI", 11, "bold"),
                 fg=self.colors["text_main"], bg=self.colors["bg_input"]).pack(anchor="w", pady=(2, 0))
        if sec_sub:
            tk.Label(banner_frame, text=sec_sub, font=("Segoe UI", 8),
                     fg=self.colors["text_muted"], bg=self.colors["bg_input"]).pack(anchor="w")

        # Label Sous-Menus
        tk.Label(self.sidebar_frame, text="SOUS-MENUS",
                 font=("Segoe UI", 8, "bold"), fg=self.colors["text_muted"],
                 bg=self.colors["bg_sidebar"]).pack(anchor="w", padx=15, pady=(6, 6))

        # Définition des sous-menus strictement filtrés par section
        sub_menus = []
        if self.current_section == "home":
            sub_menus = [
                ("dashboard", "📊 Tableau de Bord", self.show_dashboard_view),
            ]
        elif self.current_section == "config":
            sub_menus = [
                ("preferences", "⚙️ Préférences Locales", self.show_preferences_view),
                ("sync_repos", "🔄 Gestion & Sync Dépôts", self.show_sync_view),
                ("snapshots", "🛡️ Versioning & Sauvegardes", self.show_snapshots_view),
                ("logs_view", "📋 Console & Journaux", self.show_logs_view),
            ]
        elif self.current_section == "coreos":
            sub_menus = [
                ("opml_feed", "📁 evoX CoreOS (Flux OPML)", self.show_opml_view),
                ("pegasus_meta", "🎮 Pegasus Metadata & Icônes", self.show_pegasus_view),
            ]
        elif self.current_section == "webui":
            sub_menus = [
                ("webui_general", "🌐 Général & GitHub", lambda: self.show_webui_subview("general")),
                ("webui_sources", "🗄️ Sources & Catalogues", lambda: self.show_webui_subview("sources")),
                ("webui_webkit", "🧭 WebKit Exploits", lambda: self.show_webui_subview("webkit")),
                ("webui_services", "🖥️ Services PS5", lambda: self.show_webui_subview("services")),
                ("webui_creators", "📺 Créateurs YouTube", lambda: self.show_webui_subview("creators")),
                ("webui_packs", "📦 Packs AIO & Releases", lambda: self.show_webui_subview("packs")),
                ("webui_credits", "❤️ Crédits & Remerciements", lambda: self.show_webui_subview("credits")),
                ("webui_socials", "🔗 Réseaux Sociaux", lambda: self.show_webui_subview("socials")),
                ("webui_raw", "📝 Éditeur Brut JSON", lambda: self.show_webui_subview("raw")),
            ]
        elif self.current_section == "tools":
            sub_menus = [
                ("icons_browser", "🎨 Icônes & Assets", self.show_icons_view),
                ("python_app", "🐍 App Python Tkinter", self.show_python_info_view),
            ]

        self.nav_buttons = {}
        for key, text, cmd in sub_menus:
            btn = tk.Button(self.sidebar_frame, text=text, font=("Segoe UI", 9),
                            anchor="w", relief="flat", padx=14, pady=7, cursor="hand2",
                            bg=self.colors["bg_sidebar"], fg=self.colors["text_main"],
                            activebackground=self.colors["bg_card"],
                            activeforeground=self.colors["accent"],
                            command=lambda c=cmd, k=key: self.navigate_to(k, c))
            btn.pack(fill=tk.X, padx=8, pady=1)
            self.nav_buttons[key] = btn

        # Mini résumé des flux si section home ou coreos
        if self.current_section in ("home", "coreos"):
            stats_box = tk.Frame(self.sidebar_frame, bg=self.colors["bg_card"], padx=10, pady=8,
                                 highlightbackground=self.colors["border"], highlightthickness=1)
            stats_box.pack(fill=tk.X, padx=10, pady=(15, 5))

            tk.Label(stats_box, text="FLUX COREOS", font=("Segoe UI", 8, "bold"),
                     fg=self.colors["text_muted"], bg=self.colors["bg_card"]).pack(anchor="w", pady=(0, 4))

            counts = [
                ("⚡ Payloads", len(self.feed_data.get("payloads", []))),
                ("📦 PKG", len(self.feed_data.get("pkg", []))),
                ("🛡️ FFPFSC", len(self.feed_data.get("ffpfsc", []))),
                ("🎮 Apps", len(self.feed_data.get("apps", []))),
            ]
            for label, cnt in counts:
                row = tk.Frame(stats_box, bg=self.colors["bg_card"])
                row.pack(fill=tk.X, pady=1)
                tk.Label(row, text=label, font=("Segoe UI", 8),
                         fg=self.colors["text_main"], bg=self.colors["bg_card"]).pack(side=tk.LEFT)
                tk.Label(row, text=str(cnt), font=("Segoe UI", 8, "bold"),
                         fg=self.colors["accent"], bg=self.colors["bg_card"]).pack(side=tk.RIGHT)

        # Info version en bas de la sidebar
        lbl_ver = tk.Label(self.sidebar_frame, text="evoX CoreOS v0.1\nPython Tkinter Engine",
                           font=("Segoe UI", 8), fg=self.colors["text_muted"],
                           bg=self.colors["bg_sidebar"], justify=tk.CENTER)
        lbl_ver.pack(side=tk.BOTTOM, pady=12)

    def navigate_to(self, key, command):
        self.active_tab_key = key
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(bg=self.colors["bg_card"], fg=self.colors["accent"], font=("Segoe UI", 9, "bold"))
            else:
                btn.configure(bg=self.colors["bg_sidebar"], fg=self.colors["text_main"], font=("Segoe UI", 9))
        self.clear_content_frame()
        command()

    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_repos_required_view(self, redirect_section="home", redirect_action=None):
        """Vue obligatoire invitant l'utilisateur à renseigner ses 2 dépôts et à lancer la synchronisation."""
        self.clear_content_frame()

        top_banner = tk.Frame(self.content_frame, bg=self.colors["bg_card"], padx=20, pady=16,
                              highlightbackground=self.colors["border"], highlightthickness=1)
        top_banner.pack(fill=tk.X, pady=(0, 15))

        tk.Label(top_banner, text="INITIALISATION DU HUB EVOX",
                 font=("Segoe UI", 8, "bold"), fg=self.colors["accent"], bg=self.colors["bg_card"]).pack(anchor="w")
        tk.Label(top_banner, text="🔒 Configuration & Synchronisation Initiale Requise",
                 font=("Segoe UI", 16, "bold"), fg=self.colors["text_main"], bg=self.colors["bg_card"]).pack(anchor="w", pady=(2, 2))
        tk.Label(top_banner,
                 text="Pour pouvoir éditer les fichiers de flux evoX-CoreOS et configurer la WebUI, vous devez obligatoirement ajouter vos deux dépôts GitHub et synchroniser.",
                 font=("Segoe UI", 9), fg=self.colors["text_muted"], bg=self.colors["bg_card"]).pack(anchor="w")

        card = tk.Frame(self.content_frame, bg=self.colors["bg_card"], padx=25, pady=20,
                        highlightbackground=self.colors["border"], highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True)

        step_box = tk.Frame(card, bg=self.colors["bg_input"], padx=15, pady=12,
                            highlightbackground=self.colors["border"], highlightthickness=1)
        step_box.pack(fill=tk.X, pady=(0, 15))

        tk.Label(step_box, text="ℹ️ Démarrage à blanc : aucune information pré-remplie.", font=("Segoe UI", 10, "bold"),
                 fg="#38bdf8", bg=self.colors["bg_input"]).pack(anchor="w")
        tk.Label(step_box,
                 text="Renseignez ci-dessous les deux dépôts GitHub associés (votre dépôt CoreOS pour les flux OPML/données, et votre dépôt WebUI pour l'interface web). Dès que la synchronisation est terminée, tous les outils d'édition seront automatiquement débloqués.",
                 font=("Segoe UI", 9), fg=self.colors["text_muted"], bg=self.colors["bg_input"], justify=tk.LEFT).pack(anchor="w", pady=(4, 0))

        form_grid = tk.Frame(card, bg=self.colors["bg_card"])
        form_grid.pack(fill=tk.X, pady=(0, 10))

        # CoreOS Repo
        tk.Label(form_grid, text="📦 Dépôt GitHub evoX-CoreOS (Données & OPML) : *",
                 font=("Segoe UI", 9, "bold"), fg=self.colors["text_main"], bg=self.colors["bg_card"]).pack(anchor="w", pady=(4, 2))
        ent_coreos = tk.Entry(form_grid, font=("Segoe UI", 10), bg=self.colors["bg_input"],
                              fg=self.colors["text_main"], insertbackground="#ffffff", relief="flat")
        ent_coreos.insert(0, self.config.get("coreosRepo", ""))
        ent_coreos.pack(fill=tk.X, pady=(0, 10))

        # WebUI Repo
        tk.Label(form_grid, text="🌐 Dépôt GitHub evoX-CoreOS-WebUI (Site & config.json) : *",
                 font=("Segoe UI", 9, "bold"), fg=self.colors["text_main"], bg=self.colors["bg_card"]).pack(anchor="w", pady=(4, 2))
        ent_webui = tk.Entry(form_grid, font=("Segoe UI", 10), bg=self.colors["bg_input"],
                             fg=self.colors["text_main"], insertbackground="#ffffff", relief="flat")
        ent_webui.insert(0, self.config.get("webuiRepo", ""))
        ent_webui.pack(fill=tk.X, pady=(0, 10))

        # GitHub Token
        tk.Label(form_grid, text="🔑 Token Personnel GitHub (Optionnel, utile pour dépôts privés ou rate-limit) :",
                 font=("Segoe UI", 9, "bold"), fg=self.colors["text_muted"], bg=self.colors["bg_card"]).pack(anchor="w", pady=(4, 2))
        ent_token = tk.Entry(form_grid, font=("Segoe UI", 10), bg=self.colors["bg_input"],
                             fg=self.colors["text_main"], insertbackground="#ffffff", relief="flat", show="*")
        ent_token.insert(0, self.config.get("githubToken", ""))
        ent_token.pack(fill=tk.X, pady=(0, 15))

        # Live sync console
        tk.Label(card, text="Journal de Synchronisation :", font=("Segoe UI", 9, "bold"),
                 fg=self.colors["text_muted"], bg=self.colors["bg_card"]).pack(anchor="w", pady=(5, 4))

        self.init_sync_log_txt = scrolledtext.ScrolledText(card, height=8, bg="#05070d", fg="#10b981",
                                                           font=("Consolas", 9), insertbackground="#ffffff", relief="flat")
        self.init_sync_log_txt.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        self.init_sync_log_txt.insert(tk.END, "En attente de la saisie des deux dépôts et du lancement de la synchronisation...\n")

        btn_row = tk.Frame(card, bg=self.colors["bg_card"])
        btn_row.pack(fill=tk.X)

        def run_initial_sync():
            c_repo = self.clean_repo_name(ent_coreos.get())
            w_repo = self.clean_repo_name(ent_webui.get())
            tok = ent_token.get().strip()

            if not c_repo or not w_repo:
                messagebox.showwarning("Dépôts obligatoires",
                                       "Veuillez renseigner les deux dépôts GitHub (CoreOS et WebUI) avant de synchroniser.")
                return

            self.config["coreosRepo"] = c_repo
            self.config["webuiRepo"] = w_repo
            self.config["githubToken"] = tok
            if not self.config.get("githubUser") and "/" in c_repo:
                self.config["githubUser"] = c_repo.split("/")[0]
            self.save_preferences()

            btn_do_sync.configure(state=tk.DISABLED, text="⏳ Synchronisation en cours...")
            self.init_sync_log_txt.insert(tk.END, f"\n=== Lancement de la synchronisation ({c_repo} & {w_repo}) ===\n")
            self.init_sync_log_txt.see(tk.END)

            self.sync_log_txt = self.init_sync_log_txt

            def post_sync_check():
                try:
                    if btn_do_sync.winfo_exists():
                        btn_do_sync.configure(state=tk.NORMAL, text="⚡ Enregistrer & Synchroniser Maintenant")
                except Exception:
                    pass
                if self.is_ready_to_edit():
                    messagebox.showinfo("Dépôts Initialisés !",
                                        "Synchronisation effectuée avec succès !\nTous les menus et outils d'édition sont maintenant accessibles.")
                    try:
                        if redirect_action:
                            redirect_action()
                        elif redirect_section == "webui":
                            self.select_section("webui")
                        elif redirect_section == "coreos":
                            self.select_section("coreos")
                        else:
                            self.select_section("home")
                    except Exception as e_red:
                        self.log(f"Redirection post-sync fallback: {e_red}", "WARN")
                        self.select_section("home")

            self._post_sync_action = post_sync_check
            self.sync_from_github_thread("both")

        btn_do_sync = tk.Button(btn_row, text="⚡ Enregistrer & Synchroniser Maintenant", font=("Segoe UI", 10, "bold"),
                                bg=self.colors["accent"], fg="#ffffff", activebackground=self.colors["accent_hover"],
                                activeforeground="#ffffff", relief="flat", padx=20, pady=8, cursor="hand2",
                                command=run_initial_sync)
        btn_do_sync.pack(side=tk.LEFT)

    # ==========================================
    # VUE 1: TABLEAU DE BORD (DASHBOARD)
    # ==========================================
    def show_dashboard_view(self):
        # Stats summary counts - strictly real counts from loaded files
        payloads_files = len(self.feed_data.get("payloads", []))
        total_payload_items = sum(len(f.get("outlines", [])) for f in self.feed_data.get("payloads", []))

        pkg_files = len(self.feed_data.get("pkg", []))
        total_pkg_items = sum(len(f.get("outlines", [])) for f in self.feed_data.get("pkg", []))

        ffpfsc_files = len(self.feed_data.get("ffpfsc", []))
        total_ffpfsc_items = sum(len(f.get("outlines", [])) for f in self.feed_data.get("ffpfsc", []))

        apps_files = len(self.feed_data.get("apps", []))
        total_apps_items = sum(len(f.get("outlines", [])) for f in self.feed_data.get("apps", []))

        # Hero Banner
        hero = tk.Frame(self.content_frame, bg=self.colors["bg_card"], highlightbackground=self.colors["border"], highlightthickness=1)
        hero.pack(fill=tk.X, pady=(0, 15))

        hero_inner = tk.Frame(hero, bg=self.colors["bg_card"])
        hero_inner.pack(padx=25, pady=20)

        lbl_hero_title = tk.Label(hero_inner, text="evoX CoreOS WebUI", font=("Segoe UI", 22, "bold"),
                                  fg=self.colors["text_main"], bg=self.colors["bg_card"])
        lbl_hero_title.pack()

        lbl_hero_sub = tk.Label(hero_inner, text="Dashboard centralisé pour la gestion, les flux et le store evoX PS5",
                                font=("Segoe UI", 11), fg=self.colors["text_muted"], bg=self.colors["bg_card"])
        lbl_hero_sub.pack(pady=5)

        # Status badge if not synchronized
        has_sync = self.config.get("hasSynchronized", False) and bool(self.config.get("coreosRepo") or self.config.get("webuiRepo"))
        if not has_sync:
            sync_warn_box = tk.Frame(hero_inner, bg=self.colors["bg_input"], padx=10, pady=5,
                                     highlightbackground=self.colors["accent"], highlightthickness=1)
            sync_warn_box.pack(pady=6)
            tk.Label(sync_warn_box, text="⚠️ Aucun dépôt synchronisé — Données locales vierges",
                     font=("Segoe UI", 9, "bold"), fg=self.colors["accent"], bg=self.colors["bg_input"]).pack(side=tk.LEFT, padx=(0, 8))
            tk.Button(sync_warn_box, text="⚡ Configurer / Synchroniser", font=("Segoe UI", 8, "bold"),
                      bg=self.colors["accent"], fg="#ffffff", relief="flat", padx=8, pady=2, cursor="hand2",
                      command=lambda: (self.select_section("coreos"), self.select_tab("sync"))).pack(side=tk.LEFT)

        btn_box = tk.Frame(hero_inner, bg=self.colors["bg_card"])
        btn_box.pack(pady=8)

        btn_p1 = tk.Button(btn_box, text="📦 Éditeur WebUI", font=("Segoe UI", 9, "bold"),
                           bg=self.colors["accent"], fg="#ffffff", relief="flat", padx=16, pady=6, cursor="hand2",
                           command=lambda: self.select_section("webui"))
        btn_p1.pack(side=tk.LEFT, padx=6)

        btn_p2 = tk.Button(btn_box, text="📋 Gérer les Flux CoreOS", font=("Segoe UI", 9),
                           bg=self.colors["bg_input"], fg=self.colors["text_main"], relief="flat", padx=16, pady=6, cursor="hand2",
                           command=lambda: self.select_section("coreos"))
        btn_p2.pack(side=tk.LEFT, padx=6)

        # 4 Stat Cards displaying REAL counts exclusively
        stats_frame = tk.Frame(self.content_frame, bg=self.colors["bg_main"])
        stats_frame.pack(fill=tk.X, pady=(0, 15))

        metrics = [
            (str(total_payload_items), f"{payloads_files} fichier(s)", "Payloads", "🧊", self.colors["accent"]),
            (str(total_pkg_items), f"{pkg_files} fichier(s)", "PKGs", "📦", self.colors["accent"]),
            (str(total_ffpfsc_items), f"{ffpfsc_files} fichier(s)", "FFPFSC", "⚡", self.colors["accent"]),
            (str(total_apps_items), f"{apps_files} fichier(s)", "Apps", "🌐", self.colors["accent"])
        ]

        for i, (main_stat, sub_stat, label, icon, color) in enumerate(metrics):
            card = tk.Frame(stats_frame, bg=self.colors["bg_card"], highlightbackground=self.colors["border"], highlightthickness=1)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4 if i > 0 else 0)

            c_inner = tk.Frame(card, bg=self.colors["bg_card"])
            c_inner.pack(padx=15, pady=15, fill=tk.BOTH)

            lbl_icon = tk.Label(c_inner, text=icon, font=("Segoe UI", 20), fg=color, bg=self.colors["bg_card"])
            lbl_icon.pack(side=tk.LEFT, padx=(0, 12))

            t_box = tk.Frame(c_inner, bg=self.colors["bg_card"])
            t_box.pack(side=tk.LEFT)

            lbl_val = tk.Label(t_box, text=main_stat, font=("Segoe UI", 16, "bold"), fg=self.colors["text_main"], bg=self.colors["bg_card"])
            lbl_val.pack(anchor="w")

            lbl_subt = tk.Label(t_box, text=f"{label} ({sub_stat})", font=("Segoe UI", 9), fg=self.colors["text_muted"], bg=self.colors["bg_card"])
            lbl_subt.pack(anchor="w")

        # Two split panels at the bottom: Sources Actifs & Remerciements
        bottom_frame = tk.Frame(self.content_frame, bg=self.colors["bg_main"])
        bottom_frame.pack(fill=tk.BOTH, expand=True)

        # Panel 1: Dépôts Sources Actifs
        p1 = tk.Frame(bottom_frame, bg=self.colors["bg_card"], highlightbackground=self.colors["border"], highlightthickness=1)
        p1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        p1_inner = tk.Frame(p1, bg=self.colors["bg_card"])
        p1_inner.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        lbl_p1_title = tk.Label(p1_inner, text="📁 Dépôts Sources Actifs", font=("Segoe UI", 11, "bold"),
                                fg=self.colors["text_main"], bg=self.colors["bg_card"])
        lbl_p1_title.pack(anchor="w", pady=(0, 10))

        lbl_c_repo = tk.Label(p1_inner, text="Dépôt CoreOS :", font=("Segoe UI", 9, "bold"),
                              fg=self.colors["accent"], bg=self.colors["bg_card"])
        lbl_c_repo.pack(anchor="w")

        coreos_val = self.config.get('coreosRepo') or 'Non configuré'
        lbl_c_val = tk.Label(p1_inner, text=f"• {coreos_val}", font=("Consolas", 9),
                             fg=self.colors["text_main"] if self.config.get('coreosRepo') else self.colors["text_muted"],
                             bg=self.colors["bg_input"], padx=6, pady=3)
        lbl_c_val.pack(anchor="w", fill=tk.X, pady=(2, 6))

        lbl_w_repo = tk.Label(p1_inner, text="Dépôt WebUI :", font=("Segoe UI", 9, "bold"),
                              fg=self.colors["accent_purple"], bg=self.colors["bg_card"])
        lbl_w_repo.pack(anchor="w")

        webui_val = self.config.get('webuiRepo') or 'Non configuré'
        lbl_w_val = tk.Label(p1_inner, text=f"• {webui_val}", font=("Consolas", 9),
                             fg=self.colors["text_main"] if self.config.get('webuiRepo') else self.colors["text_muted"],
                             bg=self.colors["bg_input"], padx=6, pady=3)
        lbl_w_val.pack(anchor="w", fill=tk.X, pady=(2, 6))

        lbl_p_src = tk.Label(p1_inner, text="Source PLDMGR :", font=("Segoe UI", 9, "bold"),
                              fg=self.colors["text_muted"], bg=self.colors["bg_card"])
        lbl_p_src.pack(anchor="w")

        src_url = self.webui_config.get("sources", {}).get("pldmgr", "")
        lbl_p_val = tk.Label(p1_inner, text=src_url or "Non configurée (attente config.json)", font=("Consolas", 8),
                             fg=self.colors["text_main"] if src_url else self.colors["text_muted"],
                             bg=self.colors["bg_input"], padx=6, pady=4)
        lbl_p_val.pack(anchor="w", fill=tk.X, pady=(2, 6))

        # Panel 2: Remerciements & Crédits
        p2 = tk.Frame(bottom_frame, bg=self.colors["bg_card"], highlightbackground=self.colors["border"], highlightthickness=1)
        p2.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        p2_inner = tk.Frame(p2, bg=self.colors["bg_card"])
        p2_inner.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        lbl_p2_title = tk.Label(p2_inner, text="❤️ Remerciements & Crédits", font=("Segoe UI", 11, "bold"),
                                fg=self.colors["text_main"], bg=self.colors["bg_card"])
        lbl_p2_title.pack(anchor="w", pady=(0, 10))

        credits_list = self.webui_config.get("credits", [])
        if credits_list:
            for c in credits_list:
                lbl_c = tk.Label(p2_inner, text=f"✔ {c}", font=("Segoe UI", 9),
                                 fg=self.colors["text_muted"], bg=self.colors["bg_card"])
                lbl_c.pack(anchor="w", pady=1)
        else:
            lbl_empty_cred = tk.Label(p2_inner, text="Aucun crédit (aucun fichier config.json chargé)",
                                      font=("Segoe UI", 9, "italic"), fg=self.colors["text_muted"], bg=self.colors["bg_card"])
            lbl_empty_cred.pack(anchor="w", pady=6)

    # ==========================================
    # VUE 2: GESTIONNAIRE OPML (/feed/)
    # ==========================================
    def show_opml_view(self):
        if not self.is_ready_to_edit():
            self.show_repos_required_view(redirect_section="coreos", redirect_action=self.show_opml_view)
            return

        top_bar = tk.Frame(self.content_frame, bg=self.colors["bg_main"])
        top_bar.pack(fill=tk.X, pady=(0, 10))

        lbl_title = tk.Label(top_bar, text="Gestionnaire des Flux OPML (/feed/)",
                             font=("Segoe UI", 14, "bold"), fg=self.colors["text_main"], bg=self.colors["bg_main"])
        lbl_title.pack(side=tk.LEFT)

        btn_add_file = tk.Button(top_bar, text="➕ Nouveau Fichier OPML", font=("Segoe UI", 9, "bold"),
                                 bg=self.colors["accent"], fg="#ffffff", relief="flat", padx=10, pady=4, cursor="hand2",
                                 command=self.dialog_new_opml)
        btn_add_file.pack(side=tk.RIGHT, padx=5)

        btn_add_outline = tk.Button(top_bar, text="➕ Ajouter un Outline", font=("Segoe UI", 9),
                                    bg=self.colors["bg_input"], fg=self.colors["text_main"], relief="flat",
                                    padx=10, pady=4, cursor="hand2", command=self.dialog_add_outline)
        btn_add_outline.pack(side=tk.RIGHT, padx=5)

        # Categories selector (apps, payloads, ffpfsc, pkg)
        cat_bar = tk.Frame(self.content_frame, bg=self.colors["bg_card"], height=42)
        cat_bar.pack(fill=tk.X, pady=(0, 10))

        self.cat_buttons = {}
        for cat in ["payloads", "apps", "pkg", "ffpfsc"]:
            count = len(self.feed_data.get(cat, []))
            btn = tk.Button(cat_bar, text=f"{cat.upper()} ({count})", font=("Segoe UI", 9, "bold"),
                            relief="flat", padx=15, pady=8,
                            bg=self.colors["accent"] if cat == self.active_category else self.colors["bg_card"],
                            fg="#ffffff" if cat == self.active_category else self.colors["text_muted"],
                            command=lambda c=cat: self.select_opml_category(c))
            btn.pack(side=tk.LEFT, padx=2)
            self.cat_buttons[cat] = btn

        # Main splitter: Left = files list, Right = outline editor & details
        split_frame = tk.Frame(self.content_frame, bg=self.colors["bg_main"])
        split_frame.pack(fill=tk.BOTH, expand=True)

        # Left: Files in selected category
        left_box = tk.Frame(split_frame, bg=self.colors["bg_card"], width=280, highlightbackground=self.colors["border"], highlightthickness=1)
        left_box.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_box.pack_propagate(False)

        lbl_files = tk.Label(left_box, text="Fichiers OPML disponibles", font=("Segoe UI", 9, "bold"),
                             fg=self.colors["text_muted"], bg=self.colors["bg_card"])
        lbl_files.pack(anchor="w", padx=10, pady=(8, 4))

        self.files_listbox = tk.Listbox(left_box, bg=self.colors["bg_input"], fg=self.colors["text_main"],
                                        selectbackground=self.colors["accent"], selectforeground="#ffffff",
                                        relief="flat", borderwidth=0, font=("Segoe UI", 9))
        self.files_listbox.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 4))
        self.files_listbox.bind("<<ListboxSelect>>", self.on_opml_file_selected)
        self.files_listbox.bind("<Delete>", lambda e: self.delete_opml_file())

        # File actions bar (Rename & Delete list)
        file_actions = tk.Frame(left_box, bg=self.colors["bg_card"])
        file_actions.pack(fill=tk.X, padx=8, pady=(0, 8))

        btn_ren_file = tk.Button(file_actions, text="✏️ Renommer", font=("Segoe UI", 8, "bold"),
                                 bg=self.colors["bg_input"], fg=self.colors["text_main"], relief="flat",
                                 padx=6, pady=4, cursor="hand2", command=self.dialog_rename_opml_file)
        btn_ren_file.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        btn_del_file = tk.Button(file_actions, text="🗑️ Supprimer", font=("Segoe UI", 8, "bold"),
                                 bg=self.colors["bg_input"], fg=self.colors["accent"], relief="flat",
                                 padx=6, pady=4, cursor="hand2", command=self.delete_opml_file)
        btn_del_file.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # Context menu for files listbox
        list_ctx = tk.Menu(self.root, tearoff=0, bg=self.colors["bg_card"], fg=self.colors["text_main"],
                           activebackground=self.colors["accent"], activeforeground="#ffffff", relief="flat")
        list_ctx.add_command(label="✏️ Renommer la liste OPML", command=self.dialog_rename_opml_file)
        list_ctx.add_command(label="🗑️ Supprimer la liste OPML", command=self.delete_opml_file)
        list_ctx.add_separator()
        list_ctx.add_command(label="➕ Nouvelle liste OPML", command=self.dialog_new_opml)

        def show_list_ctx(event):
            try:
                idx = self.files_listbox.nearest(event.y)
                if idx >= 0:
                    self.files_listbox.selection_clear(0, tk.END)
                    self.files_listbox.selection_set(idx)
                    self.on_opml_file_selected(None)
                list_ctx.tk_popup(event.x_root, event.y_root)
            finally:
                list_ctx.grab_release()

        self.files_listbox.bind("<Button-3>", show_list_ctx)

        # Right: Outlines table
        right_box = tk.Frame(split_frame, bg=self.colors["bg_card"], highlightbackground=self.colors["border"], highlightthickness=1)
        right_box.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Quick Search & Outline action buttons
        outline_bar = tk.Frame(right_box, bg=self.colors["bg_card"])
        outline_bar.pack(fill=tk.X, padx=10, pady=(8, 4))

        tk.Label(outline_bar, text="🔍 Filtrer :", font=("Segoe UI", 9, "bold"),
                 fg=self.colors["text_muted"], bg=self.colors["bg_card"]).pack(side=tk.LEFT)

        self.opml_search_var = tk.StringVar()
        self.opml_search_var.trace_add("write", lambda *args: self.refresh_outlines_tree())
        search_entry = tk.Entry(outline_bar, textvariable=self.opml_search_var, bg=self.colors["bg_input"],
                                fg=self.colors["text_main"], insertbackground="#ffffff", relief="flat", font=("Segoe UI", 9))
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 10))

        btn_tree_add = tk.Button(outline_bar, text="➕ Ajouter", font=("Segoe UI", 8, "bold"),
                                 bg=self.colors["accent"], fg="#ffffff", relief="flat", padx=10, pady=4, cursor="hand2",
                                 command=self.dialog_add_outline)
        btn_tree_add.pack(side=tk.LEFT, padx=(0, 4))

        btn_tree_edit = tk.Button(outline_bar, text="✏️ Éditer", font=("Segoe UI", 8),
                                  bg=self.colors["bg_input"], fg=self.colors["text_main"], relief="flat", padx=10, pady=4, cursor="hand2",
                                  command=self.dialog_edit_outline)
        btn_tree_edit.pack(side=tk.LEFT, padx=(0, 4))

        btn_tree_del = tk.Button(outline_bar, text="🗑️ Supprimer", font=("Segoe UI", 8),
                                 bg=self.colors["bg_input"], fg=self.colors["accent"], relief="flat", padx=10, pady=4, cursor="hand2",
                                 command=self.delete_outline)
        btn_tree_del.pack(side=tk.LEFT)

        # Table of outlines
        columns = ("title", "author", "xmlUrl", "description")
        self.outlines_tree = ttk.Treeview(right_box, columns=columns, show="headings", selectmode="browse")
        self.outlines_tree.heading("title", text="Titre / Nom")
        self.outlines_tree.heading("author", text="Auteur")
        self.outlines_tree.heading("xmlUrl", text="URL Dépôt / Fichier")
        self.outlines_tree.heading("description", text="Description")

        self.outlines_tree.column("title", width=150)
        self.outlines_tree.column("author", width=110)
        self.outlines_tree.column("xmlUrl", width=220)
        self.outlines_tree.column("description", width=250)

        tree_scroll = ttk.Scrollbar(right_box, orient=tk.VERTICAL, command=self.outlines_tree.yview)
        self.outlines_tree.configure(yscrollcommand=tree_scroll.set)

        self.outlines_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=(4, 10))
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Bindings for outlines tree
        self.outlines_tree.bind("<Double-Button-1>", lambda e: self.dialog_edit_outline())
        self.outlines_tree.bind("<Delete>", lambda e: self.delete_outline())

        # Context menu for outlines tree
        tree_ctx = tk.Menu(self.root, tearoff=0, bg=self.colors["bg_card"], fg=self.colors["text_main"],
                           activebackground=self.colors["accent"], activeforeground="#ffffff", relief="flat")
        tree_ctx.add_command(label="✏️ Modifier cet élément", command=self.dialog_edit_outline)
        tree_ctx.add_command(label="🗑️ Supprimer cet élément", command=self.delete_outline)
        tree_ctx.add_separator()
        tree_ctx.add_command(label="➕ Ajouter un élément (Outline)", command=self.dialog_add_outline)

        def show_tree_ctx(event):
            row_id = self.outlines_tree.identify_row(event.y)
            if row_id:
                self.outlines_tree.selection_set(row_id)
            try:
                tree_ctx.tk_popup(event.x_root, event.y_root)
            finally:
                tree_ctx.grab_release()

        self.outlines_tree.bind("<Button-3>", show_tree_ctx)

        self.refresh_opml_files_list()

    def select_opml_category(self, cat):
        self.active_category = cat
        for c, btn in self.cat_buttons.items():
            if c == cat:
                btn.configure(bg=self.colors["accent"], fg="#ffffff")
            else:
                btn.configure(bg=self.colors["bg_card"], fg=self.colors["text_muted"])
        self.refresh_opml_files_list()

    def refresh_opml_files_list(self):
        self.files_listbox.delete(0, tk.END)
        files = self.feed_data.get(self.active_category, [])
        for f in files:
            self.files_listbox.insert(tk.END, f["name"])
        if files:
            self.files_listbox.select_set(0)
            self.active_file = files[0]
            self.refresh_outlines_tree()
        else:
            self.active_file = None
            for row in self.outlines_tree.get_children():
                self.outlines_tree.delete(row)

    def on_opml_file_selected(self, event):
        selection = self.files_listbox.curselection()
        if selection:
            idx = selection[0]
            files = self.feed_data.get(self.active_category, [])
            if idx < len(files):
                self.active_file = files[idx]
                self.refresh_outlines_tree()

    def refresh_outlines_tree(self):
        for row in self.outlines_tree.get_children():
            self.outlines_tree.delete(row)
        if not self.active_file:
            return
        query = getattr(self, "opml_search_var", None)
        q = query.get().strip().lower() if query else ""
        for item in self.active_file.get("outlines", []):
            title = str(item.get("title", item.get("text", "")))
            author = str(item.get("author", ""))
            xmlUrl = str(item.get("xmlUrl", ""))
            desc = str(item.get("description", ""))
            if not q or (q in title.lower() or q in author.lower() or q in xmlUrl.lower() or q in desc.lower()):
                self.outlines_tree.insert("", tk.END, values=(title, author, xmlUrl, desc))

    def delete_opml_file(self):
        if not self.active_file:
            messagebox.showwarning("Attention", "Veuillez sélectionner un fichier OPML à supprimer.")
            return

        file_to_delete = self.active_file
        fname = file_to_delete.get("name", "")
        cat = self.active_category

        confirm = messagebox.askyesno(
            "Supprimer la liste OPML",
            f"Êtes-vous sûr de vouloir supprimer définitivement la liste OPML '{fname}' (/feed/{cat}/) ?\n\n"
            "Cette action supprimera également le fichier sur le disque local."
        )
        if not confirm:
            return

        coreos_repo = self.clean_repo_name(self.config.get("coreosRepo", ""))
        possible_paths = []
        if file_to_delete.get("filePath"):
            possible_paths.append(file_to_delete["filePath"])
        if coreos_repo:
            dest_dir = self.get_repo_dir(coreos_repo)
            possible_paths.append(os.path.join(dest_dir, "feed", cat, fname))
            coreos_short = self.get_repo_short_name(coreos_repo)
            possible_paths.append(os.path.join(self.config["workspaceDir"], coreos_short, "feed", cat, fname))
        possible_paths.append(os.path.join(self.config["workspaceDir"], "feed", cat, fname))

        for p in set(possible_paths):
            if os.path.isfile(p):
                try:
                    os.remove(p)
                except Exception as ed:
                    self.log(f"Erreur suppression disque {p}: {ed}", "WARN")

        cat_files = self.feed_data.get(cat, [])
        self.feed_data[cat] = [f for f in cat_files if f.get("name") != fname]

        if hasattr(self, "cat_buttons") and cat in self.cat_buttons:
            self.cat_buttons[cat].configure(text=f"{cat.upper()} ({len(self.feed_data[cat])})")

        self.active_file = None
        self.refresh_opml_files_list()
        self.log(f"Liste OPML '{fname}' supprimée avec succès.", "SUCCESS")
        messagebox.showinfo("Fichier Supprimé", f"La liste OPML '{fname}' a été supprimée avec succès.")

    def dialog_rename_opml_file(self):
        if not self.active_file:
            messagebox.showwarning("Attention", "Veuillez sélectionner un fichier OPML à renommer.")
            return

        file_to_rename = self.active_file
        old_name = file_to_rename.get("name", "")
        cat = self.active_category

        win = tk.Toplevel(self.root)
        win.title(f"Renommer {old_name}")
        win.geometry("460x200")
        win.configure(bg=self.colors["bg_main"])
        win.transient(self.root)

        tk.Label(win, text=f"Nouveau nom de fichier (/feed/{cat}/) :",
                 font=("Segoe UI", 10, "bold"), fg=self.colors["text_main"], bg=self.colors["bg_main"]).pack(pady=(20, 5), padx=25, anchor="w")

        ent = tk.Entry(win, font=("Segoe UI", 10), bg=self.colors["bg_input"], fg=self.colors["text_main"],
                       insertbackground="#ffffff", relief="flat")
        ent.insert(0, old_name)
        ent.pack(fill=tk.X, padx=25, pady=(0, 15))
        ent.focus_set()
        ent.select_range(0, tk.END)

        def do_rename():
            new_name = ent.get().strip()
            if not new_name:
                messagebox.showwarning("Attention", "Le nom du fichier ne peut pas être vide.")
                return
            if not new_name.endswith(".opml"):
                new_name += ".opml"
            if new_name == old_name:
                win.destroy()
                return

            existing = [f["name"] for f in self.feed_data.get(cat, []) if f["name"] != old_name]
            if new_name in existing:
                messagebox.showerror("Erreur", f"Un fichier nommé '{new_name}' existe déjà dans /feed/{cat}/.")
                return

            old_path = file_to_rename.get("filePath", "")
            if old_path and os.path.isfile(old_path):
                new_path = os.path.join(os.path.dirname(old_path), new_name)
                try:
                    os.rename(old_path, new_path)
                    file_to_rename["filePath"] = new_path
                except Exception as e:
                    self.log(f"Erreur renommage sur disque: {e}", "WARN")

            file_to_rename["name"] = new_name
            file_to_rename["title"] = new_name.replace(".opml", "")
            self.save_opml_file_to_disk(file_to_rename)

            self.refresh_opml_files_list()
            self.log(f"Fichier OPML renommé : '{old_name}' -> '{new_name}'", "SUCCESS")
            win.destroy()

        btn_row = tk.Frame(win, bg=self.colors["bg_main"])
        btn_row.pack(fill=tk.X, padx=25)
        tk.Button(btn_row, text="💾 Enregistrer", font=("Segoe UI", 9, "bold"),
                  bg=self.colors["accent"], fg="#ffffff", relief="flat", padx=15, pady=6, cursor="hand2",
                  command=do_rename).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(btn_row, text="Annuler", font=("Segoe UI", 9),
                  bg=self.colors["bg_input"], fg=self.colors["text_main"], relief="flat", padx=15, pady=6, cursor="hand2",
                  command=win.destroy).pack(side=tk.LEFT)

    def dialog_new_opml(self):
        win = tk.Toplevel(self.root)
        win.title("Créer un nouveau fichier OPML")
        win.geometry("450x220")
        win.configure(bg=self.colors["bg_main"])
        win.transient(self.root)

        lbl = tk.Label(win, text=f"Nouveau fichier dans /feed/{self.active_category}/",
                       font=("Segoe UI", 10, "bold"), fg=self.colors["text_main"], bg=self.colors["bg_main"])
        lbl.pack(pady=(15, 10))

        entry_name = tk.Entry(win, font=("Segoe UI", 10), bg=self.colors["bg_input"], fg=self.colors["text_main"], relief="flat")
        entry_name.insert(0, f"{self.active_category}_feed.opml")
        entry_name.pack(fill=tk.X, padx=25, pady=5)
        entry_name.focus_set()

        def save_new():
            name = entry_name.get().strip()
            if not name:
                name = f"{self.active_category}_feed.opml"
            if not name.endswith(".opml"):
                name += ".opml"
            new_file_data = {
                "name": name,
                "category": self.active_category,
                "title": name.replace(".opml", ""),
                "outlines": []
            }
            self.feed_data[self.active_category].append(new_file_data)
            self.save_opml_file_to_disk(new_file_data)
            if hasattr(self, "cat_buttons") and self.active_category in self.cat_buttons:
                self.cat_buttons[self.active_category].configure(text=f"{self.active_category.upper()} ({len(self.feed_data[self.active_category])})")
            self.refresh_opml_files_list()
            self.log(f"Fichier OPML créé : /feed/{self.active_category}/{name}", "SUCCESS")
            win.destroy()

        btn_save = tk.Button(win, text="Créer le fichier OPML", font=("Segoe UI", 9, "bold"),
                             bg=self.colors["accent"], fg="#ffffff", relief="flat", padx=15, pady=6, cursor="hand2", command=save_new)
        btn_save.pack(pady=20)

    def dialog_add_outline(self):
        if not self.active_file:
            messagebox.showwarning("Attention", "Veuillez sélectionner un fichier OPML d'abord.")
            return

        win = tk.Toplevel(self.root)
        win.title(f"Ajouter un Outline dans {self.active_file['name']}")
        win.geometry("520x430")
        win.configure(bg=self.colors["bg_main"])
        win.transient(self.root)

        fields = [
            ("Titre / Nom : *", "title"),
            ("Auteur :", "author"),
            ("URL Git / Release : *", "xmlUrl"),
            ("Description :", "description"),
        ]

        entries = {}
        for label_text, key in fields:
            lbl = tk.Label(win, text=label_text, font=("Segoe UI", 9, "bold"),
                           fg=self.colors["text_main"], bg=self.colors["bg_main"])
            lbl.pack(anchor="w", padx=25, pady=(8, 2))

            ent = tk.Entry(win, font=("Segoe UI", 10), bg=self.colors["bg_input"], fg=self.colors["text_main"],
                           insertbackground="#ffffff", relief="flat")
            ent.pack(fill=tk.X, padx=25)
            entries[key] = ent

        entries["title"].focus_set()

        def save_outline():
            title_val = entries["title"].get().strip()
            url_val = entries["xmlUrl"].get().strip()
            if not title_val:
                messagebox.showwarning("Attention", "Le Titre de l'élément est obligatoire.")
                return
            new_outline = {
                "text": title_val,
                "title": title_val,
                "type": "rss",
                "xmlUrl": url_val,
                "author": entries["author"].get().strip(),
                "description": entries["description"].get().strip()
            }
            self.active_file["outlines"].append(new_outline)
            self.save_opml_file_to_disk(self.active_file)
            self.refresh_outlines_tree()
            self.log(f"Élément ajouté à {self.active_file['name']} : {new_outline['title']}", "SUCCESS")
            win.destroy()

        btn_row = tk.Frame(win, bg=self.colors["bg_main"])
        btn_row.pack(fill=tk.X, padx=25, pady=20)

        btn_save = tk.Button(btn_row, text="💾 Enregistrer l'Outline", font=("Segoe UI", 9, "bold"),
                             bg=self.colors["accent"], fg="#ffffff", relief="flat", padx=15, pady=6, cursor="hand2", command=save_outline)
        btn_save.pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(btn_row, text="Annuler", font=("Segoe UI", 9),
                  bg=self.colors["bg_input"], fg=self.colors["text_main"], relief="flat", padx=15, pady=6, cursor="hand2",
                  command=win.destroy).pack(side=tk.LEFT)

    def dialog_edit_outline(self):
        if not self.active_file:
            messagebox.showwarning("Attention", "Veuillez sélectionner un fichier OPML d'abord.")
            return

        selected = self.outlines_tree.selection()
        if not selected:
            messagebox.showwarning("Attention", "Veuillez sélectionner un élément (outline) dans le tableau à modifier.")
            return

        item_id = selected[0]
        item_vals = self.outlines_tree.item(item_id, "values")
        if not item_vals:
            return

        cur_title, cur_author, cur_url, cur_desc = item_vals
        matched_idx = None
        for idx, it in enumerate(self.active_file.get("outlines", [])):
            t = str(it.get("title", it.get("text", "")))
            u = str(it.get("xmlUrl", ""))
            if t == cur_title and u == cur_url:
                matched_idx = idx
                break

        if matched_idx is None:
            for idx, it in enumerate(self.active_file.get("outlines", [])):
                if str(it.get("title", it.get("text", ""))) == cur_title:
                    matched_idx = idx
                    break

        if matched_idx is None:
            messagebox.showerror("Erreur", "Impossible de retrouver l'élément dans le fichier sélectionné.")
            return

        target_outline = self.active_file["outlines"][matched_idx]

        win = tk.Toplevel(self.root)
        win.title(f"Modifier l'Outline : {cur_title}")
        win.geometry("520x430")
        win.configure(bg=self.colors["bg_main"])
        win.transient(self.root)

        fields = [
            ("Titre / Nom : *", "title", target_outline.get("title", target_outline.get("text", ""))),
            ("Auteur :", "author", target_outline.get("author", "")),
            ("URL Git / Release :", "xmlUrl", target_outline.get("xmlUrl", "")),
            ("Description :", "description", target_outline.get("description", ""))
        ]

        entries = {}
        for label_text, key, val in fields:
            lbl = tk.Label(win, text=label_text, font=("Segoe UI", 9, "bold"),
                           fg=self.colors["text_main"], bg=self.colors["bg_main"])
            lbl.pack(anchor="w", padx=25, pady=(8, 2))

            ent = tk.Entry(win, font=("Segoe UI", 10), bg=self.colors["bg_input"], fg=self.colors["text_main"],
                           insertbackground="#ffffff", relief="flat")
            ent.insert(0, val)
            ent.pack(fill=tk.X, padx=25)
            entries[key] = ent

        entries["title"].focus_set()

        def save_changes():
            new_title = entries["title"].get().strip()
            if not new_title:
                messagebox.showwarning("Attention", "Le titre ne peut pas être vide.")
                return
            target_outline["title"] = new_title
            target_outline["text"] = new_title
            target_outline["author"] = entries["author"].get().strip()
            target_outline["xmlUrl"] = entries["xmlUrl"].get().strip()
            target_outline["description"] = entries["description"].get().strip()

            self.save_opml_file_to_disk(self.active_file)
            self.refresh_outlines_tree()
            self.log(f"Élément modifié dans {self.active_file['name']} : {new_title}", "SUCCESS")
            win.destroy()

        btn_row = tk.Frame(win, bg=self.colors["bg_main"])
        btn_row.pack(fill=tk.X, padx=25, pady=20)

        tk.Button(btn_row, text="💾 Enregistrer les Modifications", font=("Segoe UI", 9, "bold"),
                  bg=self.colors["accent"], fg="#ffffff", relief="flat", padx=15, pady=6, cursor="hand2",
                  command=save_changes).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(btn_row, text="Annuler", font=("Segoe UI", 9),
                  bg=self.colors["bg_input"], fg=self.colors["text_main"], relief="flat", padx=15, pady=6, cursor="hand2",
                  command=win.destroy).pack(side=tk.LEFT)

    def delete_outline(self):
        if not self.active_file:
            messagebox.showwarning("Attention", "Veuillez sélectionner un fichier OPML d'abord.")
            return

        selected = self.outlines_tree.selection()
        if not selected:
            messagebox.showwarning("Attention", "Veuillez sélectionner un élément (outline) à supprimer dans le tableau.")
            return

        item_id = selected[0]
        item_vals = self.outlines_tree.item(item_id, "values")
        if not item_vals:
            return

        cur_title, cur_author, cur_url, cur_desc = item_vals
        confirm = messagebox.askyesno(
            "Supprimer l'élément",
            f"Voulez-vous vraiment supprimer l'élément '{cur_title}' du fichier '{self.active_file['name']}' ?"
        )
        if not confirm:
            return

        matched_idx = None
        for idx, it in enumerate(self.active_file.get("outlines", [])):
            t = str(it.get("title", it.get("text", "")))
            u = str(it.get("xmlUrl", ""))
            if t == cur_title and u == cur_url:
                matched_idx = idx
                break

        if matched_idx is None:
            for idx, it in enumerate(self.active_file.get("outlines", [])):
                if str(it.get("title", it.get("text", ""))) == cur_title:
                    matched_idx = idx
                    break

        if matched_idx is not None:
            removed = self.active_file["outlines"].pop(matched_idx)
            self.save_opml_file_to_disk(self.active_file)
            self.refresh_outlines_tree()
            self.log(f"Élément '{removed.get('title')}' supprimé de {self.active_file['name']}.", "SUCCESS")

    # ==========================================
    # VUE 3: ÉDITEUR CONFIG JSON (/web/data/config.json)
    # ==========================================
    def show_webui_view(self, category="general"):
        self.show_webui_subview(category)

    def show_webui_subview(self, category="general"):
        if not self.is_ready_to_edit():
            self.show_repos_required_view(redirect_section="webui", redirect_action=lambda: self.show_webui_subview(category))
            return

        self.active_webui_category = category
        self.clear_content_frame()

        cat_labels = {
            "general": ("🌐", "Général & GitHub", "Titre du site, utilisateur GitHub et dépôts associés."),
            "sources": ("🗄️", "Sources & Catalogues", "Configuration des flux pldmgr et catalogues JSON distants."),
            "webkit": ("🧭", "WebKit Exploits", "Liste des hôtes d'exploits WebKit PS5 pris en charge."),
            "services": ("🖥️", "Services PS5", "Services WebUI locaux (Payload Manager, Pegasus, etc.)."),
            "creators": ("📺", "Créateurs YouTube", "Créateurs de contenu reconnus de la scène PS5."),
            "packs": ("📦", "Packs AIO & Releases", "Archives tout-en-un et packs de déploiement."),
            "credits": ("❤️", "Crédits & Remerciements", "Remerciements aux développeurs et contributeurs de la scène."),
            "socials": ("🔗", "Réseaux Sociaux", "Liens communautaires, profils officiels et serveurs."),
            "raw": ("📝", "Éditeur Brut JSON", "Édition directe et validation de la structure du fichier config.json."),
        }

        icon_str, title_str, desc_str = cat_labels.get(category, ("🌐", "Configuration WebUI", ""))

        # Top Banner sans les onglets en doublon
        top_banner = tk.Frame(self.content_frame, bg=self.colors["bg_card"], padx=20, pady=15,
                              highlightbackground=self.colors["border"], highlightthickness=1)
        top_banner.pack(fill=tk.X, pady=(0, 15))

        top_left = tk.Frame(top_banner, bg=self.colors["bg_card"])
        top_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(top_left, text="GESTIONNAIRE EVOX-COREOS-WEBUI",
                 font=("Segoe UI", 8, "bold"), fg="#c084fc", bg=self.colors["bg_card"]).pack(anchor="w")

        tk.Label(top_left, text="Configuration du Site (/web/data/config.json)",
                 font=("Segoe UI", 15, "bold"), fg=self.colors["text_main"], bg=self.colors["bg_card"]).pack(anchor="w", pady=(2, 0))

        tk.Label(top_left, text="Édition dynamique par catégories associées à chaque menu de l'interface WebUI.",
                 font=("Segoe UI", 9), fg=self.colors["text_muted"], bg=self.colors["bg_card"]).pack(anchor="w", pady=(2, 6))

        # Indicateur de la catégorie active (remplace la barre de boutons en doublon)
        badge_box = tk.Frame(top_left, bg=self.colors["bg_input"], padx=10, pady=4,
                             highlightbackground=self.colors["border"], highlightthickness=1)
        badge_box.pack(anchor="w")

        tk.Label(badge_box, text="Catégorie active :", font=("Segoe UI", 8),
                 fg=self.colors["text_muted"], bg=self.colors["bg_input"]).pack(side=tk.LEFT, padx=(0, 6))

        tk.Label(badge_box, text=f"{icon_str}  {title_str}", font=("Segoe UI", 9, "bold"),
                 fg="#c084fc", bg=self.colors["bg_input"]).pack(side=tk.LEFT)

        # Bouton d'enregistrement en haut à droite
        btn_save = tk.Button(top_banner, text="💾 Enregistrer config.json", font=("Segoe UI", 9, "bold"),
                             bg=self.colors["accent"], fg="#ffffff", activebackground=self.colors["accent_hover"],
                             activeforeground="#ffffff", relief="flat", padx=16, pady=8, cursor="hand2",
                             command=self.save_webui_config_to_disk)
        btn_save.pack(side=tk.RIGHT, padx=5)

        # Corps de la catégorie sélectionnée
        body_frame = tk.Frame(self.content_frame, bg=self.colors["bg_card"],
                              highlightbackground=self.colors["border"], highlightthickness=1)
        body_frame.pack(fill=tk.BOTH, expand=True)

        if category == "general":
            self.build_config_general_tab(body_frame)
        elif category == "sources":
            self.build_config_sources_tab(body_frame)
        elif category == "webkit":
            self.build_config_webkit_tab(body_frame)
        elif category == "services":
            self.build_config_services_tab(body_frame)
        elif category == "creators":
            self.build_config_creators_tab(body_frame)
        elif category == "packs":
            self.build_config_packs_tab(body_frame)
        elif category == "credits":
            self.build_config_credits_tab(body_frame)
        elif category == "socials":
            self.build_config_socials_tab(body_frame)
        elif category == "raw":
            self.build_config_raw_tab(body_frame)

    def build_config_general_tab(self, parent):
        build_config_general_tab(self, parent)

    def build_config_webkit_tab(self, parent):
        build_config_webkit_tab(self, parent)

    def build_config_services_tab(self, parent):
        build_config_services_tab(self, parent)

    def build_config_creators_tab(self, parent):
        build_config_creators_tab(self, parent)

    def build_config_sources_tab(self, parent):
        build_config_sources_tab(self, parent)

    def build_config_packs_tab(self, parent):
        build_config_packs_tab(self, parent)

    def build_config_credits_tab(self, parent):
        build_config_credits_tab(self, parent)

    def build_config_socials_tab(self, parent):
        build_config_socials_tab(self, parent)

    def build_config_raw_tab(self, parent):
        build_config_raw_tab(self, parent)

    def show_python_info_view(self):
        self.clear_content_frame()

        top_banner = tk.Frame(self.content_frame, bg=self.colors["bg_card"], padx=20, pady=16,
                              highlightbackground=self.colors["border"], highlightthickness=1)
        top_banner.pack(fill=tk.X, pady=(0, 15))

        tk.Label(top_banner, text="OUTILS & ENVIRONNEMENT PYTHON",
                 font=("Segoe UI", 8, "bold"), fg=self.colors["accent"], bg=self.colors["bg_card"]).pack(anchor="w")

        tk.Label(top_banner, text="Application Python Tkinter (evox_manager.py)",
                 font=("Segoe UI", 16, "bold"), fg=self.colors["text_main"], bg=self.colors["bg_card"]).pack(anchor="w", pady=(2, 2))

        tk.Label(top_banner, text="Console autonome de bureau pour administrer vos flux OPML et le site WebUI sans navigateur.",
                 font=("Segoe UI", 9), fg=self.colors["text_muted"], bg=self.colors["bg_card"]).pack(anchor="w")

        card = tk.Frame(self.content_frame, bg=self.colors["bg_card"], padx=20, pady=20,
                        highlightbackground=self.colors["border"], highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True)

        specs = [
            ("Fichier exécuté :", os.path.abspath(__file__)),
            ("Version Python :", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} ({sys.platform})"),
            ("Interface Graphique :", "Tkinter / TTK (Moteur Natif Bureau)"),
            ("Dépôt CoreOS :", self.config.get("coreosRepo", "")),
            ("Dépôt WebUI :", self.config.get("webuiRepo", "")),
            ("Dossier Workspace :", self.config.get("workspaceDir", "./")),
            ("Statut de l'application :", "En cours d'exécution (Prêt)"),
        ]

        for label_t, val_t in specs:
            row = tk.Frame(card, bg=self.colors["bg_card"])
            row.pack(fill=tk.X, pady=4)
            tk.Label(row, text=label_t, font=("Segoe UI", 9, "bold"), width=24, anchor="w",
                     fg=self.colors["text_muted"], bg=self.colors["bg_card"]).pack(side=tk.LEFT)
            tk.Label(row, text=val_t, font=("Consolas" if "/" in val_t or "." in val_t else "Segoe UI", 9),
                     fg=self.colors["text_main"], bg=self.colors["bg_card"], anchor="w").pack(side=tk.LEFT)

        btn_bar = tk.Frame(card, bg=self.colors["bg_card"])
        btn_bar.pack(anchor="w", pady=(20, 10))

        def copy_cmd():
            cmd_str = f"python3 {os.path.basename(__file__)}"
            self.root.clipboard_clear()
            self.root.clipboard_append(cmd_str)
            self.log("Commande python3 copiée dans le presse-papier !", "INFO")
            messagebox.showinfo("Copié", f"Commande copiée :\n\n{cmd_str}")

        btn_copy = tk.Button(btn_bar, text="📋 Copier commande de lancement", font=("Segoe UI", 9, "bold"),
                             bg=self.colors["accent"], fg="#ffffff", relief="flat", padx=12, pady=6, cursor="hand2",
                             command=copy_cmd)
        btn_copy.pack(side=tk.LEFT, padx=(0, 10))

        btn_reload = tk.Button(btn_bar, text="🔄 Recharger données locales", font=("Segoe UI", 9),
                               bg=self.colors["bg_input"], fg=self.colors["text_main"], relief="flat", padx=12, pady=6, cursor="hand2",
                               command=lambda: [self.load_local_data(), self.load_pegasus_data(), self.log("Données rafraîchies.", "SUCCESS")])
        btn_reload.pack(side=tk.LEFT, padx=(0, 10))

    @staticmethod
    def _is_real_package(fn: str) -> bool:
        if not fn or not isinstance(fn, str):
            return False
        clean = fn.strip()
        if clean.startswith("http://") or clean.startswith("https://"):
            return False
        lower = clean.lower()
        return lower.endswith(".pkg") or lower.endswith(".ffpfsc")

    @classmethod
    def _extract_real_package(cls, entry: dict):
        if not entry or not isinstance(entry, dict):
            return None

        fname = ""
        fn_prop = entry.get("filename")
        if fn_prop and cls._is_real_package(fn_prop):
            fname = fn_prop.strip()
        elif entry.get("title") and cls._is_real_package(entry.get("title")):
            fname = entry.get("title").strip()
        elif entry.get("name") and cls._is_real_package(entry.get("name")):
            fname = entry.get("name").strip()
        else:
            links = entry.get("downloadLinks")
            raw_url = (links[0].get("url") if isinstance(links, list) and links and isinstance(links[0], dict) else "") or entry.get("url") or ""
            if raw_url and isinstance(raw_url, str):
                base = os.path.basename(raw_url.split("?")[0].strip())
                if cls._is_real_package(base):
                    fname = base

        if not fname or not cls._is_real_package(fname):
            return None

        is_pkg = fname.lower().endswith(".pkg")
        itype = "PKG" if is_pkg else "FFPFSC"

        links = entry.get("downloadLinks")
        url = (links[0].get("url") if isinstance(links, list) and links and isinstance(links[0], dict) else "") or entry.get("url") or ""

        title_id = entry.get("titleId") or entry.get("title_id") or ("CUSA00000" if is_pkg else "FFPFSC001")

        title = entry.get("description") or entry.get("name") or ""
        if not title or cls._is_real_package(title) or title == fname:
            title = re.sub(r"\.(pkg|ffpfsc)$", "", fname, flags=re.I)
            title = re.sub(r"^PS5PKG_", "", title, flags=re.I).replace("_", " ")

        icon = ""
        raw_poster = entry.get("icon") or entry.get("posterUrl") or ""
        if raw_poster and isinstance(raw_poster, str):
            icon = os.path.basename(raw_poster.strip())

        return {
            "type": itype,
            "filename": fname,
            "title_id": title_id,
            "title": title.strip(),
            "url": str(url).strip(),
            "icon": icon.strip()
        }

    # ==========================================
    # VUE 3.5: PEGASUS METADATA & ICON MANAGER
    # Source: evoX-CoreOS/json/pegasus-dl/catalog.json
    # Cible: evoX-CoreOS/assets/icon/pegasus_metadata.json
    # ==========================================
    def load_pegasus_data(self):
        """Charge catalog.json et pegasus_metadata.json (avec fallback pegasus_icons.json)"""
        coreos_repo = self.clean_repo_name(self.config.get("coreosRepo", ""))
        self.pegasus_metadata = {}
        self.pegasus_items_list = []

        if not coreos_repo:
            return

        coreos_dir = self.get_repo_dir(coreos_repo)
        if not coreos_dir:
            return

        self.pegasus_icon_dir = os.path.join(coreos_dir, "assets", "icon")
        self.pegasus_metadata_path = os.path.join(self.pegasus_icon_dir, "pegasus_metadata.json")
        self.pegasus_legacy_path = os.path.join(self.pegasus_icon_dir, "pegasus_icons.json")
        self.pegasus_catalog_path = os.path.join(coreos_dir, "json", "pegasus-dl", "catalog.json")

        if os.path.exists(self.pegasus_metadata_path):
            try:
                with open(self.pegasus_metadata_path, "r", encoding="utf-8") as f:
                    self.pegasus_metadata = json.load(f)
            except Exception as e:
                self.log(f"Erreur chargement métadonnées Pegasus: {e}", "WARN")

        if not self.pegasus_metadata and os.path.exists(self.pegasus_legacy_path):
            try:
                with open(self.pegasus_legacy_path, "r", encoding="utf-8") as f:
                    legacy = json.load(f)
                    for k, v in legacy.items():
                        self.pegasus_metadata[k] = {"titleId": "", "title": "", "icon": str(v)}
            except Exception as e:
                self.log(f"Erreur chargement icônes legacy Pegasus: {e}", "WARN")

        # Charger le catalogue local s'il existe
        if os.path.exists(self.pegasus_catalog_path):
            try:
                with open(self.pegasus_catalog_path, "r", encoding="utf-8") as f:
                    cat_data = json.load(f)
                    raw_list = cat_data if isinstance(cat_data, list) else (cat_data.get("packages", []) if isinstance(cat_data, dict) else [])
                    for entry in raw_list:
                        pkg = self._extract_real_package(entry)
                        if pkg:
                            fn = pkg["filename"]
                            saved = self.pegasus_metadata.get(fn, {})
                            self.pegasus_items_list.append({
                                "type": pkg["type"],
                                "filename": fn,
                                "title_id": saved.get("titleId") or pkg["title_id"],
                                "title": saved.get("title") or pkg["title"],
                                "url": pkg["url"],
                                "icon": saved.get("icon") or pkg["icon"]
                            })
            except Exception as e:
                self.log(f"Erreur lecture catalogue Pegasus: {e}", "WARN")

    def show_pegasus_view(self):
        if not self.is_ready_to_edit():
            self.show_repos_required_view(redirect_section="coreos", redirect_action=self.show_pegasus_view)
            return

        inner = tk.Frame(self.content_frame, bg=self.colors["bg_card"],
                         highlightbackground=self.colors["border"], highlightthickness=1)
        inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header bar
        header_frame = tk.Frame(inner, bg=self.colors["bg_card"])
        header_frame.pack(fill=tk.X, padx=20, pady=(15, 10))

        lbl_title = tk.Label(header_frame, text="🎮 evoX-CoreOS - Pegasus Metadata & Icon Manager",
                             font=("Segoe UI", 13, "bold"), fg=self.colors["text_main"], bg=self.colors["bg_card"])
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(header_frame,
                           text=f"Source: {os.path.relpath(self.pegasus_catalog_path, self.config['workspaceDir'])}  ➔  Cible: {os.path.relpath(self.pegasus_metadata_path, self.config['workspaceDir'])}",
                           font=("Consolas", 8), fg=self.colors["accent"], bg=self.colors["bg_card"])
        lbl_sub.pack(anchor="w", pady=(2, 0))

        # Top Control Frame (Repo URL + Scan + Save)
        top_bar = tk.Frame(inner, bg=self.colors["bg_card"])
        top_bar.pack(fill=tk.X, padx=20, pady=5)

        tk.Label(top_bar, text="GitHub / Source :", font=("Segoe UI", 9, "bold"),
                 fg=self.colors["text_muted"], bg=self.colors["bg_card"]).pack(side=tk.LEFT, padx=(0, 5))

        coreos_repo_cfg = self.clean_repo_name(self.config.get('coreosRepo', ''))
        self.pegasus_repo_var = tk.StringVar(value=f"https://github.com/{coreos_repo_cfg}" if coreos_repo_cfg else "")
        ent_repo = tk.Entry(top_bar, textvariable=self.pegasus_repo_var, font=("Segoe UI", 9),
                            bg=self.colors["bg_input"], fg=self.colors["text_main"],
                            insertbackground="#ffffff", relief="flat", width=38)
        ent_repo.pack(side=tk.LEFT, padx=(0, 8), ipady=3)

        btn_scan = tk.Button(top_bar, text="🚀 Scan Feeds & Catalogue", font=("Segoe UI", 9, "bold"),
                             bg="#8b5cf6", fg="#ffffff", relief="flat", padx=12, pady=4,
                             command=self.scan_pegasus_feeds)
        btn_scan.pack(side=tk.LEFT, padx=3)

        btn_save = tk.Button(top_bar, text="💾 Sauvegarder la Configuration", font=("Segoe UI", 9, "bold"),
                             bg=self.colors["accent"], fg="#ffffff", relief="flat", padx=12, pady=4,
                             command=self.save_pegasus_config)
        btn_save.pack(side=tk.LEFT, padx=3)

        btn_open_folder = tk.Button(top_bar, text="📂 Dossier Icônes", font=("Segoe UI", 8),
                                    bg=self.colors["bg_input"], fg=self.colors["text_main"], relief="flat", padx=8, pady=4,
                                    command=self.open_pegasus_icon_folder)
        btn_open_folder.pack(side=tk.RIGHT, padx=3)

        # Filter & Search Bar
        filter_bar = tk.Frame(inner, bg=self.colors["bg_card"])
        filter_bar.pack(fill=tk.X, padx=20, pady=(10, 5))

        tk.Label(filter_bar, text="Filtre Type :", font=("Segoe UI", 8, "bold"),
                 fg=self.colors["text_muted"], bg=self.colors["bg_card"]).pack(side=tk.LEFT, padx=(0, 5))

        self.pegasus_type_filter = tk.StringVar(value="ALL")
        for t in ["ALL", "PKG", "FFPFSC"]:
            rb = tk.Radiobutton(filter_bar, text=t, value=t, variable=self.pegasus_type_filter,
                                font=("Segoe UI", 8, "bold"), bg=self.colors["bg_card"],
                                fg=self.colors["text_main"], selectcolor=self.colors["bg_input"],
                                activebackground=self.colors["bg_card"],
                                activeforeground=self.colors["accent"],
                                command=self.refresh_pegasus_tree)
            rb.pack(side=tk.LEFT, padx=2)

        tk.Label(filter_bar, text="Rechercher :", font=("Segoe UI", 8, "bold"),
                 fg=self.colors["text_muted"], bg=self.colors["bg_card"]).pack(side=tk.LEFT, padx=(15, 5))

        self.pegasus_search_var = tk.StringVar()
        self.pegasus_search_var.trace_add("write", lambda *args: self.refresh_pegasus_tree())
        ent_search = tk.Entry(filter_bar, textvariable=self.pegasus_search_var, font=("Segoe UI", 9),
                              bg=self.colors["bg_input"], fg=self.colors["text_main"],
                              insertbackground="#ffffff", relief="flat", width=25)
        ent_search.pack(side=tk.LEFT, padx=2, ipady=2)

        self.lbl_pegasus_count = tk.Label(filter_bar, text="", font=("Segoe UI", 8),
                                          fg=self.colors["text_muted"], bg=self.colors["bg_card"])
        self.lbl_pegasus_count.pack(side=tk.RIGHT, padx=5)

        # Center Treeview Frame
        tree_frame = tk.Frame(inner, bg=self.colors["bg_card"])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        columns = ("type", "filename", "title_id", "title", "url", "icon")
        self.pegasus_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        self.pegasus_tree.heading("type", text="Type")
        self.pegasus_tree.heading("filename", text="Nom de fichier (Filename)")
        self.pegasus_tree.heading("title_id", text="Title ID")
        self.pegasus_tree.heading("title", text="Titre (Title)")
        self.pegasus_tree.heading("url", text="URL Source")
        self.pegasus_tree.heading("icon", text="Icône / Poster")

        self.pegasus_tree.column("type", width=70, anchor="center")
        self.pegasus_tree.column("filename", width=200)
        self.pegasus_tree.column("title_id", width=110, anchor="center")
        self.pegasus_tree.column("title", width=220)
        self.pegasus_tree.column("url", width=180)
        self.pegasus_tree.column("icon", width=140)

        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.pegasus_tree.yview)
        self.pegasus_tree.configure(yscrollcommand=vsb.set)
        self.pegasus_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.pegasus_tree.bind("<<TreeviewSelect>>", self.on_pegasus_select)
        self.pegasus_tree.bind("<Double-1>", lambda e: self.apply_pegasus_changes())

        # Bottom Quick Edit Frame
        edit_frame = tk.LabelFrame(inner, text=" Édition des Métadonnées de l'Élément Sélectionné ",
                                   font=("Segoe UI", 9, "bold"), fg=self.colors["text_main"],
                                   bg=self.colors["bg_input"], padx=15, pady=10, relief="solid", borderwidth=1)
        edit_frame.pack(fill=tk.X, padx=20, pady=(5, 15))

        # Row 1: Target File
        r1 = tk.Frame(edit_frame, bg=self.colors["bg_input"])
        r1.pack(fill=tk.X, pady=3)
        tk.Label(r1, text="Fichier Cible :", font=("Segoe UI", 9, "bold"),
                 fg=self.colors["text_muted"], bg=self.colors["bg_input"], width=14, anchor="w").pack(side=tk.LEFT)
        self.lbl_edit_filename = tk.Label(r1, text="(Aucun élément sélectionné)", font=("Consolas", 9, "bold"),
                                          fg=self.colors["accent"], bg=self.colors["bg_input"], anchor="w")
        self.lbl_edit_filename.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Row 2: Title ID + Game Title
        r2 = tk.Frame(edit_frame, bg=self.colors["bg_input"])
        r2.pack(fill=tk.X, pady=3)

        tk.Label(r2, text="Title ID :", font=("Segoe UI", 9, "bold"),
                 fg=self.colors["text_muted"], bg=self.colors["bg_input"], width=14, anchor="w").pack(side=tk.LEFT)
        self.pegasus_edit_title_id = tk.StringVar()
        ent_tid = tk.Entry(r2, textvariable=self.pegasus_edit_title_id, font=("Consolas", 9),
                           bg=self.colors["bg_card"], fg=self.colors["text_main"],
                           insertbackground="#ffffff", relief="flat", width=18)
        ent_tid.pack(side=tk.LEFT, padx=(0, 20), ipady=2)

        tk.Label(r2, text="Titre du Jeu :", font=("Segoe UI", 9, "bold"),
                 fg=self.colors["text_muted"], bg=self.colors["bg_input"], width=12, anchor="w").pack(side=tk.LEFT)
        self.pegasus_edit_title = tk.StringVar()
        ent_title = tk.Entry(r2, textvariable=self.pegasus_edit_title, font=("Segoe UI", 9),
                             bg=self.colors["bg_card"], fg=self.colors["text_main"],
                             insertbackground="#ffffff", relief="flat")
        ent_title.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=2)

        # Row 3: Icon File + Browse + Apply Button
        r3 = tk.Frame(edit_frame, bg=self.colors["bg_input"])
        r3.pack(fill=tk.X, pady=3)

        tk.Label(r3, text="Icône / Poster :", font=("Segoe UI", 9, "bold"),
                 fg=self.colors["text_muted"], bg=self.colors["bg_input"], width=14, anchor="w").pack(side=tk.LEFT)
        self.pegasus_edit_icon = tk.StringVar()
        ent_icon = tk.Entry(r3, textvariable=self.pegasus_edit_icon, font=("Consolas", 9),
                            bg=self.colors["bg_card"], fg=self.colors["text_main"],
                            insertbackground="#ffffff", relief="flat")
        ent_icon.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=2)

        btn_browse_icon = tk.Button(r3, text="📂 Parcourir...", font=("Segoe UI", 8, "bold"),
                                    bg=self.colors["bg_card"], fg=self.colors["text_main"], relief="flat", padx=8, pady=2,
                                    command=self.browse_pegasus_icon)
        btn_browse_icon.pack(side=tk.LEFT, padx=(0, 10))

        btn_apply = tk.Button(r3, text="✔️ Appliquer les Modifications", font=("Segoe UI", 9, "bold"),
                              bg="#10b981", fg="#ffffff", relief="flat", padx=14, pady=3,
                              command=self.apply_pegasus_changes)
        btn_apply.pack(side=tk.RIGHT)

        # Remplir le tableau
        self.refresh_pegasus_tree()

    def refresh_pegasus_tree(self):
        """Met à jour l'affichage de l'arbre selon le filtre de type et de texte"""
        if not hasattr(self, "pegasus_tree"):
            return

        for item in self.pegasus_tree.get_children():
            self.pegasus_tree.delete(item)

        filter_type = getattr(self, "pegasus_type_filter", None)
        f_type = filter_type.get() if filter_type else "ALL"
        search_q = self.pegasus_search_var.get().lower().strip() if hasattr(self, "pegasus_search_var") else ""

        displayed_count = 0
        for it in self.pegasus_items_list:
            if f_type != "ALL" and it.get("type") != f_type:
                continue

            fn = it.get("filename", "")
            tid = it.get("title_id", "")
            ti = it.get("title", "")
            ic = it.get("icon", "")

            if search_q and not (search_q in fn.lower() or search_q in tid.lower() or search_q in ti.lower() or search_q in ic.lower()):
                continue

            self.pegasus_tree.insert("", tk.END, values=(
                it.get("type", "PKG"),
                fn,
                tid,
                ti,
                it.get("url", ""),
                ic
            ))
            displayed_count += 1

        if hasattr(self, "lbl_pegasus_count"):
            self.lbl_pegasus_count.config(text=f"{displayed_count} / {len(self.pegasus_items_list)} éléments")

    def on_pegasus_select(self, event=None):
        """Appelé lors de la sélection d'un item dans le tableau"""
        sel = self.pegasus_tree.selection()
        if not sel:
            return
        item_vals = self.pegasus_tree.item(sel[0], "values")
        if item_vals:
            fn = item_vals[1]
            tid = item_vals[2]
            title = item_vals[3]
            icon = item_vals[5]

            self.lbl_edit_filename.config(text=fn)
            self.pegasus_edit_title_id.set(tid)
            self.pegasus_edit_title.set(title)
            self.pegasus_edit_icon.set(icon)

    def apply_pegasus_changes(self):
        """Applique les modifications locales de l'élément sélectionné"""
        fn = self.lbl_edit_filename.cget("text")
        if not fn or fn.startswith("("):
            messagebox.showwarning("Sélection requise", "Veuillez sélectionner un élément dans la liste.", parent=self.root)
            return

        tid = self.pegasus_edit_title_id.get().strip()
        title = self.pegasus_edit_title.get().strip()
        icon = self.pegasus_edit_icon.get().strip()

        # Update in list
        for it in self.pegasus_items_list:
            if it.get("filename") == fn:
                it["title_id"] = tid
                it["title"] = title
                it["icon"] = icon
                break

        # Update in metadata dictionary
        self.pegasus_metadata[fn] = {
            "titleId": tid,
            "title": title,
            "icon": icon
        }

        self.refresh_pegasus_tree()
        self.log(f"Métadonnées modifiées pour {fn}: Title ID={tid}, Titre={title}, Icône={icon}", "INFO")

    def browse_pegasus_icon(self):
        """Ouvre un dialogue pour sélectionner un fichier image"""
        initial_dir = self.pegasus_icon_dir if os.path.exists(self.pegasus_icon_dir) else self.config["workspaceDir"]
        f = filedialog.askopenfilename(
            parent=self.root,
            title="Sélectionner une icône / poster",
            initialdir=initial_dir,
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.webp;*.svg"), ("Tous les fichiers", "*.*")]
        )
        if f:
            # Si le fichier est déjà dans assets/icon, on prend juste le nom relatif
            fname = os.path.basename(f)
            # Copie dans le dossier assets/icon si nécessaire
            target = os.path.join(self.pegasus_icon_dir, fname)
            if os.path.abspath(f) != os.path.abspath(target):
                try:
                    shutil.copy2(f, target)
                    self.log(f"Image copiée dans {self.pegasus_icon_dir}: {fname}", "SUCCESS")
                except Exception as e:
                    self.log(f"Erreur copie image: {e}", "WARN")
            self.pegasus_edit_icon.set(fname)

    def open_pegasus_icon_folder(self):
        """Ouvre l'explorateur de fichiers sur le dossier des icônes"""
        os.makedirs(self.pegasus_icon_dir, exist_ok=True)
        try:
            if sys.platform == "win32":
                os.startfile(self.pegasus_icon_dir)
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", self.pegasus_icon_dir])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", self.pegasus_icon_dir])
        except Exception as e:
            messagebox.showinfo("Dossier Icônes", f"Chemin des icônes :\n{self.pegasus_icon_dir}", parent=self.root)

    def scan_pegasus_feeds(self):
        """Scanne le catalogue local, les flux OPML locaux, et optionnellement l'API GitHub de manière stricte (fichiers réels uniquement)"""
        self.log("Démarrage du scan Pegasus (mode strict, paquets réels)...", "INFO")
        count_before = len(self.pegasus_items_list)

        def worker():
            items_dict = {it["filename"]: it for it in self.pegasus_items_list if self._is_real_package(it.get("filename"))}

            def add_scanned(pkg_info):
                if not pkg_info or not self._is_real_package(pkg_info.get("filename")):
                    return
                fn = pkg_info["filename"]
                if fn in items_dict:
                    # Enrich existing if url or icon was missing
                    if not items_dict[fn].get("url") and pkg_info.get("url"):
                        items_dict[fn]["url"] = pkg_info["url"]
                    if not items_dict[fn].get("icon") and pkg_info.get("icon"):
                        items_dict[fn]["icon"] = pkg_info["icon"]
                    return
                saved = self.pegasus_metadata.get(fn, {})
                items_dict[fn] = {
                    "type": pkg_info["type"],
                    "filename": fn,
                    "title_id": saved.get("titleId") or pkg_info["title_id"],
                    "title": saved.get("title") or pkg_info["title"],
                    "url": pkg_info["url"],
                    "icon": saved.get("icon") or pkg_info["icon"]
                }

            # 1. Scanner le catalogue local
            if os.path.exists(self.pegasus_catalog_path):
                try:
                    with open(self.pegasus_catalog_path, "r", encoding="utf-8") as f:
                        c_data = json.load(f)
                        raw_list = c_data if isinstance(c_data, list) else (c_data.get("packages", []) if isinstance(c_data, dict) else [])
                        for entry in raw_list:
                            add_scanned(self._extract_real_package(entry))
                except Exception as e:
                    self.log(f"Erreur scan catalog.json: {e}", "WARN")

            # 2. Scanner les flux OPML locaux dans feed/pkg/ et feed/ffpfsc/
            for cat, itype in [("pkg", "PKG"), ("ffpfsc", "FFPFSC")]:
                p = os.path.join(self.config["workspaceDir"], "evoX-CoreOS", "feed", cat)
                if os.path.exists(p):
                    for f in os.listdir(p):
                        if f.endswith(".opml"):
                            try:
                                tree = ET.parse(os.path.join(p, f))
                                for out in tree.findall(".//outline"):
                                    xml_url = out.attrib.get("xmlUrl", "")
                                    if xml_url:
                                        base = os.path.basename(xml_url.split("?")[0].strip())
                                        if self._is_real_package(base):
                                            title = out.attrib.get("description") or out.attrib.get("title") or out.attrib.get("text") or base
                                            if self._is_real_package(title):
                                                title = re.sub(r"\.(pkg|ffpfsc)$", "", base, flags=re.I).replace("_", " ")
                                            add_scanned({
                                                "type": "PKG" if base.lower().endswith(".pkg") else "FFPFSC",
                                                "filename": base,
                                                "title_id": "CUSA00000" if base.lower().endswith(".pkg") else "FFPFSC001",
                                                "title": title.strip(),
                                                "url": xml_url.strip(),
                                                "icon": ""
                                            })
                            except Exception:
                                pass

            # 3. Scanner GitHub distant si URL fournie (uniquement les fichiers manifestes officiels)
            repo_url = self.pegasus_repo_var.get().strip() if hasattr(self, "pegasus_repo_var") else ""
            if "github.com" in repo_url:
                clean = repo_url.rstrip("/").replace(".git", "")
                parts = clean.split("/")
                if len(parts) >= 2:
                    user, repo = parts[-2], parts[-1]
                    target_rel_files = [
                        "json/pegasus-dl/catalog.json",
                        "json/pkg.json",
                        "json/ffpfsc.json",
                        "feed/pkg/PS5_PKG_APPS.opml",
                        "feed/ffpfsc/FFPFSC_Apps.opml"
                    ]
                    for branch in ["main", "master"]:
                        found_branch = False
                        for rel in target_rel_files:
                            raw_url = f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{rel}"
                            try:
                                req = urllib.request.Request(raw_url, headers={"User-Agent": "evoX-Manager-Python"})
                                with urllib.request.urlopen(req, timeout=10) as raw_resp:
                                    found_branch = True
                                    content_bytes = raw_resp.read()
                                    if rel.endswith(".json"):
                                        parsed = json.loads(content_bytes.decode("utf-8"))
                                        raw_list = parsed if isinstance(parsed, list) else (
                                            parsed.get("packages", []) if "packages" in parsed else parsed.get("files", [])
                                        )
                                        if isinstance(raw_list, list):
                                            for elem in raw_list:
                                                add_scanned(self._extract_real_package(elem))
                                    elif rel.endswith(".opml"):
                                        tree = ET.fromstring(content_bytes.decode("utf-8"))
                                        for out in tree.findall(".//outline"):
                                            xml_url = out.attrib.get("xmlUrl", "")
                                            if xml_url:
                                                base = os.path.basename(xml_url.split("?")[0].strip())
                                                if self._is_real_package(base):
                                                    title = out.attrib.get("description") or out.attrib.get("title") or out.attrib.get("text") or base
                                                    if self._is_real_package(title):
                                                        title = re.sub(r"\.(pkg|ffpfsc)$", "", base, flags=re.I).replace("_", " ")
                                                    add_scanned({
                                                        "type": "PKG" if base.lower().endswith(".pkg") else "FFPFSC",
                                                        "filename": base,
                                                        "title_id": "CUSA00000" if base.lower().endswith(".pkg") else "FFPFSC001",
                                                        "title": title.strip(),
                                                        "url": xml_url.strip(),
                                                        "icon": ""
                                                    })
                            except Exception:
                                pass
                        if found_branch:
                            break

            # Filtrage strict final : aucun fichier qui ne termine pas par .pkg ou .ffpfsc
            self.pegasus_items_list = [it for it in items_dict.values() if self._is_real_package(it.get("filename"))]
            self.root.after(0, lambda: self._on_scan_complete(count_before))

        threading.Thread(target=worker, daemon=True).start()

    def _on_scan_complete(self, count_before):
        self.refresh_pegasus_tree()
        diff = len(self.pegasus_items_list) - count_before
        self.log(f"Scan terminé : {len(self.pegasus_items_list)} paquets réels au total (+{diff} nouveaux).", "SUCCESS")
        messagebox.showinfo("Scan Terminé",
                            f"Scan réussi !\n{len(self.pegasus_items_list)} paquets réels vérifiés (.pkg/.ffpfsc).\n(+{diff} nouveaux)",
                            parent=self.root)

    def save_pegasus_config(self):
        """Sauvegarde les métadonnées dans assets/icon/pegasus_metadata.json et catalog.json au format standard"""
        try:
            os.makedirs(self.pegasus_icon_dir, exist_ok=True)
            os.makedirs(os.path.dirname(self.pegasus_catalog_path), exist_ok=True)

            # 1. Sauvegarder pegasus_metadata.json (uniquement pour les paquets réels)
            clean_metadata = {
                k: v for k, v in self.pegasus_metadata.items()
                if self._is_real_package(k)
            }
            with open(self.pegasus_metadata_path, "w", encoding="utf-8") as f:
                json.dump(clean_metadata, f, indent=4, ensure_ascii=False)

            # 2. Sauvegarder catalog.json structuré proprement
            real_packages = [
                it for it in self.pegasus_items_list
                if self._is_real_package(it.get("filename"))
            ]

            packages_list = []
            coreos_repo_name = self.clean_repo_name(self.config.get("coreosRepo", ""))
            for it in real_packages:
                fn = it["filename"]
                is_pkg = fn.lower().endswith(".pkg")
                default_poster = (
                    f"https://cdn.jsdelivr.net/gh/{coreos_repo_name}@main/assets/evoX-CoreOS_pkg.jpg"
                    if is_pkg and coreos_repo_name
                    else (f"https://cdn.jsdelivr.net/gh/{coreos_repo_name}@main/assets/evoX-CoreOS_ffpfsc.jpg" if coreos_repo_name else "")
                )
                poster = default_poster
                if it.get("icon"):
                    poster = (
                        it["icon"]
                        if it["icon"].startswith("http")
                        else (f"https://cdn.jsdelivr.net/gh/{coreos_repo_name}@main/assets/icon/{it['icon']}" if coreos_repo_name else it["icon"])
                    )

                packages_list.append({
                    "titleId": it.get("title_id") or ("CUSA00000" if is_pkg else "FFPFSC001"),
                    "title": fn,
                    "version": it.get("version", "v1.0.0"),
                    "category": "game" if is_pkg else "FFPFSC",
                    "description": it.get("title") or fn,
                    "posterUrl": poster,
                    "downloadSource": f"https://github.com/{coreos_repo_name}" if coreos_repo_name else "",
                    "downloadLinks": [
                        {
                            "name": "Github",
                            "url": it.get("url", "")
                        }
                    ]
                })

            formatted_catalog = {
                "name": "Evox-CoreOS Catalog",
                "packages": packages_list
            }

            with open(self.pegasus_catalog_path, "w", encoding="utf-8") as f:
                json.dump(formatted_catalog, f, indent=4, ensure_ascii=False)

            self.log(f"Métadonnées sauvegardées dans {self.pegasus_metadata_path}", "SUCCESS")
            self.log(f"Catalogue synchronisé ({len(packages_list)} paquets réels) dans {self.pegasus_catalog_path}", "SUCCESS")
            messagebox.showinfo("Sauvegarde réussie",
                                f"Configuration Pegasus sauvegardée avec succès !\n\n"
                                f"Fichiers générés/mis à jour ({len(packages_list)} paquets réels) :\n"
                                f"• {self.pegasus_metadata_path}\n"
                                f"• {self.pegasus_catalog_path}",
                                parent=self.root)
        except Exception as e:
            self.log(f"Erreur sauvegarde Pegasus: {e}", "ERROR")
            messagebox.showerror("Erreur Sauvegarde", f"Impossible de sauvegarder la configuration : {e}", parent=self.root)

    # ==========================================
    # VUE 4: SYNCHRONISATION GITHUB
    # ==========================================
    def show_sync_view(self):
        container = tk.Frame(self.content_frame, bg=self.colors["bg_main"])
        container.pack(fill=tk.BOTH, expand=True)

        header_box = tk.Frame(container, bg=self.colors["bg_card"], highlightbackground=self.colors["border"], highlightthickness=1)
        header_box.pack(fill=tk.X, pady=(0, 15))

        lbl_t = tk.Label(header_box, text="⚡ Centre de Synchronisation GitHub & Multi-Dépôts",
                         font=("Segoe UI", 13, "bold"), fg=self.colors["text_main"], bg=self.colors["bg_card"])
        lbl_t.pack(anchor="w", padx=20, pady=(15, 4))

        lbl_sub = tk.Label(header_box, text="Importez, validez et synchronisez les dépôts GitHub de test ou de production vers votre espace local.",
                           font=("Segoe UI", 9), fg=self.colors["text_muted"], bg=self.colors["bg_card"])
        lbl_sub.pack(anchor="w", padx=20, pady=(0, 15))

        # Action bar: Global sync & repo config
        actions_bar = tk.Frame(container, bg=self.colors["bg_main"])
        actions_bar.pack(fill=tk.X, pady=(0, 15))

        btn_sync_all = tk.Button(
            actions_bar, text="⚡ TOUT SYNCHRONISER (CoreOS + WebUI)", font=("Segoe UI", 10, "bold"),
            bg=self.colors["accent"], fg="#ffffff", activebackground=self.colors["accent_hover"],
            activeforeground="#ffffff", relief="flat", padx=16, pady=8, cursor="hand2",
            command=lambda: self.sync_from_github_thread("both")
        )
        btn_sync_all.pack(side=tk.LEFT, padx=(0, 10))

        btn_reload_local = tk.Button(
            actions_bar, text="🔄 Recharger Fichiers Locaux", font=("Segoe UI", 9, "bold"),
            bg=self.colors["bg_input"], fg=self.colors["text_main"], relief="flat", padx=12, pady=8, cursor="hand2",
            command=self._manual_reload_local_data
        )
        btn_reload_local.pack(side=tk.LEFT, padx=(0, 10))

        btn_add_repo = tk.Button(
            actions_bar, text="➕ Configurer / Changer les Dépôts", font=("Segoe UI", 9, "bold"),
            bg=self.colors["bg_card"], fg=self.colors["text_main"], highlightbackground=self.colors["border"],
            highlightthickness=1, relief="flat", padx=12, pady=8, cursor="hand2",
            command=self.dialog_add_or_configure_repo
        )
        btn_add_repo.pack(side=tk.LEFT)

        # Repos container (2 columns)
        cards_frame = tk.Frame(container, bg=self.colors["bg_main"])
        cards_frame.pack(fill=tk.X, pady=(0, 15))

        # Card 1: CoreOS
        clean_coreos = self.clean_repo_name(self.config.get("coreosRepo", ""))
        c1 = tk.Frame(cards_frame, bg=self.colors["bg_card"], highlightbackground=self.colors["border"], highlightthickness=1)
        c1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        c1_inner = tk.Frame(c1, bg=self.colors["bg_card"], padx=15, pady=15)
        c1_inner.pack(fill=tk.BOTH, expand=True)

        lbl_c1_title = tk.Label(c1_inner, text="📦 Dépôt CoreOS (Flux OPML / Pegasus)",
                                font=("Segoe UI", 11, "bold"), fg=self.colors["accent"], bg=self.colors["bg_card"])
        lbl_c1_title.pack(anchor="w", pady=(0, 4))

        lbl_c1_repo = tk.Label(c1_inner, text=f"GitHub: {clean_coreos or 'Non configuré'}",
                               font=("Consolas", 9, "bold"), fg=self.colors["text_main"], bg=self.colors["bg_input"], padx=8, pady=4)
        lbl_c1_repo.pack(anchor="w", fill=tk.X, pady=(0, 10))

        total_opml = sum(len(v) for v in self.feed_data.values())
        lbl_c1_stats = tk.Label(c1_inner, text=f"• Fichiers OPML locaux chargés : {total_opml}\n• Paquets Pegasus en mémoire : {len(self.pegasus_items_list)}",
                                font=("Segoe UI", 9), fg=self.colors["text_muted"], bg=self.colors["bg_card"], justify=tk.LEFT)
        lbl_c1_stats.pack(anchor="w", pady=(0, 12))

        c1_btns = tk.Frame(c1_inner, bg=self.colors["bg_card"])
        c1_btns.pack(fill=tk.X)

        btn_c1_sync = tk.Button(c1_btns, text="📥 Sync", font=("Segoe UI", 9, "bold"),
                                bg=self.colors["accent"], fg="#ffffff", relief="flat", padx=10, pady=5, cursor="hand2",
                                command=lambda: self.sync_from_github_thread("coreos"))
        btn_c1_sync.pack(side=tk.LEFT, padx=(0, 6))

        btn_c1_test = tk.Button(c1_btns, text="🔍 Tester", font=("Segoe UI", 9),
                                bg=self.colors["bg_input"], fg=self.colors["text_main"], relief="flat", padx=10, pady=5, cursor="hand2",
                                command=lambda: self.test_github_repo_connection("coreosRepo"))
        btn_c1_test.pack(side=tk.LEFT, padx=(0, 6))

        btn_c1_edit = tk.Button(c1_btns, text="✏️ Éditer", font=("Segoe UI", 9),
                                bg=self.colors["bg_input"], fg=self.colors["text_main"], relief="flat", padx=10, pady=5, cursor="hand2",
                                command=lambda: self.dialog_edit_repo("coreosRepo"))
        btn_c1_edit.pack(side=tk.LEFT, padx=(0, 6))

        btn_c1_del = tk.Button(c1_btns, text="🗑️ Retirer", font=("Segoe UI", 9),
                               bg=self.colors["bg_input"], fg=self.colors["accent"], relief="flat", padx=10, pady=5, cursor="hand2",
                               command=lambda: self.remove_configured_repo("coreosRepo"))
        btn_c1_del.pack(side=tk.LEFT)

        # Card 2: WebUI
        clean_webui = self.clean_repo_name(self.config.get("webuiRepo", ""))
        c2 = tk.Frame(cards_frame, bg=self.colors["bg_card"], highlightbackground=self.colors["border"], highlightthickness=1)
        c2.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        c2_inner = tk.Frame(c2, bg=self.colors["bg_card"], padx=15, pady=15)
        c2_inner.pack(fill=tk.BOTH, expand=True)

        lbl_c2_title = tk.Label(c2_inner, text="🌐 Dépôt WebUI (config.json)",
                                font=("Segoe UI", 11, "bold"), fg=self.colors["accent_purple"], bg=self.colors["bg_card"])
        lbl_c2_title.pack(anchor="w", pady=(0, 4))

        lbl_c2_repo = tk.Label(c2_inner, text=f"GitHub: {clean_webui or 'Non configuré'}",
                               font=("Consolas", 9, "bold"), fg=self.colors["text_main"], bg=self.colors["bg_input"], padx=8, pady=4)
        lbl_c2_repo.pack(anchor="w", fill=tk.X, pady=(0, 10))

        has_cfg = bool(self.webui_config)
        lbl_c2_stats = tk.Label(c2_inner, text=f"• Configuration WebUI : {'Chargée avec succès' if has_cfg else 'Absente'}\n• Hôtes WebKit actifs : {len(self.webui_config.get('webkit', []))}",
                                font=("Segoe UI", 9), fg=self.colors["text_muted"], bg=self.colors["bg_card"], justify=tk.LEFT)
        lbl_c2_stats.pack(anchor="w", pady=(0, 12))

        c2_btns = tk.Frame(c2_inner, bg=self.colors["bg_card"])
        c2_btns.pack(fill=tk.X)

        btn_c2_sync = tk.Button(c2_btns, text="📥 Sync", font=("Segoe UI", 9, "bold"),
                                bg=self.colors["accent_purple"], fg="#ffffff", relief="flat", padx=10, pady=5, cursor="hand2",
                                command=lambda: self.sync_from_github_thread("webui"))
        btn_c2_sync.pack(side=tk.LEFT, padx=(0, 6))

        btn_c2_test = tk.Button(c2_btns, text="🔍 Tester", font=("Segoe UI", 9),
                                bg=self.colors["bg_input"], fg=self.colors["text_main"], relief="flat", padx=10, pady=5, cursor="hand2",
                                command=lambda: self.test_github_repo_connection("webuiRepo"))
        btn_c2_test.pack(side=tk.LEFT, padx=(0, 6))

        btn_c2_edit = tk.Button(c2_btns, text="✏️ Éditer", font=("Segoe UI", 9),
                                bg=self.colors["bg_input"], fg=self.colors["text_main"], relief="flat", padx=10, pady=5, cursor="hand2",
                                command=lambda: self.dialog_edit_repo("webuiRepo"))
        btn_c2_edit.pack(side=tk.LEFT, padx=(0, 6))

        btn_c2_del = tk.Button(c2_btns, text="🗑️ Retirer", font=("Segoe UI", 9),
                               bg=self.colors["bg_input"], fg=self.colors["accent"], relief="flat", padx=10, pady=5, cursor="hand2",
                               command=lambda: self.remove_configured_repo("webuiRepo"))
        btn_c2_del.pack(side=tk.LEFT)

        # Activity log in sync view
        log_box = tk.Frame(container, bg=self.colors["bg_card"], highlightbackground=self.colors["border"], highlightthickness=1)
        log_box.pack(fill=tk.BOTH, expand=True)

        lbl_log_title = tk.Label(log_box, text="📋 Journal de Synchronisation en Direct",
                                 font=("Segoe UI", 10, "bold"), fg=self.colors["text_main"], bg=self.colors["bg_card"])
        lbl_log_title.pack(anchor="w", padx=15, pady=(10, 4))

        self.sync_log_txt = scrolledtext.ScrolledText(log_box, height=10, bg=self.colors["bg_input"],
                                                      fg=self.colors["text_main"], font=("Consolas", 9), relief="flat")
        self.sync_log_txt.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        self.sync_log_txt.insert(tk.END, "Prêt pour la synchronisation. Cliquez sur un bouton ci-dessus pour démarrer.\n")

    def dialog_add_or_configure_repo(self):
        """Dialogue pour ajouter ou modifier les dépôts CoreOS ou WebUI"""
        win = tk.Toplevel(self.root)
        win.title("Configurer / Ajouter un Dépôt")
        win.geometry("540x360")
        win.configure(bg=self.colors["bg_main"])
        win.transient(self.root)

        tk.Label(win, text="Configurer les Dépôts GitHub", font=("Segoe UI", 12, "bold"),
                 fg=self.colors["text_main"], bg=self.colors["bg_main"]).pack(anchor="w", padx=25, pady=(20, 4))
        tk.Label(win, text="Spécifiez vos dépôts au format 'utilisateur/depot' ou par URL complète GitHub.",
                 font=("Segoe UI", 9), fg=self.colors["text_muted"], bg=self.colors["bg_main"]).pack(anchor="w", padx=25, pady=(0, 15))

        # CoreOS repo
        tk.Label(win, text="📦 Dépôt CoreOS (Flux OPML / Pegasus) :", font=("Segoe UI", 9, "bold"),
                 fg=self.colors["accent"], bg=self.colors["bg_main"]).pack(anchor="w", padx=25, pady=(4, 2))
        ent_coreos = tk.Entry(win, font=("Segoe UI", 10), bg=self.colors["bg_input"], fg=self.colors["text_main"],
                              insertbackground="#ffffff", relief="flat")
        ent_coreos.insert(0, self.config.get("coreosRepo", ""))
        ent_coreos.pack(fill=tk.X, padx=25, pady=(0, 10))

        # WebUI repo
        tk.Label(win, text="🌐 Dépôt WebUI (config.json) :", font=("Segoe UI", 9, "bold"),
                 fg=self.colors["accent_purple"], bg=self.colors["bg_main"]).pack(anchor="w", padx=25, pady=(4, 2))
        ent_webui = tk.Entry(win, font=("Segoe UI", 10), bg=self.colors["bg_input"], fg=self.colors["text_main"],
                             insertbackground="#ffffff", relief="flat")
        ent_webui.insert(0, self.config.get("webuiRepo", ""))
        ent_webui.pack(fill=tk.X, padx=25, pady=(0, 15))

        def do_save():
            val_c = self.clean_repo_name(ent_coreos.get())
            val_w = self.clean_repo_name(ent_webui.get())
            self.config["coreosRepo"] = val_c
            self.config["webuiRepo"] = val_w
            if not self.config.get("githubUser"):
                if "/" in val_c:
                    self.config["githubUser"] = val_c.split("/")[0]
                elif "/" in val_w:
                    self.config["githubUser"] = val_w.split("/")[0]
            self.save_preferences()
            self.load_local_data()
            self.load_pegasus_data()
            self.log("Configuration des dépôts mise à jour.", "SUCCESS")
            if self.current_section == "coreos" and self.active_tab_key == "sync":
                self.show_sync_view()
            elif self.current_section == "home":
                self.show_dashboard_view()
            messagebox.showinfo("Dépôts Enregistrés", "Les dépôts configurés ont été mis à jour avec succès.")
            win.destroy()

        btn_row = tk.Frame(win, bg=self.colors["bg_main"])
        btn_row.pack(fill=tk.X, padx=25, pady=10)

        tk.Button(btn_row, text="💾 Enregistrer", font=("Segoe UI", 9, "bold"),
                  bg=self.colors["accent"], fg="#ffffff", relief="flat", padx=16, pady=7, cursor="hand2",
                  command=do_save).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(btn_row, text="Annuler", font=("Segoe UI", 9),
                  bg=self.colors["bg_input"], fg=self.colors["text_main"], relief="flat", padx=16, pady=7, cursor="hand2",
                  command=win.destroy).pack(side=tk.LEFT)

    def dialog_edit_repo(self, repo_key="coreosRepo"):
        """Modifier un dépôt spécifique"""
        repo_label = "CoreOS (Flux OPML / Pegasus)" if repo_key == "coreosRepo" else "WebUI (config.json)"
        win = tk.Toplevel(self.root)
        win.title(f"Modifier le Dépôt {repo_label}")
        win.geometry("520x240")
        win.configure(bg=self.colors["bg_main"])
        win.transient(self.root)

        tk.Label(win, text=f"Dépôt GitHub : {repo_label}", font=("Segoe UI", 11, "bold"),
                 fg=self.colors["text_main"], bg=self.colors["bg_main"]).pack(anchor="w", padx=25, pady=(20, 4))
        tk.Label(win, text="Format : utilisateur/nom_du_depot ou URL GitHub",
                 font=("Segoe UI", 9), fg=self.colors["text_muted"], bg=self.colors["bg_main"]).pack(anchor="w", padx=25, pady=(0, 12))

        ent = tk.Entry(win, font=("Segoe UI", 10), bg=self.colors["bg_input"], fg=self.colors["text_main"],
                       insertbackground="#ffffff", relief="flat")
        ent.insert(0, self.config.get(repo_key, ""))
        ent.pack(fill=tk.X, padx=25, pady=(0, 20))
        ent.focus_set()

        def do_save():
            new_val = self.clean_repo_name(ent.get())
            self.config[repo_key] = new_val
            if "/" in new_val and not self.config.get("githubUser"):
                self.config["githubUser"] = new_val.split("/")[0]
            self.save_preferences()
            self.load_local_data()
            self.load_pegasus_data()
            self.log(f"Dépôt {repo_label} mis à jour : '{new_val}'", "SUCCESS")
            if self.current_section == "coreos" and self.active_tab_key == "sync":
                self.show_sync_view()
            elif self.current_section == "home":
                self.show_dashboard_view()
            messagebox.showinfo("Dépôt Mis à Jour", f"Le dépôt {repo_label} a été configuré à :\n{new_val or 'Non configuré'}")
            win.destroy()

        btn_row = tk.Frame(win, bg=self.colors["bg_main"])
        btn_row.pack(fill=tk.X, padx=25)

        tk.Button(btn_row, text="💾 Enregistrer", font=("Segoe UI", 9, "bold"),
                  bg=self.colors["accent"], fg="#ffffff", relief="flat", padx=15, pady=6, cursor="hand2",
                  command=do_save).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(btn_row, text="Annuler", font=("Segoe UI", 9),
                  bg=self.colors["bg_input"], fg=self.colors["text_main"], relief="flat", padx=15, pady=6, cursor="hand2",
                  command=win.destroy).pack(side=tk.LEFT)

    def remove_configured_repo(self, repo_key="coreosRepo"):
        """Supprimer ou retirer un dépôt configuré"""
        repo_label = "CoreOS (Flux OPML / Pegasus)" if repo_key == "coreosRepo" else "WebUI (config.json)"
        cur_val = self.config.get(repo_key, "")
        if not cur_val:
            messagebox.showinfo("Information", f"Le dépôt {repo_label} n'est pas configuré.")
            return

        confirm = messagebox.askyesno(
            "Supprimer le Dépôt",
            f"Voulez-vous vraiment supprimer le dépôt {repo_label} ('{cur_val}') ?\n\n"
            "Ce dépôt sera retiré de la configuration et ses données associées seront réinitialisées."
        )
        if not confirm:
            return

        self.config[repo_key] = ""
        if repo_key == "coreosRepo":
            for cat in ["apps", "payloads", "ffpfsc", "pkg"]:
                self.feed_data[cat] = []
            self.pegasus_items_list = []
            self.pegasus_metadata = {}
        elif repo_key == "webuiRepo":
            self.webui_config = {}
            self.webui_config_path = ""

        if not self.config.get("coreosRepo") and not self.config.get("webuiRepo"):
            self.config["hasSynchronized"] = False

        self.save_preferences()
        self.load_local_data()
        self.load_pegasus_data()
        self.log(f"Dépôt {repo_label} supprimé de la configuration.", "INFO")
        if self.current_section == "coreos" and self.active_tab_key == "sync":
            self.show_sync_view()
        elif self.current_section == "home":
            self.show_dashboard_view()
        messagebox.showinfo("Dépôt Supprimé", f"Le dépôt {repo_label} a été supprimé.")

    # ==========================================
    # VUE 6: ICÔNES FONTAWESOME & ICONS8
    # ==========================================
    # VUE 6: CATALOGUE D'ICÔNES ET ASSETS (FA 6.7 & ICONS8)
    # ==========================================
    def show_icons_view(self):
        top_bar = tk.Frame(self.content_frame, bg=self.colors["bg_main"])
        top_bar.pack(fill=tk.X, pady=(0, 10))

        lbl = tk.Label(top_bar, text="🎨 Bibliothèque d'Icônes (Font Awesome 6 & Icons8 Gratuit)",
                       font=("Segoe UI", 14, "bold"), fg=self.colors["text_main"], bg=self.colors["bg_main"])
        lbl.pack(side=tk.LEFT)

        # Base exhaustive d'icônes
        all_icons_data = [
            # Marques & Réseaux Sociaux (avec Facebook, Bluesky, etc.)
            ("fa-brands fa-facebook", "Facebook", "Marque / Réseau", "Réseau social Meta / Partage"),
            ("fa-brands fa-facebook-messenger", "Messenger", "Marque / Réseau", "Messagerie instantanée Facebook"),
            ("fa-brands fa-bluesky", "Bluesky Social", "Marque / Réseau", "Réseau social décentralisé Bluesky (ATProto)"),
            ("fa-brands fa-discord", "Discord", "Marque / Réseau", "Serveur vocal & salon Discord"),
            ("fa-brands fa-x-twitter", "X / Twitter", "Marque / Réseau", "Microblogging X (Twitter)"),
            ("fa-brands fa-youtube", "YouTube", "Marque / Réseau", "Chaîne et vidéos YouTube"),
            ("fa-brands fa-twitch", "Twitch", "Marque / Réseau", "Streaming et lives Twitch"),
            ("fa-brands fa-instagram", "Instagram", "Marque / Réseau", "Photos et publications Instagram"),
            ("fa-brands fa-tiktok", "TikTok", "Marque / Réseau", "Vidéos courtes TikTok"),
            ("fa-brands fa-telegram", "Telegram", "Marque / Réseau", "Canaux et groupes Telegram"),
            ("fa-brands fa-whatsapp", "WhatsApp", "Marque / Réseau", "Messagerie WhatsApp"),
            ("fa-brands fa-reddit", "Reddit", "Marque / Réseau", "Communautés Reddit"),
            ("fa-brands fa-threads", "Threads", "Marque / Réseau", "Réseau Threads Meta"),
            ("fa-brands fa-mastodon", "Mastodon", "Marque / Réseau", "Réseau libre Mastodon"),
            ("fa-brands fa-github", "GitHub", "Marque / Réseau", "Dépôt de code et releases GitHub"),
            ("fa-brands fa-steam", "Steam", "Marque / Réseau", "Boutique et communauté Steam Valve"),
            ("fa-brands fa-playstation", "PlayStation PSN", "Marque / Réseau", "PlayStation Network Sony"),
            ("fa-brands fa-spotify", "Spotify", "Marque / Réseau", "Streaming musical Spotify"),

            # Gaming, Scène PS5 & Exploits
            ("fa-solid fa-gamepad", "Manette DualSense", "Gaming / PS5", "Contrôleur PS5 / Jeux"),
            ("fa-solid fa-bolt", "Éclair Exploit", "Gaming / PS5", "Flash, Kstuff, etaHEN, Exploit Kernel"),
            ("fa-solid fa-fire", "Flamme Hot Release", "Gaming / PS5", "Nouveautés brûlantes et payloads"),
            ("fa-solid fa-cubes", "Payloads Manager", "Gaming / PS5", "Injecteur de payloads et binloader"),
            ("fa-solid fa-cube", "Module / Payload", "Gaming / PS5", "Module individuel"),
            ("fa-solid fa-box", "Paquet PKG", "Gaming / PS5", "Fichier d'installation .pkg"),
            ("fa-solid fa-box-open", "Paquet Décompressé", "Gaming / PS5", "Contenu extrait / FPF / FFPFSC"),
            ("fa-solid fa-boxes-stacked", "Dépôt Packages", "Gaming / PS5", "Catalogue de téléchargements"),
            ("fa-solid fa-store", "Homebrew Store", "Gaming / PS5", "Boutique d'applications et jeux"),
            ("fa-solid fa-rocket", "Fusée Boot / Run", "Gaming / PS5", "Lancement rapide d'exploit ou app"),
            ("fa-solid fa-trophy", "Trophée Platine", "Gaming / PS5", "Succès et récompenses PS5"),
            ("fa-solid fa-skull", "Crâne Hardcore", "Gaming / PS5", "Mode jailbreak avancé"),

            # Système, Fichiers & Réseau
            ("fa-solid fa-server", "Serveur Dédié", "Système / Réseau", "Serveur web / hôte HTTP"),
            ("fa-solid fa-microchip", "Processeur CPU", "Système / Réseau", "Noyau PS5 AMD Zen 2"),
            ("fa-solid fa-hard-drive", "Disque SSD NVMe", "Système / Réseau", "Stockage interne / externe"),
            ("fa-solid fa-folder-open", "Dossier Pegasus", "Système / Réseau", "Répertoire de jeux et assets"),
            ("fa-solid fa-network-wired", "Réseau LAN RJ45", "Système / Réseau", "Connexion Ethernet locale"),
            ("fa-solid fa-wifi", "Wi-Fi Sans Fil", "Système / Réseau", "Connexion sans fil"),
            ("fa-solid fa-satellite-dish", "Flux Distant", "Système / Réseau", "Transmission FTP / HTTP"),
            ("fa-solid fa-cloud-arrow-down", "Téléchargement Cloud", "Système / Réseau", "Téléchargement distant"),
            ("fa-solid fa-rss", "Flux RSS / OPML", "Système / Réseau", "Flux de syndication Pegasus"),
            ("fa-solid fa-shield-halved", "Bouclier Kstuff", "Système / Réseau", "Sécurité et sandbox bypass"),
            ("fa-solid fa-gears", "Paramètres WebUI", "Système / Réseau", "Configuration du serveur"),
            ("fa-solid fa-terminal", "Console / TTY", "Système / Réseau", "Invite de commande et logs"),

            # Multimédia & Audio
            ("fa-solid fa-circle-play", "Lecture / Start", "Multimédia", "Lancer un flux ou jeu"),
            ("fa-solid fa-music", "Musique Audio", "Multimédia", "Piste audio ou player"),
            ("fa-solid fa-headphones", "Casque 3D Audio", "Multimédia", "Sortie casque Tempest 3D"),
            ("fa-solid fa-tv", "Écran / IPTV", "Multimédia", "Lecteur IPTV ou stream ProsperoTV"),
            ("fa-solid fa-radio", "Radio FM / Web", "Multimédia", "Radio ProsperoRadio"),
            ("fa-solid fa-compact-disc", "Disque BD-JB", "Multimédia", "Disque Blu-ray Exploit BD-JB"),

            # Icons8 Gratuites (URLs Directes CDN)
            ("https://img.icons8.com/fluency/96/facebook-new.png", "Icons8 Facebook", "Icons8 CDN Gratuit", "Logo Facebook officiel haute résolution"),
            ("https://img.icons8.com/fluency/96/bluesky.png", "Icons8 Bluesky", "Icons8 CDN Gratuit", "Logo papillon Bluesky Social PNG"),
            ("https://img.icons8.com/fluency/96/discord-logo.png", "Icons8 Discord", "Icons8 CDN Gratuit", "Logo Discord Fluency"),
            ("https://img.icons8.com/fluency/96/twitterx.png", "Icons8 X / Twitter", "Icons8 CDN Gratuit", "Logo X Twitter moderne"),
            ("https://img.icons8.com/fluency/96/youtube-play.png", "Icons8 YouTube", "Icons8 CDN Gratuit", "Bouton YouTube Play"),
            ("https://img.icons8.com/fluency/96/twitch.png", "Icons8 Twitch", "Icons8 CDN Gratuit", "Logo Twitch Stream"),
            ("https://img.icons8.com/fluency/96/playstation-5.png", "Icons8 PlayStation 5", "Icons8 CDN Gratuit", "Console PS5 blanche Fluency"),
            ("https://img.icons8.com/fluency/96/controller.png", "Icons8 Controller", "Icons8 CDN Gratuit", "Manette DualSense blanche Fluency"),
            ("https://img.icons8.com/fluency/96/server.png", "Icons8 Server", "Icons8 CDN Gratuit", "Rack serveur informatique"),
            ("https://img.icons8.com/fluency/96/console.png", "Icons8 Terminal", "Icons8 CDN Gratuit", "Console de commande noire"),
            ("https://img.icons8.com/fluency/96/chip.png", "Icons8 CPU Puce", "Icons8 CDN Gratuit", "Microprocesseur électronique"),
            ("https://img.icons8.com/fluency/96/box.png", "Icons8 Package PKG", "Icons8 CDN Gratuit", "Boîte colis archive PKG"),
            ("https://img.icons8.com/fluency/96/folder-invoices.png", "Icons8 Dossier", "Icons8 CDN Gratuit", "Dossier avec fichiers Pegasus"),
            ("https://img.icons8.com/fluency/96/lightning-bolt.png", "Icons8 Exploit", "Icons8 CDN Gratuit", "Éclair d'énergie jaune"),
            ("https://img.icons8.com/fluency/96/wifi.png", "Icons8 Wi-Fi", "Icons8 CDN Gratuit", "Ondes Wi-Fi bleues"),
            ("https://img.icons8.com/fluency/96/shield.png", "Icons8 Bouclier", "Icons8 CDN Gratuit", "Bouclier de protection sécurité"),
            ("https://img.icons8.com/fluency/96/settings.png", "Icons8 Réglages", "Icons8 CDN Gratuit", "Engrenages de configuration")
        ]

        # Barre de recherche & filtres
        search_card = tk.Frame(self.content_frame, bg=self.colors["bg_card"], padx=12, pady=8,
                               highlightbackground=self.colors["border"], highlightthickness=1)
        search_card.pack(fill=tk.X, pady=(0, 10))

        tk.Label(search_card, text="🔍 Filtrer :", font=("Segoe UI", 9, "bold"),
                 fg=self.colors["text_muted"], bg=self.colors["bg_card"]).pack(side=tk.LEFT, padx=(0, 6))

        search_var = tk.StringVar()
        ent_search = tk.Entry(search_card, textvariable=search_var, font=("Segoe UI", 10),
                              bg=self.colors["bg_input"], fg=self.colors["text_main"],
                              insertbackground="white", relief="flat", width=30)
        ent_search.pack(side=tk.LEFT, padx=(0, 15), ipady=2)

        tk.Label(search_card, text="Double-cliquez sur une ligne pour copier la valeur.",
                 font=("Segoe UI", 9, "italic"), fg=self.colors["accent"], bg=self.colors["bg_card"]).pack(side=tk.LEFT)

        # Tableau des icônes
        tree_frame = tk.Frame(self.content_frame, bg=self.colors["bg_card"],
                              highlightbackground=self.colors["border"], highlightthickness=1)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("valeur", "nom", "categorie", "description")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=16)

        tree.heading("valeur", text="Classe FA / URL Icons8")
        tree.heading("nom", text="Nom de l'Icône")
        tree.heading("categorie", text="Catégorie")
        tree.heading("description", text="Usage recommandé")

        tree.column("valeur", width=330)
        tree.column("nom", width=170)
        tree.column("categorie", width=140)
        tree.column("description", width=280)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

        def copy_selected():
            sel = tree.selection()
            if not sel:
                return
            item = tree.item(sel[0])
            val = item["values"][0]
            self.root.clipboard_clear()
            self.root.clipboard_append(str(val))
            self.log(f"Copié dans le presse-papier: {val}", "INFO")
            messagebox.showinfo("Copié !", f"La valeur suivante a été copiée :\n\n{val}")

        def update_tree(*args):
            tree.delete(*tree.get_children())
            query = search_var.get().strip().lower()
            for val, nom, cat, desc in all_icons_data:
                if not query or (query in val.lower() or query in nom.lower() or query in cat.lower() or query in desc.lower()):
                    tree.insert("", tk.END, values=(val, nom, cat, desc))

        search_var.trace("w", update_tree)
        update_tree()

        tree.bind("<Double-1>", lambda e: copy_selected())

        # Barre inférieure avec boutons d'action rapide
        bottom_bar = tk.Frame(self.content_frame, bg=self.colors["bg_main"], pady=6)
        bottom_bar.pack(fill=tk.X)

        btn_copy = tk.Button(bottom_bar, text="📋 Copier la valeur sélectionnée", font=("Segoe UI", 9, "bold"),
                             bg=self.colors["accent"], fg="#ffffff", relief="flat", padx=12, pady=4,
                             command=copy_selected)
        btn_copy.pack(side=tk.LEFT, padx=(0, 10))

        def copy_bluesky():
            self.root.clipboard_clear()
            self.root.clipboard_append("fa-brands fa-bluesky")
            messagebox.showinfo("Copié !", "fa-brands fa-bluesky copié !")

        def copy_facebook():
            self.root.clipboard_clear()
            self.root.clipboard_append("fa-brands fa-facebook")
            messagebox.showinfo("Copié !", "fa-brands fa-facebook copié !")

        btn_bsky = tk.Button(bottom_bar, text="🦋 Bluesky FA", font=("Segoe UI", 9),
                             bg="#080d1a", fg="#38bdf8", relief="flat", padx=8, pady=4,
                             command=copy_bluesky)
        btn_bsky.pack(side=tk.LEFT, padx=(0, 6))

        btn_fb = tk.Button(bottom_bar, text="📘 Facebook FA", font=("Segoe UI", 9),
                           bg="#080d1a", fg="#60a5fa", relief="flat", padx=8, pady=4,
                           command=copy_facebook)
        btn_fb.pack(side=tk.LEFT)

    # ==========================================
    # VUE 7: VERSIONING & SAUVEGARDES
    # ==========================================
    def show_snapshots_view(self):
        top_bar = tk.Frame(self.content_frame, bg=self.colors["bg_main"])
        top_bar.pack(fill=tk.X, pady=(0, 10))

        lbl = tk.Label(top_bar, text="Historique des Snapshots & Sauvegardes",
                       font=("Segoe UI", 14, "bold"), fg=self.colors["text_main"], bg=self.colors["bg_main"])
        lbl.pack(side=tk.LEFT)

        btn_new_snap = tk.Button(top_bar, text="📸 Créer un Snapshot", font=("Segoe UI", 9, "bold"),
                                 bg=self.colors["accent"], fg="#ffffff", relief="flat", padx=12, pady=4,
                                 command=self.create_snapshot)
        btn_new_snap.pack(side=tk.RIGHT)

        inner = tk.Frame(self.content_frame, bg=self.colors["bg_card"], highlightbackground=self.colors["border"], highlightthickness=1)
        inner.pack(fill=tk.BOTH, expand=True)

        columns = ("time", "title", "files", "path")
        tree = ttk.Treeview(inner, columns=columns, show="headings")
        tree.heading("time", text="Horodatage")
        tree.heading("title", text="Titre du Snapshot")
        tree.heading("files", text="Éléments")
        tree.heading("path", text="Chemin ZIP")
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # List backups in backups directory
        if os.path.exists(self.config["backupsDir"]):
            for f in sorted(os.listdir(self.config["backupsDir"]), reverse=True):
                if f.endswith(".zip"):
                    tree.insert("", tk.END, values=(f[:19].replace("_", " "), f, "Archive Complète", os.path.join(self.config["backupsDir"], f)))

    def create_snapshot(self, title="Sauvegarde manuelle"):
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        zip_filename = os.path.join(self.config["backupsDir"], f"backup_{now}.zip")
        try:
            with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.config["workspaceDir"]):
                    if "backups" in root or "logs" in root:
                        continue
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, self.config["workspaceDir"])
                        zipf.write(full_path, rel_path)
            self.log(f"Snapshot créé avec succès : {os.path.basename(zip_filename)}", "SUCCESS")
            messagebox.showinfo("Sauvegarde", f"Snapshot créé avec succès !\nFichier : {os.path.basename(zip_filename)}")
        except Exception as e:
            self.log(f"Erreur création snapshot : {e}", "ERROR")

    # ==========================================
    # VUE 8: LOGS & CONSOLE
    # ==========================================
    def show_logs_view(self):
        lbl = tk.Label(self.content_frame, text="Journaux d'Événements & Logs Système",
                       font=("Segoe UI", 14, "bold"), fg=self.colors["text_main"], bg=self.colors["bg_main"])
        lbl.pack(anchor="w", pady=(0, 10))

        inner = tk.Frame(self.content_frame, bg=self.colors["bg_card"], highlightbackground=self.colors["border"], highlightthickness=1)
        inner.pack(fill=tk.BOTH, expand=True)

        self.txt_logs = scrolledtext.ScrolledText(inner, bg=self.colors["bg_sidebar"], fg=self.colors["text_main"],
                                                  font=("Consolas", 10), insertbackground="#ffffff", relief="flat")
        self.txt_logs.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Log tags
        self.txt_logs.tag_config("INFO", foreground="#60a5fa")
        self.txt_logs.tag_config("SUCCESS", foreground="#34d399")
        self.txt_logs.tag_config("WARN", foreground="#fbbf24")
        self.txt_logs.tag_config("ERROR", foreground="#f87171")

        # Load existing log file if any
        log_file = os.path.join(self.config["logsDir"], "evox_manager.log")
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.txt_logs.insert(tk.END, content)
            except Exception:
                pass

    def log(self, message, level="INFO"):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{now}] [{level}] {message}\n"
        # Write to file
        log_file = os.path.join(self.config["logsDir"], "evox_manager.log")
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(formatted)
        except Exception:
            pass

    # ==========================================
    # VUE 9: PRÉFÉRENCES LOCALES
    # ==========================================
    def show_preferences_view(self):
        lbl = tk.Label(self.content_frame, text="Paramètres & Préférences Locales",
                       font=("Segoe UI", 14, "bold"), fg=self.colors["text_main"], bg=self.colors["bg_main"])
        lbl.pack(anchor="w", pady=(0, 15))

        inner = tk.Frame(self.content_frame, bg=self.colors["bg_card"], highlightbackground=self.colors["border"], highlightthickness=1)
        inner.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        form = tk.Frame(inner, bg=self.colors["bg_card"])
        form.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)

        fields = [
            ("Utilisateur GitHub :", "githubUser"),
            ("Dépôt CoreOS :", "coreosRepo"),
            ("Dépôt WebUI :", "webuiRepo"),
            ("Répertoire de travail local :", "workspaceDir"),
            ("Token GitHub (optionnel pour push) :", "githubToken")
        ]

        pref_entries = {}
        for label_text, key in fields:
            lbl_f = tk.Label(form, text=label_text, font=("Segoe UI", 9, "bold"),
                             fg=self.colors["text_main"], bg=self.colors["bg_card"])
            lbl_f.pack(anchor="w", pady=(8, 2))

            ent = tk.Entry(form, font=("Segoe UI", 10), bg=self.colors["bg_input"], fg=self.colors["text_main"], relief="flat")
            ent.insert(0, str(self.config.get(key, "")))
            ent.pack(fill=tk.X, pady=(0, 5))
            pref_entries[key] = ent

        def save_all_prefs():
            for k, ent in pref_entries.items():
                val = ent.get().strip()
                if k in ("coreosRepo", "webuiRepo"):
                    val = self.clean_repo_name(val)
                self.config[k] = val
            self.ensure_directories()
            coreos_short = self.get_repo_short_name(self.config.get("coreosRepo", "evoX-CoreOS"))
            self.pegasus_catalog_path = os.path.join(self.config["workspaceDir"], coreos_short, "json", "pegasus-dl", "catalog.json")
            self.pegasus_icon_dir = os.path.join(self.config["workspaceDir"], coreos_short, "assets", "icon")
            self.pegasus_metadata_path = os.path.join(self.pegasus_icon_dir, "pegasus_metadata.json")
            self.pegasus_legacy_path = os.path.join(self.pegasus_icon_dir, "pegasus_icons.json")
            self.save_preferences()
            self.load_local_data()
            self.load_pegasus_data()
            messagebox.showinfo("Succès", "Préférences locales enregistrées avec succès.")

        btn_box = tk.Frame(form, bg=self.colors["bg_card"])
        btn_box.pack(pady=20, fill=tk.X)

        btn_save = tk.Button(btn_box, text="💾 Enregistrer les Préférences", font=("Segoe UI", 10, "bold"),
                             bg=self.colors["accent"], fg="#ffffff", relief="flat", padx=15, pady=8, cursor="hand2", command=save_all_prefs)
        btn_save.pack(side=tk.LEFT, padx=(0, 10))

        btn_test_sync = tk.Button(btn_box, text="⚡ Enregistrer & Synchroniser Tout", font=("Segoe UI", 10, "bold"),
                                  bg=self.colors["accent_purple"], fg="#ffffff", relief="flat", padx=15, pady=8, cursor="hand2",
                                  command=lambda: (save_all_prefs(), self.sync_from_github_thread("both")))
        btn_test_sync.pack(side=tk.LEFT)

    def _manual_reload_local_data(self):
        self.load_local_data()
        self.load_pegasus_data()
        total_opml = sum(len(v) for v in self.feed_data.values())
        if hasattr(self, "files_listbox") and self.files_listbox.winfo_exists():
            self.refresh_opml_files_list()
        if self.current_section == "coreos" and self.active_tab_key == "sync":
            self.show_sync_view()
        elif self.current_section == "home":
            self.show_dashboard_view()
        messagebox.showinfo("Rechargement", f"Données locales rechargées avec succès !\n\n• {total_opml} flux OPML actifs\n• {len(self.pegasus_items_list)} paquets Pegasus\n• WebUI config : {'OK' if self.webui_config else 'Vide'}")

    # ==========================================
    # LOGIQUE PERSISTANCE OPML & CONFIG JSON
    # ==========================================
    def load_local_data(self):
        # 1. Reset OPML feeds
        for cat in ["apps", "payloads", "ffpfsc", "pkg"]:
            self.feed_data[cat] = []

        loaded_files = set()
        coreos_short = self.get_repo_short_name(self.config.get("coreosRepo", "evoX-CoreOS"))

        # Base candidate directories for CoreOS feeds (strictly master: evoX-CoreOS/feed)
        candidate_bases = [
            os.path.join(self.config["workspaceDir"], "evoX-CoreOS"),
            os.path.join(self.config["workspaceDir"], coreos_short)
        ]

        unwanted_opmls = {"apps.opml", "payloads.opml", "pkg.opml", "ffpfsc.opml", "source_aio.opml", "sourceaio.opml"}

        # 1. Scan standard feed/{cat} directories ONLY
        for base in candidate_bases:
            if not os.path.isdir(base):
                continue
            feed_base = os.path.join(base, "feed") if os.path.isdir(os.path.join(base, "feed")) else None
            if not feed_base:
                continue
            for cat in ["apps", "payloads", "ffpfsc", "pkg"]:
                cat_dir = os.path.join(feed_base, cat)
                if os.path.isdir(cat_dir):
                    for f in sorted(os.listdir(cat_dir)):
                        if f.lower() in unwanted_opmls:
                            # Automatically delete legacy parasite auto-summary file
                            try:
                                os.remove(os.path.join(cat_dir, f))
                            except Exception:
                                pass
                            continue
                        if f.endswith(".opml") and f not in loaded_files:
                            file_path = os.path.join(cat_dir, f)
                            try:
                                with open(file_path, "r", encoding="utf-8") as opml_file:
                                    content = opml_file.read()
                                    parsed = self.parse_opml_string(content, f, cat)
                                    self.feed_data[cat].append(parsed)
                                    loaded_files.add(f)
                            except Exception as e:
                                self.log(f"Erreur lecture {file_path}: {e}", "ERROR")

        # 2. Load WebUI config.json from master location
        webui_short = self.get_repo_short_name(self.config.get("webuiRepo", "evoX-CoreOS-webui"))
        config_candidates = [
            os.path.join(self.config["workspaceDir"], "evoX-CoreOS-webui", "web", "data", "config.json"),
            os.path.join(self.config["workspaceDir"], "evoX-CoreOS-WebUI", "web", "data", "config.json"),
            os.path.join(self.config["workspaceDir"], webui_short, "web", "data", "config.json"),
            os.path.join(self.config["workspaceDir"], webui_short, "data", "config.json"),
            os.path.join(self.config["workspaceDir"], webui_short, "config.json"),
            os.path.join(self.config["workspaceDir"], "web", "data", "config.json"),
            os.path.join(self.config["workspaceDir"], "data", "config.json"),
            os.path.join(self.config["workspaceDir"], "config.json"),
        ]

        config_found = False
        for cfg_path in config_candidates:
            if os.path.isfile(cfg_path):
                try:
                    with open(cfg_path, "r", encoding="utf-8") as cfg_file:
                        self.webui_config = json.load(cfg_file)
                        self.webui_config_path = cfg_path
                        config_found = True
                        break
                except Exception as e:
                    self.log(f"Erreur lecture {cfg_path}: {e}", "ERROR")

        total_opml = sum(len(v) for v in self.feed_data.values())
        self.log(f"Indexation locale terminée : {total_opml} flux OPML chargés, config WebUI : {'OK' if config_found else 'Non trouvée'}", "INFO")

    def parse_opml_string(self, content, filename, category):
        outlines = []
        title = filename.replace(".opml", "")
        try:
            root = ET.fromstring(content)
            head_title = root.find(".//head/title")
            if head_title is not None and head_title.text:
                title = head_title.text.strip()

            for outline in root.findall(".//outline"):
                raw_url = (
                    outline.get("xmlUrl") or
                    outline.get("url") or
                    outline.get("link") or
                    outline.get("htmlUrl") or
                    outline.get("download") or
                    ""
                ).strip()

                raw_title = (
                    outline.get("title") or
                    outline.get("text") or
                    outline.get("name") or
                    ""
                ).strip()

                raw_text = (
                    outline.get("text") or
                    outline.get("title") or
                    outline.get("name") or
                    raw_title or
                    "Sans titre"
                ).strip()

                raw_author = (
                    outline.get("author") or
                    outline.get("creator") or
                    ""
                ).strip()

                raw_desc = (
                    outline.get("description") or
                    outline.get("desc") or
                    ""
                ).strip()

                if raw_url or raw_title or raw_text != "Sans titre":
                    outlines.append({
                        "text": raw_text,
                        "title": raw_title or raw_text,
                        "type": outline.get("type", "rss"),
                        "xmlUrl": raw_url,
                        "author": raw_author,
                        "description": raw_desc
                    })
        except Exception as e:
            self.log(f"Erreur parsing XML pour {filename}: {e}", "WARN")

        return {
            "name": filename,
            "category": category,
            "title": title,
            "outlines": outlines
        }

    def save_opml_file_to_disk(self, file_obj):
        cat = file_obj["category"]
        filename = file_obj["name"]
        coreos_repo = self.clean_repo_name(self.config.get("coreosRepo", ""))
        if not coreos_repo:
            self.log("Impossible d'enregistrer le flux : aucun dépôt CoreOS configuré.", "ERROR")
            return

        coreos_dir = self.get_repo_dir(coreos_repo)
        target_dir = os.path.join(coreos_dir, "feed", cat)

        # Génération XML OPML standardisé 2.0
        opml_elem = ET.Element("opml", version="2.0")
        head_elem = ET.SubElement(opml_elem, "head")
        title_elem = ET.SubElement(head_elem, "title")
        title_elem.text = file_obj.get("title", filename.replace(".opml", ""))

        body_elem = ET.SubElement(opml_elem, "body")
        for item in file_obj.get("outlines", []):
            attrs = {
                "text": item.get("text", item.get("title", "")),
                "title": item.get("title", item.get("text", "")),
                "type": item.get("type", "rss"),
                "xmlUrl": item.get("xmlUrl", ""),
                "author": item.get("author", ""),
                "description": item.get("description", "")
            }
            ET.SubElement(body_elem, "outline", attrs)

        rough_string = ET.tostring(opml_elem, "utf-8")
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")

        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(pretty_xml)
        self.log(f"Flux OPML enregistré avec succès dans {file_path}", "SUCCESS")
    def save_webui_config_to_disk(self):
        try:
            if hasattr(self, "entry_site_title") and self.entry_site_title.winfo_exists():
                self.webui_config["siteTitle"] = self.entry_site_title.get().strip()
            if hasattr(self, "entry_gh_user") and self.entry_gh_user.winfo_exists():
                if "github" not in self.webui_config:
                    self.webui_config["github"] = {}
                self.webui_config["github"]["user"] = self.entry_gh_user.get().strip()
            if hasattr(self, "entry_data_repo") and self.entry_data_repo.winfo_exists():
                if "github" not in self.webui_config:
                    self.webui_config["github"] = {}
                self.webui_config["github"]["dataRepository"] = self.clean_repo_name(self.entry_data_repo.get().strip())
            if hasattr(self, "entry_webui_repo") and self.entry_webui_repo.winfo_exists():
                if "github" not in self.webui_config:
                    self.webui_config["github"] = {}
                self.webui_config["github"]["webuiRepository"] = self.clean_repo_name(self.entry_webui_repo.get().strip())
            if hasattr(self, "entry_src_pldmgr") and self.entry_src_pldmgr.winfo_exists():
                if "sources" not in self.webui_config:
                    self.webui_config["sources"] = {}
                self.webui_config["sources"]["pldmgr"] = self.entry_src_pldmgr.get().strip()
            if hasattr(self, "entry_src_changelog") and self.entry_src_changelog.winfo_exists():
                if "sources" not in self.webui_config:
                    self.webui_config["sources"] = {}
                self.webui_config["sources"]["changelog"] = self.entry_src_changelog.get().strip()
            if hasattr(self, "entry_releases_base") and self.entry_releases_base.winfo_exists():
                if "releases" not in self.webui_config:
                    self.webui_config["releases"] = {}
                self.webui_config["releases"]["baseUrl"] = self.entry_releases_base.get().strip()
            if hasattr(self, "txt_raw_json") and self.txt_raw_json.winfo_exists():
                raw_text = self.txt_raw_json.get("1.0", tk.END).strip()
                if raw_text:
                    self.webui_config = json.loads(raw_text)
        except Exception as err:
            self.log(f"Avertissement synchronisation champs config: {err}", "WARN")

        webui_repo = self.clean_repo_name(self.config.get("webuiRepo", ""))
        if not webui_repo:
            self.log("Impossible d'enregistrer la configuration : aucun dépôt WebUI configuré.", "ERROR")
            messagebox.showerror("Erreur", "Aucun dépôt WebUI n'est configuré dans les préférences.")
            return

        webui_dir = self.get_repo_dir(webui_repo)
        webui_cfg_path = os.path.join(webui_dir, "web", "data", "config.json")

        try:
            os.makedirs(os.path.dirname(webui_cfg_path), exist_ok=True)
            with open(webui_cfg_path, "w", encoding="utf-8") as f:
                json.dump(self.webui_config, f, indent=2, ensure_ascii=False)
            self.log(f"Configuration enregistrée dans {webui_cfg_path}", "SUCCESS")
            messagebox.showinfo("Succès", f"Configuration enregistrée avec succès dans :\n{webui_cfg_path}")
        except Exception as e:
            self.log(f"Erreur écriture config.json: {e}", "ERROR")
            messagebox.showerror("Erreur", f"Impossible d'enregistrer config.json :\n{e}")
    # ==========================================
    # TESTS ET SYNCHRONISATION MULTI-DÉPÔTS GITHUB
    # ==========================================
    def test_github_repo_connection(self, repo_key="coreosRepo"):
        t = threading.Thread(target=self._test_repo_worker, args=(repo_key,))
        t.daemon = True
        t.start()

    def _test_repo_worker(self, repo_key):
        raw_val = self.config.get(repo_key, "")
        clean_repo = self.clean_repo_name(raw_val)
        self.log(f"Test de connexion vers GitHub pour {repo_key}: '{clean_repo}'...", "INFO")
        if hasattr(self, "sync_log_txt") and self.sync_log_txt.winfo_exists():
            self.root.after(0, lambda: (
                self.sync_log_txt.insert(tk.END, f"\n[TEST] Vérification de https://github.com/{clean_repo}...\n"),
                self.sync_log_txt.see(tk.END)
            ))

        if not clean_repo:
            msg = f"Erreur: Aucun nom de dépôt défini pour {repo_key}."
            self.log(msg, "ERROR")
            if hasattr(self, "sync_log_txt") and self.sync_log_txt.winfo_exists():
                self.root.after(0, lambda: (
                    self.sync_log_txt.insert(tk.END, f"[TEST ÉCHEC] {msg}\n"),
                    self.sync_log_txt.see(tk.END)
                ))
            messagebox.showerror("Erreur", msg)
            return

        headers = self.get_github_headers()
        api_url = f"https://api.github.com/repos/{clean_repo}"
        try:
            req = urllib.request.Request(api_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                branch = data.get("default_branch", "main")
                is_priv = data.get("private", False)
                desc = data.get("description") or "Aucune description"
                msg = f"Dépôt accessible : {clean_repo} (Branche: {branch}, {'Privé' if is_priv else 'Public'})"
                self.log(msg, "SUCCESS")
                if hasattr(self, "sync_log_txt") and self.sync_log_txt.winfo_exists():
                    self.root.after(0, lambda: (
                        self.sync_log_txt.insert(tk.END, f"[TEST OK] {msg}\nDescription: {desc}\n"),
                        self.sync_log_txt.see(tk.END)
                    ))
                messagebox.showinfo("Test Connexion Réussi", f"Dépôt : {clean_repo}\n\nBranche par défaut : {branch}\nVisibilité : {'Privé' if is_priv else 'Public'}\nDescription : {desc}")
        except urllib.error.HTTPError as he:
            if he.code in (401, 403):
                # Fallback vérification web directe si quota API GitHub atteint sans token
                web_url = f"https://github.com/{clean_repo}"
                try:
                    w_req = urllib.request.Request(web_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(w_req, timeout=8) as w_resp:
                        if w_resp.status == 200:
                            ok_msg = f"Dépôt public accessible : {clean_repo}\n(Quota API REST 60 req/h atteint, mais l'accès direct Web/ZIP fonctionne parfaitement sans limite de débit)."
                            self.log(ok_msg, "SUCCESS")
                            if hasattr(self, "sync_log_txt") and self.sync_log_txt.winfo_exists():
                                self.root.after(0, lambda: (
                                    self.sync_log_txt.insert(tk.END, f"[TEST OK] {ok_msg}\n"),
                                    self.sync_log_txt.see(tk.END)
                                ))
                            messagebox.showinfo("Dépôt Accessible", ok_msg)
                            return
                except Exception:
                    pass
                err_msg = f"HTTP {he.code} : Limite de requêtes GitHub atteinte sans token.\n(Renseignez un Token GitHub dans Préférences pour les dépôts privés ou un quota étendu)."
            elif he.code == 404:
                err_msg = f"HTTP 404 : Dépôt '{clean_repo}' introuvable ou privé.\n(Ajoutez un Token GitHub dans Préférences si le dépôt est privé)."
            else:
                err_msg = f"HTTP {he.code} : {he.reason}"
            self.log(err_msg, "ERROR")
            if hasattr(self, "sync_log_txt") and self.sync_log_txt.winfo_exists():
                self.root.after(0, lambda: (
                    self.sync_log_txt.insert(tk.END, f"[TEST ÉCHEC] {err_msg}\n"),
                    self.sync_log_txt.see(tk.END)
                ))
            messagebox.showerror("Échec du Test", err_msg)
        except Exception as ex:
            err_msg = f"Erreur réseau / connexion : {ex}"
            self.log(err_msg, "ERROR")
            if hasattr(self, "sync_log_txt") and self.sync_log_txt.winfo_exists():
                self.root.after(0, lambda: (
                    self.sync_log_txt.insert(tk.END, f"[TEST ÉCHEC] {err_msg}\n"),
                    self.sync_log_txt.see(tk.END)
                ))
            messagebox.showerror("Erreur Connexion", err_msg)

    def sync_from_github_thread(self, repo_type="both"):
        t = threading.Thread(target=self._sync_repo_worker, args=(repo_type,))
        t.daemon = True
        t.start()

    def _sync_repo_worker(self, repo_type="both"):
        def log_sync(msg, level="INFO"):
            self.log(msg, level)
            if hasattr(self, "sync_log_txt") and self.sync_log_txt.winfo_exists():
                self.root.after(0, lambda m=f"[{level}] {msg}\n": (
                    self.sync_log_txt.insert(tk.END, m),
                    self.sync_log_txt.see(tk.END)
                ))

        log_sync(f"=== Début synchronisation (Mode: {repo_type}) ===", "INFO")
        headers = self.get_github_headers()
        imported_files_count = 0

        # ==========================================
        # 1. COREOS SYNCHRONIZATION
        # ==========================================
        if repo_type in ("coreos", "both"):
            raw_coreos = self.config.get("coreosRepo", "")
            coreos_repo = self.clean_repo_name(raw_coreos)
            if not coreos_repo:
                log_sync("Dépôt CoreOS non configuré. Passage.", "WARN")
            else:
                log_sync(f"Synchronisation CoreOS depuis GitHub : '{coreos_repo}'...", "INFO")
                dest_dir = self.get_repo_dir(coreos_repo)
                dest_dirs = [dest_dir]

                # Step 1: Detect branch
                default_branch = "main"
                api_url = f"https://api.github.com/repos/{coreos_repo}"
                api_rate_limited = False
                try:
                    req = urllib.request.Request(api_url, headers=headers)
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        repo_meta = json.loads(resp.read().decode("utf-8"))
                        default_branch = repo_meta.get("default_branch", "main")
                        log_sync(f"Dépôt {coreos_repo} détecté (branche: {default_branch})", "SUCCESS")
                except urllib.error.HTTPError as he:
                    if he.code in (401, 403):
                        api_rate_limited = True
                        log_sync(f"Note quota GitHub ({he.code}) : utilisation de la méthode directe ZIP.", "INFO")
                    else:
                        log_sync(f"Info dépôt HTTP {he.code} ({he.reason}). Utilisation branche '{default_branch}'.", "WARN")
                except Exception as ex:
                    log_sync(f"Info dépôt exception ({ex}). Utilisation branche '{default_branch}'.", "WARN")

                discovered = []
                unwanted_opmls = {"apps.opml", "payloads.opml", "pkg.opml", "ffpfsc.opml", "source_aio.opml", "sourceaio.opml"}

                # Step 2: Try Git Trees API only if not rate limited
                if not api_rate_limited:
                    tree_url = f"https://api.github.com/repos/{coreos_repo}/git/trees/{default_branch}?recursive=1"
                    try:
                        req = urllib.request.Request(tree_url, headers=headers)
                        with urllib.request.urlopen(req, timeout=12) as resp:
                            tree_data = json.loads(resp.read().decode("utf-8"))
                            for item in tree_data.get("tree", []):
                                p = item.get("path", "").replace("\\", "/")
                                p_low = p.lower()
                                if p_low.endswith(".opml"):
                                    parts = [seg for seg in p.split("/") if seg]
                                    # Expected structure: feed/<category>/<filename>.opml
                                    if len(parts) >= 3 and parts[0].lower() == "feed":
                                        cat = parts[1].lower()
                                        if cat in ("apps", "payloads", "pkg", "ffpfsc"):
                                            fname = parts[-1]
                                            if fname.lower() not in unwanted_opmls:
                                                discovered.append((p, cat, fname))
                                elif p_low.endswith("catalog.json") and "pegasus-dl" in p_low:
                                    discovered.append((p, "catalog", "catalog.json"))
                                elif p_low.endswith("pegasus_metadata.json"):
                                    discovered.append((p, "metadata", "pegasus_metadata.json"))
                            log_sync(f"Arborescence Git analysée : {len(discovered)} fichier(s) OPML légitimes découverts dans /feed/.", "INFO")
                    except Exception as e_tree:
                        log_sync(f"Git Tree API non disponible, bascule directe sur archive ZIP.", "INFO")

                # Step 3: Download discovered files via raw URLs if any
                coreos_imported = 0
                if discovered:
                    for p, cat, filename in discovered:
                        raw_url = f"https://raw.githubusercontent.com/{coreos_repo}/{default_branch}/{p}"

                        try:
                            f_req = urllib.request.Request(raw_url, headers=headers)
                            with urllib.request.urlopen(f_req, timeout=10) as f_resp:
                                content = f_resp.read()

                            if cat in ("apps", "payloads", "pkg", "ffpfsc"):
                                for base_dir in set(dest_dirs):
                                    dest = os.path.join(base_dir, "feed", cat, filename)
                                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                                    with open(dest, "wb") as f_out:
                                        f_out.write(content)
                                coreos_imported += 1
                                log_sync(f"Flux importé : /feed/{cat}/{filename}", "SUCCESS")
                            elif cat == "catalog":
                                for base_dir in set(dest_dirs):
                                    dest = os.path.join(base_dir, "json", "pegasus-dl", "catalog.json")
                                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                                    with open(dest, "wb") as f_out:
                                        f_out.write(content)
                                coreos_imported += 1
                                log_sync("Catalogue Pegasus catalog.json importé !", "SUCCESS")
                            elif cat == "metadata":
                                for base_dir in set(dest_dirs):
                                    dest = os.path.join(base_dir, "assets", "icon", "pegasus_metadata.json")
                                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                                    with open(dest, "wb") as f_out:
                                        f_out.write(content)
                                coreos_imported += 1
                                log_sync("Métadonnées Pegasus importées !", "SUCCESS")
                        except Exception as ed:
                            log_sync(f"Erreur téléchargement de {p}: {ed}", "WARN")

                # Step 4: Archive ZIP direct download (immune to GitHub 403 API rate limits!)
                if coreos_imported == 0:
                    log_sync(f"Téléchargement direct de l'archive ZIP pour '{coreos_repo}'...", "INFO")
                    zip_urls = [
                        f"https://codeload.github.com/{coreos_repo}/zip/refs/heads/{default_branch}",
                        f"https://github.com/{coreos_repo}/archive/refs/heads/{default_branch}.zip",
                        f"https://codeload.github.com/{coreos_repo}/zip/refs/heads/main",
                        f"https://codeload.github.com/{coreos_repo}/zip/refs/heads/master"
                    ]
                    for z_url in zip_urls:
                        try:
                            z_req = urllib.request.Request(z_url, headers=headers)
                            with urllib.request.urlopen(z_req, timeout=20) as z_resp:
                                z_data = z_resp.read()
                                import io
                                with zipfile.ZipFile(io.BytesIO(z_data)) as zf:
                                    for zinfo in zf.namelist():
                                        clean_z = zinfo.replace("\\", "/")
                                        fname = os.path.basename(clean_z)
                                        if not fname:
                                            continue
                                        parts = [seg for seg in clean_z.split("/") if seg]
                                        feed_idx = -1
                                        for idx, seg in enumerate(parts):
                                            if seg.lower() == "feed":
                                                feed_idx = idx
                                                break

                                        if fname.lower().endswith(".opml"):
                                            # MUST be strictly inside feed/<category>/
                                            if feed_idx != -1 and len(parts) > feed_idx + 2:
                                                cat = parts[feed_idx + 1].lower()
                                                if cat in ("apps", "payloads", "pkg", "ffpfsc"):
                                                    if fname.lower() not in unwanted_opmls:
                                                        content = zf.read(zinfo)
                                                        for base_dir in set(dest_dirs):
                                                            dest = os.path.join(base_dir, "feed", cat, fname)
                                                            os.makedirs(os.path.dirname(dest), exist_ok=True)
                                                            with open(dest, "wb") as fo:
                                                                fo.write(content)
                                                        coreos_imported += 1
                                                        log_sync(f"Flux extrait : /feed/{cat}/{fname}", "SUCCESS")
                                        elif fname == "catalog.json" and "pegasus-dl" in clean_z.lower():
                                            content = zf.read(zinfo)
                                            for base_dir in set(dest_dirs):
                                                dest = os.path.join(base_dir, "json", "pegasus-dl", "catalog.json")
                                                os.makedirs(os.path.dirname(dest), exist_ok=True)
                                                with open(dest, "wb") as fo:
                                                    fo.write(content)
                                            coreos_imported += 1
                                            log_sync("catalog.json extrait de l'archive ZIP !", "SUCCESS")
                                        elif fname == "pegasus_metadata.json":
                                            content = zf.read(zinfo)
                                            for base_dir in set(dest_dirs):
                                                dest = os.path.join(base_dir, "assets", "icon", "pegasus_metadata.json")
                                                os.makedirs(os.path.dirname(dest), exist_ok=True)
                                                with open(dest, "wb") as fo:
                                                    fo.write(content)
                                            coreos_imported += 1
                                            log_sync("pegasus_metadata.json extrait de l'archive ZIP !", "SUCCESS")
                            if coreos_imported > 0:
                                break
                        except Exception as ez:
                            pass

                imported_files_count += coreos_imported
                log_sync(f"Dépôt CoreOS : {coreos_imported} fichier(s) importé(s) dans {dest_dir}.", "SUCCESS" if coreos_imported > 0 else "WARN")

        # ==========================================
        # 2. WEBUI CONFIG SYNCHRONIZATION
        # ==========================================
        if repo_type in ("webui", "both"):
            raw_webui = self.config.get("webuiRepo", "")
            webui_repo = self.clean_repo_name(raw_webui)
            if not webui_repo:
                log_sync("Dépôt WebUI non configuré. Passage.", "WARN")
            else:
                log_sync(f"Synchronisation WebUI depuis GitHub : '{webui_repo}'...", "INFO")
                dest_dir = self.get_repo_dir(webui_repo)
                webui_dest_path = os.path.join(dest_dir, "web", "data", "config.json")

                # Detect default branch (or fallback)
                w_branch = "main"
                candidate_branches = ["main", "master"]

                candidate_paths = [
                    "web/data/config.json",
                    "data/config.json",
                    "config.json",
                    "web/config.json",
                    "src/data/config.json",
                    "public/data/config.json"
                ]

                cfg_downloaded = False
                parsed_cfg = None

                # 1. Try Direct Raw URLs (no GitHub REST API rate limits!)
                for br in candidate_branches:
                    for c_path in candidate_paths:
                        raw_cfg_url = f"https://raw.githubusercontent.com/{webui_repo}/{br}/{c_path}"
                        try:
                            req = urllib.request.Request(raw_cfg_url, headers=headers)
                            with urllib.request.urlopen(req, timeout=10) as resp:
                                cfg_text = resp.read().decode("utf-8")
                                parsed_cfg = json.loads(cfg_text)
                                cfg_downloaded = True
                                log_sync(f"Configuration WebUI récupérée depuis {raw_cfg_url}", "SUCCESS")
                                break
                        except Exception:
                            pass
                    if cfg_downloaded:
                        break

                # 2. Fallback: Download repo ZIP and extract config.json directly (no API rate limit!)
                if not cfg_downloaded:
                    for br in candidate_branches:
                        zip_urls = [
                            f"https://codeload.github.com/{webui_repo}/zip/refs/heads/{br}",
                            f"https://github.com/{webui_repo}/archive/refs/heads/{br}.zip"
                        ]
                        for z_url in zip_urls:
                            try:
                                req = urllib.request.Request(z_url, headers=headers)
                                with urllib.request.urlopen(req, timeout=20) as resp:
                                    z_data = resp.read()
                                import io
                                with zipfile.ZipFile(io.BytesIO(z_data)) as zf:
                                    matched_entry = None
                                    for zinfo in zf.namelist():
                                        low = zinfo.lower()
                                        if low.endswith("web/data/config.json") or low.endswith("/data/config.json") or low.endswith("/config.json") or zinfo == "config.json":
                                            matched_entry = zinfo
                                            if "web" in low:
                                                break
                                    if matched_entry:
                                        content_bytes = zf.read(matched_entry)
                                        parsed_cfg = json.loads(content_bytes.decode("utf-8"))
                                        cfg_downloaded = True
                                        log_sync(f"Configuration WebUI extraite de l'archive ZIP ({matched_entry})", "SUCCESS")
                                        break
                            except Exception:
                                pass
                        if cfg_downloaded:
                            break

                # Write ONLY to the master destination: /workspace/evoX-CoreOS-webui/web/data/config.json
                if cfg_downloaded and parsed_cfg is not None:
                    try:
                        os.makedirs(os.path.dirname(webui_dest_path), exist_ok=True)
                        with open(webui_dest_path, "w", encoding="utf-8") as f_out:
                            json.dump(parsed_cfg, f_out, indent=2, ensure_ascii=False)
                        self.webui_config = parsed_cfg
                        self.webui_config_path = webui_dest_path
                        imported_files_count += 1
                        log_sync(f"Configuration WebUI enregistrée proprement dans :\n{webui_dest_path}", "SUCCESS")
                    except Exception as e:
                        log_sync(f"Erreur d'écriture dans {webui_dest_path}: {e}", "ERROR")
                else:
                    log_sync(f"Attention: Impossible de trouver config.json sur le dépôt {webui_repo}.", "WARN")

        # ==========================================
        # 3. POST-SYNC REFRESH & UI UPDATE
        # ==========================================
        log_sync("Rechargement et indexation des données locales...", "INFO")
        self.load_local_data()
        self.load_pegasus_data()

        self.root.after(0, self._on_sync_completed_ui, imported_files_count, repo_type)

    def _on_sync_completed_ui(self, count, repo_type):
        self.config["hasSynchronized"] = True
        self.save_preferences()

        if hasattr(self, "lbl_user_header") and self.lbl_user_header.winfo_exists():
            user_display = self.config.get("githubUser")
            if not user_display and self.config.get("coreosRepo") and "/" in self.config.get("coreosRepo"):
                user_display = self.config.get("coreosRepo").split("/")[0]
            self.lbl_user_header.configure(text=f"🐙 {user_display or 'Configuré'}")

        total_opml = sum(len(v) for v in self.feed_data.values())
        msg = f"Synchronisation terminée !\n\n• {count} fichier(s) importé(s) ou mis à jour\n• {total_opml} flux OPML chargés au total\n• {len(self.pegasus_items_list)} paquets Pegasus détectés"
        self.log(f"Synchronisation terminée: {count} fichiers importés, {total_opml} flux OPML actifs.", "SUCCESS")

        if hasattr(self, "_post_sync_action") and self._post_sync_action:
            action = self._post_sync_action
            self._post_sync_action = None
            action()
            return

        if hasattr(self, "files_listbox") and self.files_listbox.winfo_exists():
            self.refresh_opml_files_list()
        if self.current_section == "coreos" and self.active_tab_key == "sync":
            self.show_sync_view()
        elif self.current_section == "home":
            self.show_dashboard_view()

        messagebox.showinfo("Synchronisation Réussie", msg)


def main():
    root = tk.Tk()
    app = EvoXManagerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
