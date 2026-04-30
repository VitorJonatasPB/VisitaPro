from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.contrib.auth.models import Group
from .models import Empresa, Visita, Funcionario, Disciplina, PerguntaRelatorio
from .data_sources import get_data_source_choices

User = get_user_model()


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["name", "permissions"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nome do Grupo de Acesso",
                }
            ),
            "permissions": forms.SelectMultiple(
                attrs={"class": "form-select", "style": "height: 250px;"}
            ),
        }


class AssessorForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=False,
        help_text="Deixe em branco para não alterar",
    )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "foto",
            "cor_mapa",
            "is_active",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "foto": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
            "cor_mapa": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "type": "color",
                    "style": "height: 50px; padding: 4px; cursor: pointer;",
                    "title": "Escolha a cor do pin no mapa",
                }
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cor_mapa"].help_text = ""

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_assessor = True
        if self.cleaned_data.get("password"):
            user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class AdminUserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=False,
        help_text="Deixe em branco para não alterar",
    )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "is_admin",
            "groups",
            "user_permissions",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_admin": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "groups": forms.SelectMultiple(
                attrs={"class": "form-select", "style": "height: 150px;"}
            ),
            "user_permissions": forms.SelectMultiple(
                attrs={"class": "form-select", "style": "height: 150px;"}
            ),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        if user.is_admin:
            user.is_staff = True
        if self.cleaned_data.get("password"):
            user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            self.save_m2m()  # Importante salvar grants m2m
        return user


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = [
            "nome",
            "cnpj_cpf",
            "telefone",
            "email",
            "cep",
            "rua",
            "numero",
            "bairro",
            "cidade",
            "estado",
            "assessor",
            "status",
            "assessores_autorizados",
            "latitude",
            "longitude",
        ]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "cnpj_cpf": forms.TextInput(attrs={"class": "form-control cnpj-cpf-mask"}),
            "telefone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "assessor": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "assessores_autorizados": forms.SelectMultiple(
                attrs={"class": "form-select"}
            ),
            "cep": forms.TextInput(attrs={"class": "form-control cep-mask"}),
            "rua": forms.TextInput(attrs={"class": "form-control"}),
            "numero": forms.TextInput(attrs={"class": "form-control"}),
            "bairro": forms.TextInput(attrs={"class": "form-control"}),
            "cidade": forms.TextInput(attrs={"class": "form-control"}),
            "estado": forms.TextInput(attrs={"class": "form-control", "maxlength": "2"}),
            "latitude": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ex: -23.550520"}
            ),
            "longitude": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ex: -46.633308"}
            ),
        }


class VisitaForm(forms.ModelForm):
    class Meta:
        model = Visita
        fields = ["empresa", "assessor", "data", "horario", "status", "observacoes"]
        widgets = {
            "empresa": forms.Select(attrs={"class": "form-select", "id": "id_empresa"}),
            "assessor": forms.Select(
                attrs={"class": "form-select", "id": "id_assessor"}
            ),
            "data": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "horario": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "observacoes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        user = self.user
        super(VisitaForm, self).__init__(*args, **kwargs)
        
        # O formulário de agenda deve permitir apenas o status "agendada"
        self.fields["status"].choices = [("agendada", "Agendada")]
        
        if user:
            if not getattr(user, "is_admin", False) and not user.is_superuser:
                self.fields["empresa"].queryset = Empresa.objects.filter(
                    Q(assessor=user) | Q(assessores_autorizados=user)
                ).distinct()
                if "assessor" in self.fields:
                    del self.fields["assessor"]
            else:
                # Admin vê todos os assessores marcados como assessor
                self.fields["assessor"].queryset = User.objects.filter(
                    is_assessor=True
                )

    def clean_data(self):
        data = self.cleaned_data.get("data")
        if data and self.user:
            if not getattr(self.user, "is_admin", False) and not self.user.is_superuser:
                from django.utils import timezone
                from django.core.exceptions import ValidationError

                hoje = timezone.now().date()
                meses_diff = (data.year - hoje.year) * 12 + data.month - hoje.month

                if meses_diff != 1:
                    raise ValidationError(
                        "Você só pode agendar visitas exatamente para o próximo mês."
                    )
        return data


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "widget",
            MultipleFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                    "capture": "environment",
                    "multiple": True,
                }
            ),
        )
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


class RelatorioVisitaForm(forms.ModelForm):
    fotos = MultipleFileField(required=False)

    class Meta:
        model = Visita
        fields = [
            "status",
            "contatoes_atendidos",
            "relatorio",
            "nome_responsavel",
            "assinatura",
            "checkin_time",
            "checkin_lat",
            "checkin_lng",
            "checkout_time",
            "checkout_lat",
            "checkout_lng",
        ]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select form-select-lg mb-3"}),
            "contatoes_atendidos": forms.SelectMultiple(
                attrs={
                    "class": "form-select",
                    "data-placeholder": "Selecione os contatoes atendidos...",
                }
            ),
            "relatorio": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Descreva detalhadamente o relato e atividades da visita...",
                }
            ),
            "nome_responsavel": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nome do Responsável"}
            ),
            "assinatura": forms.HiddenInput(),
            "checkin_time": forms.HiddenInput(),
            "checkin_lat": forms.HiddenInput(),
            "checkin_lng": forms.HiddenInput(),
            "checkout_time": forms.HiddenInput(),
            "checkout_lat": forms.HiddenInput(),
            "checkout_lng": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super(RelatorioVisitaForm, self).__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, "empresa"):
            self.fields["contatoes_atendidos"].queryset = Funcionario.objects.filter(
                empresa=self.instance.empresa
            ).order_by("nome")


class DisciplinaForm(forms.ModelForm):
    class Meta:
        model = Disciplina
        fields = ["nome"]
        widgets = {
            "nome": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nome da Disciplina"}
            )
        }


class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = [
            "nome",
            "empresa",
            "departamento",
            "cargo",
            "telefone",
            "email",
        ]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "empresa": forms.Select(attrs={"class": "form-select"}),
            "departamento": forms.TextInput(attrs={"class": "form-control"}),
            "cargo": forms.TextInput(attrs={"class": "form-control"}),
            "telefone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }


class PerguntaRelatorioForm(forms.ModelForm):
    class Meta:
        model = PerguntaRelatorio
        fields = ["texto", "tipo_resposta", "fonte_dados", "opcoes_resposta", "ativa"]
        widgets = {
            "texto": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex: Como estava a condição do local?",
                }
            ),
            "tipo_resposta": forms.Select(
                attrs={"class": "form-select", "id": "id_tipo_resposta"}
            ),
            "fonte_dados": forms.Select(
                attrs={"class": "form-select", "id": "id_fonte_dados"}
            ),
            "opcoes_resposta": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "id": "id_opcoes_resposta",
                    "placeholder": "Ex: Opção 1, Opção 2, Opção 3",
                }
            ),
            "ativa": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Popula as choices de fonte_dados dinamicamente do registry
        self.fields["fonte_dados"].widget.choices = get_data_source_choices()
        self.fields["fonte_dados"].required = False
