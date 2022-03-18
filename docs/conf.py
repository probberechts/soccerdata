"""Sphinx configuration."""
project = "soccerdata"
author = "Pieter Robberechts"
copyright = f"2021, {author}"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "nbsphinx",
]
exclude_patterns = ["_build", "**.ipynb_checkpoints"]
autodoc_typehints = "description"
autodoc_member_order = "bysource"

# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
html_logo = "_static/logo2.png"
html_favicon = "_static/favicon.ico"
html_theme_options = {
    "sidebar_hide_name": True,
    "light_css_variables": {
        "color-brand-primary": "#2F3C7E",
        "color-brand-content": "#2F3C7E",
        "color-sidebar-background": "#fdf3f4",
        # "color-api-name": "#7bb5b2",
        # "color-api-pre-name": "#7bb5b2",
    },
    "dark_css_variables": {
        "color-brand-primary": "#7C4DFF",
        "color-brand-content": "#7C4DFF",
    },
}

html_static_path = ["_static"]
html_css_files = ["default.css"]
