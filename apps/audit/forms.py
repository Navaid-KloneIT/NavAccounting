from django import forms
from django.forms import inlineformset_factory

from .models import (
    SOXControl, SOXControlTest,
    SoDRule, SoDViolation,
    AccessPolicy, AccessReview, AccessReviewItem,
    ChangeRequest, ChangeApproval,
    ExceptionRule, AuditException,
    DocumentCategory, Document,
)


# ──────────────────────────────────────────────
# SOX Controls
# ──────────────────────────────────────────────
class SOXControlForm(forms.ModelForm):
    class Meta:
        model = SOXControl
        exclude = ['tenant', 'created_at', 'updated_at', 'control_number', 'last_tested_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'control_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'owner': forms.Select(attrs={'class': 'form-select'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'risk_level': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class SOXControlTestForm(forms.ModelForm):
    class Meta:
        model = SOXControlTest
        exclude = ['tenant', 'created_at', 'updated_at', 'test_number', 'control']
        widgets = {
            'test_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tested_by': forms.Select(attrs={'class': 'form-select'}),
            'test_type': forms.Select(attrs={'class': 'form-select'}),
            'result': forms.Select(attrs={'class': 'form-select'}),
            'sample_size': forms.NumberInput(attrs={'class': 'form-control'}),
            'exceptions_found': forms.NumberInput(attrs={'class': 'form-control'}),
            'conclusion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


SOXControlTestFormSet = inlineformset_factory(
    SOXControl, SOXControlTest,
    form=SOXControlTestForm,
    extra=1, can_delete=True,
)


# ──────────────────────────────────────────────
# Segregation of Duties
# ──────────────────────────────────────────────
class SoDRuleForm(forms.ModelForm):
    class Meta:
        model = SoDRule
        exclude = ['tenant', 'created_at', 'updated_at', 'rule_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'conflicting_role_1': forms.TextInput(attrs={'class': 'form-control'}),
            'conflicting_role_2': forms.TextInput(attrs={'class': 'form-control'}),
            'risk_level': forms.Select(attrs={'class': 'form-select'}),
            'enforcement': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class SoDViolationForm(forms.ModelForm):
    class Meta:
        model = SoDViolation
        exclude = ['tenant', 'created_at', 'updated_at', 'violation_number',
                    'resolved_by', 'resolved_at']
        widgets = {
            'rule': forms.Select(attrs={'class': 'form-select'}),
            'user': forms.Select(attrs={'class': 'form-select'}),
            'role_1_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role_2_name': forms.TextInput(attrs={'class': 'form-control'}),
            'detected_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'mitigating_control': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['rule'].queryset = SoDRule.unscoped.filter(tenant=tenant)


# ──────────────────────────────────────────────
# Access Controls
# ──────────────────────────────────────────────
class AccessPolicyForm(forms.ModelForm):
    class Meta:
        model = AccessPolicy
        exclude = ['tenant', 'created_at', 'updated_at', 'policy_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'policy_type': forms.Select(attrs={'class': 'form-select'}),
            'target_model': forms.TextInput(attrs={'class': 'form-control'}),
            'target_field': forms.TextInput(attrs={'class': 'form-control'}),
            'access_level': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            from apps.roles.models import Role
            self.fields['role'].queryset = Role.unscoped.filter(tenant=tenant)


class AccessReviewForm(forms.ModelForm):
    class Meta:
        model = AccessReview
        exclude = ['tenant', 'created_at', 'updated_at', 'review_number', 'findings_count']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'review_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reviewer': forms.Select(attrs={'class': 'form-select'}),
            'scope': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class AccessReviewItemForm(forms.ModelForm):
    class Meta:
        model = AccessReviewItem
        exclude = ['tenant', 'created_at', 'updated_at', 'item_number', 'review']
        widgets = {
            'policy': forms.Select(attrs={'class': 'form-select'}),
            'user': forms.Select(attrs={'class': 'form-select'}),
            'current_access': forms.TextInput(attrs={'class': 'form-control'}),
            'recommended_action': forms.Select(attrs={'class': 'form-select'}),
            'reviewer_decision': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['policy'].queryset = AccessPolicy.unscoped.filter(tenant=tenant)


AccessReviewItemFormSet = inlineformset_factory(
    AccessReview, AccessReviewItem,
    form=AccessReviewItemForm,
    extra=1, can_delete=True,
)


# ──────────────────────────────────────────────
# Change Management
# ──────────────────────────────────────────────
class ChangeRequestForm(forms.ModelForm):
    class Meta:
        model = ChangeRequest
        exclude = ['tenant', 'created_at', 'updated_at', 'request_number',
                    'requested_by', 'approved_by', 'approved_at',
                    'implemented_by', 'implemented_at', 'rollback_data']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'change_type': forms.Select(attrs={'class': 'form-select'}),
            'target_model': forms.TextInput(attrs={'class': 'form-control'}),
            'target_record_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ChangeApprovalForm(forms.ModelForm):
    class Meta:
        model = ChangeApproval
        exclude = ['tenant', 'created_at', 'updated_at', 'approval_number',
                    'change_request', 'decided_at']
        widgets = {
            'approver': forms.Select(attrs={'class': 'form-select'}),
            'decision': forms.Select(attrs={'class': 'form-select'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


ChangeApprovalFormSet = inlineformset_factory(
    ChangeRequest, ChangeApproval,
    form=ChangeApprovalForm,
    extra=1, can_delete=True,
)


# ──────────────────────────────────────────────
# Exception Reporting
# ──────────────────────────────────────────────
class ExceptionRuleForm(forms.ModelForm):
    class Meta:
        model = ExceptionRule
        exclude = ['tenant', 'created_at', 'updated_at', 'rule_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'rule_type': forms.Select(attrs={'class': 'form-select'}),
            'target_model': forms.TextInput(attrs={'class': 'form-control'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class AuditExceptionForm(forms.ModelForm):
    class Meta:
        model = AuditException
        exclude = ['tenant', 'created_at', 'updated_at', 'exception_number',
                    'resolved_by', 'resolved_at']
        widgets = {
            'rule': forms.Select(attrs={'class': 'form-select'}),
            'detected_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'record_model': forms.TextInput(attrs={'class': 'form-control'}),
            'record_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'resolution_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['rule'].queryset = ExceptionRule.unscoped.filter(tenant=tenant)


# ──────────────────────────────────────────────
# Document Management
# ──────────────────────────────────────────────
class DocumentCategoryForm(forms.ModelForm):
    class Meta:
        model = DocumentCategory
        exclude = ['tenant', 'created_at', 'updated_at', 'category_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        exclude = ['tenant', 'created_at', 'updated_at', 'document_number',
                    'uploaded_by', 'file_name', 'file_size', 'file_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'linked_model': forms.TextInput(attrs={'class': 'form-control'}),
            'linked_record_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'version': forms.NumberInput(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['category'].queryset = DocumentCategory.unscoped.filter(
                tenant=tenant, is_active=True
            )
