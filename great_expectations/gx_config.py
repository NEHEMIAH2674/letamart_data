"""
great_expectations/gx_config.py
---------------------------------
Configures Great Expectations context using the GX 1.18 Fluent API.
Run once to set up the project.

Usage:
    python great_expectations/gx_config.py
"""

import great_expectations as gx

def setup_gx_context():
    # GX 1.18 uses ephemeral context — no file system required
    context = gx.get_context(mode="ephemeral")
    print(f"✅ GX context created — version: {gx.__version__}")
    print(f"✅ Context type: {type(context).__name__}")
    return context

if __name__ == "__main__":
    setup_gx_context()
