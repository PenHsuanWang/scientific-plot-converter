import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

project = 'FabPlot-CLI'
copyright = '2026'
author = 'Ben Wang'
release = '0.1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

autodoc_default_options = {
    'members': True,
    'undoc-members': False,
    'show-inheritance': True,
}
napoleon_google_docstring = False
napoleon_numpy_docstring = False

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
html_theme = 'alabaster'
