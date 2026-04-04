__author__ = "Michael Kushnir"
__version__ = "1.0"

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from config import ConfigManager
from graph_client import GraphClient
from converter_wrapper import Converter
from pathlib import Path
from datetime import datetime
import webbrowser
import threading

def main():
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.load()

    root = tk.Tk()
    root.title("reMarkable → OneNote Sync")
    root.geometry("600x550")
    root.resizable(True, True)

    metadata = {}
    graph = GraphClient(cfg.get("token", ""), cfg.get("email", ""))

    def log(msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_text.configure(state="normal")
        log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
        log_text.configure(state="disabled")
        log_text.see(tk.END)

    def with_spinner(btn, func):
        def runner():
            btn.config(state="disabled", text=f"{btn.cget('text')} ⏳")
            try:
                func()
            finally:
                btn.config(state="normal", text=btn.cget('text').replace(" ⏳", ""))
        threading.Thread(target=runner).start()

    def show_help():
        help_window = tk.Toplevel(root)
        help_window.title("Help - How to Use")
        help_window.geometry("900x800")

        text_frame = tk.Frame(help_window, height=320)
        text_frame.pack(fill="x", padx=10, pady=(0, 0))
        text_frame.pack_propagate(False)

        text_widget = tk.Text(text_frame, wrap="word", font=('Arial', 11), height=16)
        text_widget.pack(fill="x")

        instructions = ("1. Obtain a Microsoft Graph API token from the ")
        text_widget.insert("1.0", instructions)
        link_text = "Microsoft Graph Explorer"
        text_widget.insert("end", link_text)
        text_widget.insert("end",
            "\n2. Enter the token (and optional email) in the fields.\n"
            "3. Click 'Save Configuration'.\n"
            "4. Select desired notebook and section to upload to the new page.\n"
            "5. Select one or more `.rm` files.\n"
            "6. Click 'Convert & Upload' to push the notes to OneNote.\n\n"
            "---\n\n"
            "Disclaimer: This tool is intended for personal testing and educational use only.\n"
            "The Microsoft Graph API is a service provided by Microsoft and subject to its own terms of service and limitations.\n"
            "This open-source tool does not store your data, and your token is cached locally on your machine.\n"
            "If you encounter API-related issues, please consult Microsoft's documentation or community forums.\n"
        )
        start_idx = "1." + str(len(instructions))
        end_idx = "1." + str(len(instructions) + len(link_text))
        text_widget.tag_add("hyperlink", start_idx, end_idx)
        text_widget.tag_config("hyperlink", foreground="blue", underline=True)
        text_widget.tag_bind("hyperlink", "<Button-1>",
            lambda e: webbrowser.open_new("https://developer.microsoft.com/en-us/graph/graph-explorer"))
        text_widget.config(state="disabled")

        try:
            photo = tk.PhotoImage(file='assets/copy_token_screenshot.png')
            img_label = tk.Label(help_window, image=photo)
            img_label.image = photo
            img_label.pack(pady=(4, 0))
        except Exception:
            pass

    menubar = tk.Menu(root)
    helpmenu = tk.Menu(menubar, tearoff=0)
    helpmenu.add_command(label="Usage Guide", command=show_help)
    menubar.add_cascade(label="Help", menu=helpmenu)
    root.config(menu=menubar)

    # Config Frame
    grp_cfg = tk.LabelFrame(root, text="Graph API Configuration")
    tk.Label(grp_cfg, text="Graph API Token:").grid(row=0, column=0, sticky="w")
    token_var = tk.StringVar(value=cfg.get("token", ""))
    tk.Entry(grp_cfg, textvariable=token_var, width=60).grid(row=0, column=1, sticky='w')

    tk.Label(grp_cfg, text="User Email (optional):").grid(row=1, column=0, sticky="w")
    email_var = tk.StringVar(value=cfg.get("email", ""))
    tk.Entry(grp_cfg, textvariable=email_var, width=60).grid(row=1, column=1, sticky='w')

    def save_token():
        cfg["token"] = token_var.get()
        cfg["email"] = email_var.get()
        cfg_mgr.save(cfg)
        graph.token = cfg["token"]
        graph.email = cfg["email"]
        try:
            notebooks = graph.list_notebooks()
            notebook_cb["values"] = [nb["displayName"] for nb in notebooks]
            metadata["notebooks"] = notebooks
            messagebox.showinfo("Info", "Token saved & notebooks fetched.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    btn_save = tk.Button(grp_cfg, text="Save Configuration", command=lambda: with_spinner(btn_save, save_token))
    btn_save.grid(row=0, column=2, rowspan=2, sticky="ns", padx=(10, 0), pady=(2, 2))

    grp_cfg.columnconfigure(1, weight=1)
    grp_cfg.pack(pady=5, fill=tk.X, padx=10)

    # Convert/Upload Frame
    grp_cnv = tk.LabelFrame(root, text="Convert and Upload to OneNote")

    frm_sel = tk.Frame(grp_cnv)
    tk.Label(frm_sel, text="Notebook:").grid(row=0, column=0, sticky="w")
    notebook_cb = ttk.Combobox(frm_sel, state="readonly", width=30)
    notebook_cb.grid(row=0, column=1, sticky="w")
    tk.Label(frm_sel, text="Section:").grid(row=0, column=2, sticky="w")
    section_cb = ttk.Combobox(frm_sel, state="readonly", width=36)
    section_cb.grid(row=0, column=3, sticky="w")
    frm_sel.pack(pady=5, fill="x")

    def on_notebook_select(event):
        sel = notebook_cb.get()
        for nb in metadata.get("notebooks", []):
            if nb["displayName"] == sel:
                sections = graph.list_sections(nb["id"])
                section_cb["values"] = [s["displayName"] for s in sections]
                metadata["sections"] = sections

    notebook_cb.bind("<<ComboboxSelected>>", on_notebook_select)

    frm_file = tk.Frame(grp_cnv)
    file_paths_var = tk.Variable(value=[])
    tk.Button(frm_file, text="Select .rm File(s)",
              command=lambda: file_paths_var.set(filedialog.askopenfilenames(filetypes=[("rm files", "*.rm")])))\
        .grid(row=0, column=0, sticky="w")
    tk.Label(frm_file, textvariable=file_paths_var, width=60, anchor="w", justify="left", wraplength=400)\
        .grid(row=0, column=1, padx=5, sticky="w")
    btn_convert = tk.Button(frm_file, text="Convert & Upload",
                            command=lambda: with_spinner(btn_convert, convert_upload))
    btn_convert.grid(row=0, column=2, padx=(10, 0), sticky="w")

    frm_file.columnconfigure(1, weight=1)
    frm_file.pack(pady=5, fill="x")
    grp_cnv.pack(padx=10, pady=5, fill=tk.X)

    def convert_upload():
        files = file_paths_var.get()
        if not files:
            messagebox.showerror("Missing info", "Please select at least one file.")
            return
        nb_name = notebook_cb.get()
        sec_name = section_cb.get()
        if not (nb_name and sec_name):
            messagebox.showerror("Missing info", "Please select a notebook and section.")
            return
        nb_id = next(nb["id"] for nb in metadata["notebooks"] if nb["displayName"] == nb_name)
        sec_id = next(s["id"] for s in metadata["sections"] if s["displayName"] == sec_name)
        converter = Converter()
        for fpath in files:
            try:
                log(f"Converting {Path(fpath).name}...")
                xml_path = Path(converter.convert(fpath))
                log(f"Converted to {xml_path.name}")
                html_path = xml_path.with_suffix(".html")
                log(f"Uploading {xml_path.name} to OneNote...")
                graph.upload_page(sec_id, xml_path, html_path)
                log(f"✅ Uploaded {xml_path.name}")
            except Exception as e:
                log(f"❌ Error with {fpath}: {e}")
                messagebox.showerror("Error", f"{Path(fpath).name}: {e}")
        messagebox.showinfo("Done", "All files processed.")

    # Log output with scrollbar
    log_frame = tk.LabelFrame(root, text="Application Logs")
    log_frame.rowconfigure(0, weight=1)
    log_frame.columnconfigure(0, weight=1)
    log_text = tk.Text(log_frame, height=10, width=90, state="disabled")
    scrollbar = tk.Scrollbar(log_frame, command=log_text.yview)
    log_text.configure(yscrollcommand=scrollbar.set)
    log_text.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    if cfg.get("token"):
        try:
            notebooks = graph.list_notebooks()
            notebook_cb["values"] = [nb["displayName"] for nb in notebooks]
            metadata["notebooks"] = notebooks
        except Exception as e:
            log(f"Failed to fetch notebooks: {e}")

    root.mainloop()

if __name__ == "__main__":
    main()
