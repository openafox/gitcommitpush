from gitcommitpush.handlers import setup_handlers
# Jupyter Extension points
def _jupyter_server_extension_paths():
    return [{
        'module': 'gitcommitpush',
    }]

def _jupyter_nbextension_paths():
    return [{
        "section": "notebook",
        "dest": "gitcommitpush",
        "src": "static",
        "require": "gitcommitpush/main"
    }]

def load_jupyter_server_extension(nbapp):
    setup_handlers(nbapp.web_app)
