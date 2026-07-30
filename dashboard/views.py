import json, os
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.conf import settings
from .services.analytics import build_payload
from .services.map_service import create_school_map

def home(request): return redirect("tables")
def health(request): return JsonResponse({"status":"ok"})

def tables_view(request):
    payload=build_payload()
    return render(request,"dashboard/tables.html",{"data":payload,"active":"tables"})

def dashboards_view(request):
    payload=build_payload()
    chart={
        "levels":payload["levels"],
        "income":payload["tables"]["income_group"]["rows"],
        "forest":[r for r in payload["associations"] if not r["reference"] and r["adjusted_rp"]==r["adjusted_rp"]],
    }
    return render(request,"dashboard/dashboards.html",{"data":payload,"chart_json":json.dumps(chart,ensure_ascii=False),"active":"dashboards"})

def map_view(request):
    payload=build_payload(); map_html,school_rows=create_school_map(payload["schools"])
    return render(request,"dashboard/map.html",{"data":payload,"map_html":map_html,"school_rows":school_rows,"active":"map"})

def api_metrics(request): return JsonResponse(build_payload())

@require_POST
def refresh_api(request):
    expected=settings.DATA_REFRESH_TOKEN
    if not expected or request.headers.get("X-Refresh-Token")!=expected: return HttpResponseForbidden("Token inválido")
    return JsonResponse(build_payload(force=True))
