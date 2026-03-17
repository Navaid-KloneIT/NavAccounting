from apps.general_ledger.signals import AUDITED_MODELS

from .models import (
    SOXControl, SoDRule, AccessPolicy, AccessReview,
    ChangeRequest, ExceptionRule,
    DocumentCategory, Document,
)

AC_AUDITED_MODELS = [
    SOXControl, SoDRule, AccessPolicy, AccessReview,
    ChangeRequest, ExceptionRule, DocumentCategory, Document,
]

for model in AC_AUDITED_MODELS:
    if model not in AUDITED_MODELS:
        AUDITED_MODELS.append(model)
