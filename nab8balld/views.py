from django.shortcuts import render
from django.views.generic import TemplateView
import datetime

from .models import config
from .nab8balld import Nab8Balld


class SettingsView(TemplateView):
    template_name = "nab8balld/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["config"] = config.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        config = config.load()
        config.objects.create(title=request.POST["title"], date=request.POST["date"])
        config.save()
        Nab8Balld.signal_daemon()
        context = super().get_context_data(**kwargs)
        context["config"] = config
        return render(request, SettingsView.template_name, context=context)
