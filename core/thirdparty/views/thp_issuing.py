# from django.shortcuts import render, get_object_or_404
from accounts.models import ProfileThpIssuingAgent 
from ..forms import EditIssuingAgentForm
from django.views.generic import (
    TemplateView,RedirectView,ListView,DetailView,
    FormView,CreateView,UpdateView,DeleteView,)
from django.contrib.auth.mixins import (
    LoginRequiredMixin,PermissionRequiredMixin,)

from accounts.access_control import TeamAccessMixin

class agentsList(TeamAccessMixin,TemplateView):
    # context_object_name = "agents"
    view_name = "agentsList"
    template_name = "thp/thp_issuing_agent_list.html"

class ThpIssuingAgentsList(TeamAccessMixin,LoginRequiredMixin,TemplateView,):
    view_name = "ThpIssuingAgentsList"
    template_name = "thp/ThpIssuingAgentsList.html"

# class ThpIssuingAgentsDetail(LoginRequiredMixin,TemplateView,):
#     template_name = "thp/ThpIssuingAgentsDetail.html"

class ThpIssuingDashBoards(TeamAccessMixin,TemplateView,):
    view_name = "ThpIssuingDashBoards"
    template_name = "thp/ThpIssuingDashBoards.html"


class EditIssuingAgent(TeamAccessMixin,UpdateView):
    view_name = "EditIssuingAgent"
    model = ProfileThpIssuingAgent
    form_class = EditIssuingAgentForm
    template_name = 'thp/ThpIssuingAgentsDetail.html'
    success_url = '/thirdparty/ThpIssuingAgentsList/'
# test_ThpSupervizer

