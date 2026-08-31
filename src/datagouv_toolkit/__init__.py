"""Outils pour explorer, télécharger, auditer et analyser data.gouv.fr."""

import sys

from . import normalize as normalize

# Compatibilité interne pendant la migration du layout historique plat.
sys.modules.setdefault("normalize", normalize)
