from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib.auth.views import redirect_to_login


class TeamAccessControl:
    """نگاشت مرکزی: هر تیم به کدوم صفحات دسترسی داره"""

    PERMISSIONS = {
        "ThpSupervizer": ["ThpIssuingAgentsList", "ThpIssuingDashBoards", "EditIssuingAgent"],
        # "ThpIssunigAgent": [""],
    }

    @classmethod
    def has_access(cls, team_name, view_name):
        return view_name in cls.PERMISSIONS.get(team_name, [])
    
    @classmethod
    def get_allowed_views(cls, team_name):
        return cls.PERMISSIONS.get(team_name, [])

    @classmethod
    def get_all_views(cls):
        """برای سوپریوزر: اجتماع همه‌ی ویوهای موجود در سیستم"""
        views = set()
        for v in cls.PERMISSIONS.values():
            views.update(v)
        return sorted(views)
    

class TeamAccessMixin(UserPassesTestMixin):
    view_name = None  # هر ویو باید مشخص کنه

    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True
        # print(user.team.name)
        if not (user.is_authenticated and user.team):
            return False
        return TeamAccessControl.has_access(user.team.name, self.view_name)
        

    def handle_no_permission(self):
        user = self.request.user

        if not user.is_authenticated:
            # return redirect(reverse_lazy("login"))  # اسم url لاگینت رو بذار
            return redirect_to_login(self.request.get_full_path())
        
        return redirect('accounts:UrlsMap') 
        
        # return redirect(reverse_lazy("home"))


