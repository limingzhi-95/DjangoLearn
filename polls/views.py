from django.http import HttpResponse
from .models import Question
from .forms import AddForm
from django.http.request import QueryDict
from django.forms.utils import ErrorList


def index(request):
    data = request.POST
    image = request.FILES
    _form = AddForm(data, files=image)
    if _form.is_valid():
        print('***')

    error_data = _form.errors.as_json()
    print(error_data)
    print(_form.as_table())
    print(data)

    print(image)
    return HttpResponse('success')


def detail(request, question_id):
    return HttpResponse("You're looking at question %s." % question_id)


def results(request, question_id):
    response = "You're looking at the results of question %s."
    return HttpResponse(response % question_id)


def vote(request, question_id):
    return HttpResponse("You're voting on question %s." % question_id)
