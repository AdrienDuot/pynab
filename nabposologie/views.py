from django.shortcuts import render
from django.views.generic import TemplateView

from .models import Config
from .nabposologie import Nabposologie


class SettingsView(TemplateView):
    template_name = "nabposologie/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["config"] = Config.load()
        return context

    def post(self, request, *args, **kwargs):
        config = Config.load()
        config.enabled = request.POST["enabled"] == "true"
        config.save()
        Nabposologie.signal_daemon()
        context = super().get_context_data(**kwargs)
        context["config"] = config
        return render(request, SettingsView.template_name, context=context)
