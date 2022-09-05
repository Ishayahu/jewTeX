from django.shortcuts import render
from pyluach import dates, hebrewcal, parshios
from database.models import *

def index(request):
    today = dates.HebrewDate.today()
    month = today.month_name(hebrew=True)
    print(month)
    actual_parshios = parshios.getparsha_string(today, israel=False, hebrew=True).split(', ')
    print(actual_parshios)
    holidays = set()
    for i in range(1, 31):
        holiday = (today + i).holiday(hebrew=True)
        if holiday:
            holidays.add(holiday)
    print(holidays)
    summaries = set()
    for s in Summary.objects.filter(events__name=month):
        summaries.add(s)
    for p in actual_parshios:
        for s in Summary.objects.filter(events__name=p):
            summaries.add(s)
    for h in holidays:
        for s in Summary.objects.filter(events__name=h):
            summaries.add(s)

    return render(request, 'database/index.html',
                  {'month': month, 'parshios': actual_parshios,
                   'holidays': holidays, 'summaries': summaries}
                  )

def list_by_tag(request, pk):
    t = Tag.objects.get(pk=pk)
    summaries = t.summary_set.all()
    return render(request, 'database/index.html',
                  {'summaries': summaries, 'tag': t}
                  )

def show_by_pk(request, pk):
    s = Summary.objects.get(pk=pk)
    return render(request, 'database/show.html',
                  {'summary': s}
                  )
