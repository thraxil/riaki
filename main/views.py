# Create your views here.

from django.contrib.auth.decorators import permission_required
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from models import Page, get_page, create_page, exists, get_tag_pages, get_all_tags
from django.contrib.auth.models import User

class rendered_with(object):
    def __init__(self, template_name):
        self.template_name = template_name

    def __call__(self, func):
        def rendered_func(request, *args, **kwargs):
            items = func(request, *args, **kwargs)
            if type(items) == type({}):
                return render_to_response(self.template_name, items, context_instance=RequestContext(request))
            else:
                return items

        return rendered_func

@rendered_with("main/page.html")
def page(request,slug="index"):
    if request.method == "GET":
        if exists(slug):
            page = get_page(slug)
            return dict(page=page,
                        edit=request.GET.get('edit',False),
                        exists=True)
        else:
            return dict(exists=False,
                        slug=slug)
    else:
        # save/create a page
        if exists(slug):
            page = get_page(slug)
            page.body = request.POST.get('body','')
            page.title = request.POST.get('title','')
            page.update_tags(request.POST.get('tags','').split(' '))
            page.save()
            return HttpResponseRedirect(page.get_absolute_url())
        else:
            if slug == '':
                slug = request.POST.get('title').lower()
            page = create_page(slug=slug,title=request.POST.get('title',''),
                               body=request.POST.get('body',''),
                               tags=request.POST.get('tags','').split(' '))
            return HttpResponseRedirect(page.get_absolute_url())
        

@rendered_with("main/tag.html")
def tag(request,tag):
    return dict(tag=tag,pages=get_tag_pages(tag))

@rendered_with("main/tag_index.html")
def tag_index(request):
    return dict(tags=get_all_tags())
