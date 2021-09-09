import os
import sys

_THIS_DIR = os.path.dirname(os.path.realpath(__file__))
_PROJECT_DIR = os.path.normpath(os.path.join(_THIS_DIR, '..'))

# ensure "fitdecode" python package is importable
sys.path.insert(0, _PROJECT_DIR)

# import project's info (name, version, ...)
_ABOUT = {}
with open(os.path.join(_PROJECT_DIR, 'fitdecode', '__meta__.py'),
          mode='r', encoding='utf-8') as f:
    exec(f.read(), _ABOUT)


#-------------------------------------------------------------------------------
#needs_sphinx = '1.0'

project = _ABOUT['__fancy_title__']
copyright = _ABOUT['__copyright__']
author = _ABOUT['__author__']
version = _ABOUT['__version__']
release = _ABOUT['__version__']

extensions = [
    'sphinx.ext.autodoc', 'sphinx.ext.todo', 'sphinx.ext.intersphinx',
    'sphinx.ext.extlinks']

source_suffix = '.rst'
#source_encoding = 'utf-8-sig'

master_doc = 'index'

exclude_patterns = ['_build', '**/.git', '**/.svn']

templates_path = ['_templates']

rst_epilog = """
.. |project| replace:: {title}

.. |version| replace:: **v{version}**

.. |br| raw:: html

    <br />

""".format(
    title=_ABOUT['__fancy_title__'],
    version=_ABOUT['__version__'])

primary_domain = 'py'
default_role = 'any'

#highlight_language = 'python3'
pygments_style = 'sphinx'

# ext.autodoc config
autodoc_member_order = 'bysource'
autodoc_default_flags = ['members', 'undoc-members']

# ext.extlinks config
extlinks = {
    'ghu': ('https://github.com/%s', '@')}

# ext.intersphinx config
intersphinx_mapping = {'python': ('https://docs.python.org/3.6', None)}

# ext.todo config
todo_include_todos = True


html_theme = 'sphinx_rtd_theme'
html_title = _ABOUT['__fancy_title__']
html_short_title = _ABOUT['__fancy_title__']
html_logo = None #'images/logo.jpg'
html_favicon = os.path.join(_THIS_DIR, 'favicon.ico')
# html_static_path = ['_static']
html_show_sourcelink = False
html_show_sphinx = False
html_show_copyright = True
