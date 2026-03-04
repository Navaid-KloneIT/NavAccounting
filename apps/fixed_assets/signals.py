"""Extend audit trail to cover Fixed Assets models."""
from apps.general_ledger.signals import AUDITED_MODELS

from .models import Asset, AssetAcquisition, AssetDisposal, AssetTransfer, DepreciationEntry


FA_AUDITED_MODELS = [Asset, AssetAcquisition, AssetDisposal, AssetTransfer, DepreciationEntry]

# Register FA models into the shared AUDITED_MODELS list
for model in FA_AUDITED_MODELS:
    if model not in AUDITED_MODELS:
        AUDITED_MODELS.append(model)
