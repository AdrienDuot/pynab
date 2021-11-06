from django.shortcuts import render
from django.views.generic import TemplateView
import datetime

from .models import alarm
from .nab8balld import Nab8Balld


class SettingsView(TemplateView):
    template_name = "nab8balld/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["alarm"] = alarm.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        alarm = alarm.load()
        alarm.objects.create(title=request.POST["title"], date=request.POST["date"])
        alarm.save()
        Nab8Balld.signal_daemon()
        context = super().get_context_data(**kwargs)
        context["alarm"] = alarm
        return render(request, SettingsView.template_name, context=context)
