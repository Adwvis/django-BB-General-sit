import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

from thirdparty.tasks import t_test , check_active_assignments , thp_issuing_assignment, thp_issuing_assignment_bind

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(2, t_test.s(),name="t_test")
    # sender.add_periodic_task(5, check_active_assignments.s(),name="check_active_assignments")
    sender.add_periodic_task(5, thp_issuing_assignment.s(),name="thp_issuing_assignment")

# @app.on_after_configure.connect
# def kickstart_tasks(sender, **kwargs):
#     thp_issuing_assignment_bind.delay()




