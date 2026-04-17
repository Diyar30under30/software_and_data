# =====================================================================
# utils/helpers.py  —  Shared UI utilities
# =====================================================================
# WHY THIS FILE EXISTS:
#   In the original project, the same PlaceholderEntry class was
#   copy-pasted into four different files (students.py, courses.py,
#   registrations.py, attendance.py).  Duplicated code is a maintenance
#   problem: if you want to change how placeholder text looks, you have
#   to edit four places and hope you don't miss one.
#
#   This file centralises:
#     1. AppTheme  — all colors and fonts in one place.
#     2. PlaceholderEntry — one shared, improved version of the class.
#     3. Helper functions — styled_button(), make_window(), make_header()
#        so every management screen looks consistent with zero extra effort.
# =====================================================================

import tkinter as tk
from tkinter import ttk


# ─────────────────────────────────────────────────────────────────────
# 1. THEME CONSTANTS
# ─────────────────────────────────────────────────────────────────────
# All visual values live here.  To redesign the entire app, only
# edit this class — nothing else needs to change.

class AppTheme:
    # Backgrounds
    BG        = "#EFF3F8"   # Light blue-grey: main window background
    PANEL     = "#1B2A4A"   # Dark navy: header bars and section labels
    ENTRY_BG  = "#FFFFFF"   # Pure white: inside text fields

    # Action colors
    PRIMARY   = "#2563EB"   # Blue  – Add / Save / Filter buttons
    DANGER    = "#DC2626"   # Red   – Delete buttons
    SUCCESS   = "#16A34A"   # Green – Confirm / success states
    NEUTRAL   = "#64748B"   # Grey  – Secondary / Exit buttons
    WARNING   = "#D97706"   # Amber – Update buttons

    # Text colors
    TEXT         = "#1E293B"   # Near-black: labels and table cells
    MUTED        = "#94A3B8"   # Slate-grey: placeholder text
    HEADER_TEXT  = "#FFFFFF"   # White: text on dark panel backgrounds

    # Table / Treeview
    ROW_ODD      = "#FFFFFF"   # Normal row background
    ROW_EVEN     = "#DBEAFE"   # Subtle blue tint for alternating rows
    ROW_SELECTED = "#2563EB"   # Primary blue when a row is highlighted

    # Borders
    BORDER    = "#CBD5E1"   # Light grey outline around entry fields

    # ── Fonts ──────────────────────────────────────────────────────
    # "Segoe UI" is the default Windows system font; it degrades
    # gracefully to the OS default on macOS / Linux.
    FONT_HEADING = ("Segoe UI", 14, "bold")   # Window / section titles
    FONT_LABEL   = ("Segoe UI", 11)           # Form field labels
    FONT_ENTRY   = ("Segoe UI", 11)           # Text inside input fields
    FONT_BUTTON  = ("Segoe UI", 10, "bold")   # Button labels
    FONT_TABLE   = ("Segoe UI", 10)           # Treeview cell text
    FONT_TABLE_H = ("Segoe UI", 10, "bold")   # Treeview column headers
    FONT_SMALL   = ("Segoe UI", 9)            # Status bar / pagination

    # ── Sizing ─────────────────────────────────────────────────────
    PAD    = 12   # Standard outer padding (pixels)
    IPAD   = 6    # Inner padding inside widgets
    BTN_W  = 14   # Uniform button width (character units)
    ENTRY_W = 22  # Uniform entry field width (character units)


# ─────────────────────────────────────────────────────────────────────
# 2. TREEVIEW STYLING
# ─────────────────────────────────────────────────────────────────────

def apply_treeview_style(style_name="Custom.Treeview"):
    """
    Configures ttk.Style for all Treeview tables.

    Parameters
    ----------
    style_name : str
        The name you'll pass to Treeview(style=style_name).
        Using a custom name avoids overriding the global "Treeview".

    Returns
    -------
    str
        The style_name, so callers can write:
            tree = ttk.Treeview(parent, style=apply_treeview_style())
    """
    style = ttk.Style()
    style.theme_use("clam")   # "clam" allows background color overrides

    style.configure(
        style_name,
        background=AppTheme.ROW_ODD,        # Normal row background
        foreground=AppTheme.TEXT,           # Cell text color
        fieldbackground=AppTheme.ROW_ODD,   # The inner scrollable area bg
        font=AppTheme.FONT_TABLE,
        rowheight=28,                       # Taller rows are easier to click
        borderwidth=0,
    )
    style.configure(
        f"{style_name}.Heading",            # Column header row
        background=AppTheme.PANEL,          # Dark navy header
        foreground=AppTheme.HEADER_TEXT,    # White header text
        font=AppTheme.FONT_TABLE_H,
        relief="flat",                      # No 3-D border on headers
    )
    style.map(
        style_name,
        # Change background and text color when a row is selected
        background=[("selected", AppTheme.ROW_SELECTED)],
        foreground=[("selected", AppTheme.HEADER_TEXT)],
    )
    return style_name


# ─────────────────────────────────────────────────────────────────────
# 3. WINDOW FACTORY
# ─────────────────────────────────────────────────────────────────────

def make_window(title, width=720, height=580):
    """
    Creates a consistently styled Toplevel window.

    Previously every management screen duplicated tk.Toplevel() + title()
    + configure(bg=...) + geometry(...).  This factory does it all in one.

    Parameters
    ----------
    title  : str   Window title bar text.
    width  : int   Initial window width in pixels.
    height : int   Initial window height in pixels.
    """
    win = tk.Toplevel()
    win.title(title)
    win.geometry(f"{width}x{height}")   # Start at a sensible size
    win.configure(bg=AppTheme.BG)
    win.resizable(True, True)           # User can resize if needed
    return win


def make_header(parent, title):
    """
    Adds a dark navy header bar with a centered white title.
    Called at the top of every management window for brand consistency.

    Parameters
    ----------
    parent : tk widget   The window or frame to attach the header to.
    title  : str         The text displayed in the header.
    """
    header = tk.Frame(parent, bg=AppTheme.PANEL, pady=12)
    header.pack(fill="x")   # Stretch across the full width of the window
    tk.Label(
        header,
        text=title,
        font=AppTheme.FONT_HEADING,
        bg=AppTheme.PANEL,
        fg=AppTheme.HEADER_TEXT,
    ).pack(padx=AppTheme.PAD)
    return header


def make_separator(parent):
    """Thin horizontal rule — visually separates form sections."""
    sep = tk.Frame(parent, bg=AppTheme.BORDER, height=1)
    sep.pack(fill="x", padx=AppTheme.PAD, pady=(4, 8))
    return sep


# ─────────────────────────────────────────────────────────────────────
# 4. BUTTON FACTORY
# ─────────────────────────────────────────────────────────────────────

def styled_button(parent, text, command, style="primary", width=None, **kwargs):
    """
    Returns a pre-styled tk.Button so callers never need to repeat
    bg/fg/font/relief kwargs on every single button.

    Parameters
    ----------
    parent  : tk widget   Parent container.
    text    : str         Button label.
    command : callable    The function to call when clicked.
    style   : str         One of "primary", "danger", "success",
                          "warning", "neutral".
    width   : int|None    Override the default BTN_W character width.

    Why flat relief + hand2 cursor?
      - relief="flat"  removes the old Windows 95 bevelled look.
      - cursor="hand2" signals interactivity (pointer finger), which
        is a standard web convention users expect.
    """
    color_map = {
        "primary": AppTheme.PRIMARY,
        "danger":  AppTheme.DANGER,
        "success": AppTheme.SUCCESS,
        "warning": AppTheme.WARNING,
        "neutral": AppTheme.NEUTRAL,
    }
    bg = color_map.get(style, AppTheme.PRIMARY)
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg="#FFFFFF",                   # White label on all colored buttons
        font=AppTheme.FONT_BUTTON,
        relief="flat",                  # Modern flat look
        cursor="hand2",                 # Pointer finger cursor on hover
        activebackground=bg,            # Keep color when mouse is held down
        activeforeground="#FFFFFF",
        padx=AppTheme.IPAD,
        pady=AppTheme.IPAD,
        width=width or AppTheme.BTN_W,
        **kwargs,
    )
    return btn


def labeled_entry(parent, label_text, row, column=0, show=None):
    """
    Creates a label + styled entry pair in a grid layout.
    Returns the Entry widget so the caller can .get() it later.

    Parameters
    ----------
    label_text : str    Text shown to the left of the input.
    row        : int    Grid row index.
    column     : int    Starting grid column (label goes here, entry at +1).
    show       : str    Pass "•" for password masking.
    """
    tk.Label(
        parent,
        text=label_text,
        font=AppTheme.FONT_LABEL,
        bg=AppTheme.BG,
        fg=AppTheme.TEXT,
        anchor="w",
    ).grid(row=row, column=column, sticky="w", padx=(AppTheme.PAD, 6), pady=5)

    entry = tk.Entry(
        parent,
        font=AppTheme.FONT_ENTRY,
        bg=AppTheme.ENTRY_BG,
        fg=AppTheme.TEXT,
        relief="flat",
        highlightthickness=1,
        highlightbackground=AppTheme.BORDER,
        highlightcolor=AppTheme.PRIMARY,   # Blue outline when focused
        width=AppTheme.ENTRY_W,
        show=show or "",
    )
    entry.grid(row=row, column=column + 1, padx=(0, AppTheme.PAD), pady=5)
    return entry


# ─────────────────────────────────────────────────────────────────────
# 5. PLACEHOLDER ENTRY  (single canonical version)
# ─────────────────────────────────────────────────────────────────────

class PlaceholderEntry(tk.Entry):
    """
    A text entry that shows grey hint text when empty, then clears
    it automatically when the user clicks in.

    ORIGINAL PROBLEM:
        This exact class was copy-pasted into students.py, courses.py,
        registrations.py, and attendance.py — four copies of the same
        code.  If a bug existed (and the originals lacked real_value()),
        it had to be fixed in four places.

    IMPROVEMENTS OVER ORIGINAL:
        • Inherits AppTheme styling automatically (no need to pass colors).
        • Adds real_value() — returns "" instead of the placeholder text,
          so callers don't have to compare strings manually.
        • Uses highlightcolor for a focus ring (blue border when active).
    """

    def __init__(self, master=None, placeholder="Enter text here",
                 color=None, **kwargs):
        # Apply default theme styles unless the caller overrides them
        kwargs.setdefault("font",                AppTheme.FONT_ENTRY)
        kwargs.setdefault("bg",                  AppTheme.ENTRY_BG)
        kwargs.setdefault("fg",                  AppTheme.MUTED)
        kwargs.setdefault("relief",              "flat")
        kwargs.setdefault("highlightthickness",  1)
        kwargs.setdefault("highlightbackground", AppTheme.BORDER)
        kwargs.setdefault("highlightcolor",      AppTheme.PRIMARY)

        super().__init__(master, **kwargs)

        self.placeholder       = placeholder
        self.placeholder_color = color or AppTheme.MUTED
        self.default_fg_color  = AppTheme.TEXT

        # Bind focus in/out so placeholder appears/disappears automatically
        self.bind("<FocusIn>",  self._clear_placeholder)
        self.bind("<FocusOut>", self._add_placeholder)

        # Show placeholder immediately on widget creation
        self._add_placeholder()

    def _clear_placeholder(self, event=None):
        """Remove placeholder text and restore normal text color."""
        if self["fg"] == self.placeholder_color and self.get() == self.placeholder:
            self.delete(0, tk.END)
            self["fg"] = self.default_fg_color

    def _add_placeholder(self, event=None):
        """If the field is empty, restore the placeholder text."""
        if not self.get():
            self["fg"] = self.placeholder_color
            self.insert(0, self.placeholder)

    def real_value(self):
        """
        NEW METHOD (not in the original).
        Returns the user's actual input, or "" if only placeholder is shown.

        Usage:
            query = search_entry.real_value()
            if query:
                ...run search...

        Without this, callers had to write:
            val = e.get()
            if val == e.placeholder:
                val = ""
        which is easy to forget and causes subtle filter bugs.
        """
        val = self.get()
        return "" if val == self.placeholder else val
