from django.shortcuts import render
# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, NoReverseMatch
from django.views.generic import TemplateView
from .access_control import TeamAccessControl


VIEW_REGISTRY = {
    "ThpIssuingAgentsList": {"url_name": "thirdparty:ThpIssuingAgentsList", "label": "لیست نیروهای صدور"},
    "ThpIssuingDashBoards": {"url_name": "thirdparty:ThpIssuingDashBoards", "label": "داشبورد صدور"},   
}


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "registration/UrlsMap.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_superuser:
            allowed_views = TeamAccessControl.get_all_views()
        elif user.team:
            allowed_views = TeamAccessControl.get_allowed_views(user.team.name)
        else:
            allowed_views = []

        links = []
        for view_name in allowed_views:
            meta = VIEW_REGISTRY.get(view_name)
            if not meta:
                continue  # اگه view ثبت نشده باشه رد می‌شه، به جای کرش
            try:
                url = reverse(meta["url_name"])
            except NoReverseMatch:
                continue
            links.append({"label": meta["label"], "url": url})

        context["links"] = links
        return context
