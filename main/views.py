from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from models import get_page, create_page, exists, get_tag_pages, get_all_tags
import models
from utils import parse_tags


class rendered_with(object):
    def __init__(self, template_name):
        self.template_name = template_name

    def __call__(self, func):
        def rendered_func(request, *args, **kwargs):
            items = func(request, *args, **kwargs)
            if isinstance(items, dict):
                return render_to_response(
                    self.template_name, items,
                    context_instance=RequestContext(request))
            else:
                return items

        return rendered_func


@rendered_with("main/page.html")
def page(request, slug="index"):
    if request.method == "GET":
        if exists(slug):
            page = get_page(slug)
            return dict(page=page,
                        edit=request.GET.get('edit', False),
                        exists=True)
        else:
            return dict(exists=False,
                        slug=slug)
    else:
        # save/create a page
        if exists(slug):
            page = get_page(slug)
            page.body = request.POST.get('body', '')
            page.title = request.POST.get('title', '')
            tags = parse_tags(request.POST.get('tags', ''))
            page.update_tags(tags)
            page.save()
            return HttpResponseRedirect(page.get_absolute_url())
        else:
            if slug == '':
                slug = request.POST.get('title').lower()
            page = create_page(slug=slug, title=request.POST.get('title', ''),
                               body=request.POST.get('body', ''),
                               tags=parse_tags(request.POST.get('tags', '')))
            return HttpResponseRedirect(page.get_absolute_url())


@rendered_with("main/page_history.html")
def page_history(request, slug="index"):
    if exists(slug):
        page = get_page(slug)
        return dict(page=page)
    else:
        return HttpResponse("no such page")


@rendered_with("main/version.html")
def version(request, version_id):
    version = models.get_version(version_id)
    return dict(version=version)


@rendered_with("main/tag.html")
def tag(request, tag):
    return dict(tag=tag, pages=get_tag_pages(tag))


def delete_tag(request, tag):
    if request.method == "POST":
        models.delete_tag(tag)
        return HttpResponseRedirect("/tag/")
    else:
        return HttpResponse(
            """Are you sure? <form action="." method="post">"""
            """<input type="submit" value="yes"/></form>""")


@rendered_with("main/tag_index.html")
def tag_index(request):
    return dict(tags=get_all_tags())


@rendered_with("main/page_index.html")
def page_index(request):
    return dict(pages=models.get_all_pages())
