import datetime

from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView

from .models import Config
from .nabposologied import Nabposologied


class SettingsView(TemplateView):
    template_name = "nabposologied/settings.html"

    def get_context_data(self, **kwargs):
        # on charge les donnees depuis la base de données
        context = super().get_context_data(**kwargs)
        context["config"] = Config.load()
        return context

    def post(self, request, *args, **kwargs):
        # quand on reçoit une nouvelle config (via interface)
        config = Config.load()
        if "index_posologie" in request.POST:
            index_posologie = request.POST["index_posologie"]
            config.index_posologie = index_posologie
        if "visual_posologie" in request.POST:
            visual_posologie = request.POST["visual_posologie"]
            config.visual_posologie = visual_posologie
        config.save()
        Nabposologied.signal_daemon()
        context = self.get_context_data(**kwargs)
        return render(request, SettingsView.template_name, context=context)

    def put(self, request, *args, **kwargs):
        # quand on clique sur le bouton de l'intervaface pour jouer tout
        # de suite
        config = Config.load()
        config.next_performance_date = datetime.datetime.now(
            datetime.timezone.utc
        )
        config.next_performance_type = "today"
        config.save()
        Nabposologied.signal_daemon()
        return JsonResponse({"status": "ok"})
