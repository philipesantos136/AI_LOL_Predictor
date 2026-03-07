"""
charts/__init__.py — Re-exporta a API pública do pacote.
Mantém compatibilidade: `from interface.charts import generate_charts`
"""

from .renderer import generate_charts
from .html_helpers import INSIGHTS_CSS

__all__ = ["generate_charts", "INSIGHTS_CSS"]
