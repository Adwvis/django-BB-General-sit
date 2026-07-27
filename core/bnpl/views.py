from django.shortcuts import render
from django.views.generic import (
    TemplateView,RedirectView,ListView,DetailView,
    FormView,CreateView,UpdateView,DeleteView,)
from django.contrib.auth.mixins import (
    LoginRequiredMixin,PermissionRequiredMixin,)
from accounts.access_control import TeamAccessMixin

from bnpl.models import BnplAccount
from bnpl.forms import EditBnplAccountForm
# Create your views here.
class BnplAccountListView(TeamAccessMixin,LoginRequiredMixin,TemplateView,):
    view_name = "BnplAccountListView"
    template_name = "bnpl/BnplAccountList.html"


class EditBnplAccount(TeamAccessMixin,LoginRequiredMixin,UpdateView,):
    view_name = "EditBnplAccount"
    model = BnplAccount
    form_class = EditBnplAccountForm
    template_name = 'bnpl/EditBnplAccount.html'
    success_url = '/bnpl/BnplAccountListView/'



