from django.db import models
from django.conf import settings

from simplejson import loads, dumps

from riak import RiakClient
from riak import RiakPbcTransport
from riak import RiakHttpTransport

from datetime import datetime
import re

HOST = settings.RIAK_HOST
PORT = settings.RIAK_PORT

client = RiakClient(host=HOST,port=PORT)
page_bucket = client.bucket('riakipage')
version_bucket = client.bucket('riakiversion')
tag_bucket = client.bucket('riakitag')

# Create your models here.

DTFORMAT = "%Y-%m-%dT%H:%M:%S"

class Page:
    def __init__(self,p):
        self._page = p
        json = p.get_data()
        data = loads(json)
        self.slug = data['slug']
        self.title = data['title']
        self.body = data.get('body','')
        self.created = datetime.strptime(data['created'],DTFORMAT)
        self.modified = datetime.strptime(data['modified'],DTFORMAT)

    def data(self):
        # suitable for json serialization
        return {'title' : self.title,
                'slug' : self.slug,
                'body' : self.body,
                'created' : self.created.strftime(DTFORMAT),
                'modified' : self.modified.strftime(DTFORMAT),
            }

    def save(self,comment=""):
        v = self.create_version(comment)
        data = self.data()
        data['modified'] = datetime.now().strftime(DTFORMAT)
        self._page.set_data(dumps(data))
        self._page.store()

    def versions(self):
        return [v.get() for v in self._page.get_links() if v.get_bucket() == "riakiversion" and v.get().exists()]

    def version_data(self,v):
        try:
            d = loads(v.get_data())
            d['version_created'] = datetime.strptime(d['version_created'],DTFORMAT)
            d['created'] = datetime.strptime(d['created'],DTFORMAT)
            d['modified'] = datetime.strptime(d['modified'],DTFORMAT)
            # there must be one single link back to a Page
            d['page'] = Page(v.get_links()[0].get())
            return d
        except:
            return {}


    def versions_data(self):
        return [self.version_data(v)
            for v in self.versions()]

    def create_version(self,comment=""):
        id = self.slug + '-version-' + str(len(self._page.link("riakiversion").run()))
        d = self.data()
        d['version_id'] = id
        d['version_created'] = datetime.now().strftime(DTFORMAT)
        d['version_comment'] = comment
        d['tags'] = self.tags_string()
        
        v = version_bucket.new_binary(id,dumps(d)).store()
        v.add_link(self._page).store()
        self._page.add_link(v).store()
        return d
        
    def get_absolute_url(self):
        return "/page/%s/" % self.slug

    def link_text(self,text=""):
        # take care of image links first
        pattern = re.compile(r"(\[\[\s*[^\|\]]+\s*\|?\s*[^\]]*\s*\]\])")
        pattern2 = re.compile(r"^\[\[\s*([^\|\]]+)\s*\|?\s*([^\]]*)\s*\]\]$")
        results = []
        for part in pattern.split(text):
            m = pattern2.match(part)
            if m:
                (title,link_text) = m.groups()
                (cnt,slug) = self.page_by_title(title)
                if link_text == "":
                    link_text = title
                if cnt:
                    part = """<a href="/page/%s/" class="existing">%s</a>""" % (slug, link_text)
                else:
                    part = """<a href="/page/%s/" class="notfound">%s</a>""" % (make_slug(title),link_text)
            results.append(part)
        return ''.join(results)

    def page_by_title(self,title):
        slug = make_slug(title)
        return (exists(slug),slug)

    def linked_body(self):
        return self.link_text(self.body)

    def tags_string(self):
        return " ".join(self.tags())

    def tags(self):
        return [tag.get_key() for tag in self._page.get_links() if tag.get_bucket() == 'riakitag' and tag.get().exists()]

    def clear_tags(self):
        """ clear all the tag links out """
        for tag in self._page.get_links():
            if tag.get_bucket() != "riakitag":
                continue
            t = tag.get()
            if not t.exists():
                continue
            self._page.remove_link(tag).store()
            t.remove_link(self._page).store()
            # if the tag no longer has any pages, delete it
            if len(t.get_links()) == 0:
                t.delete()
        self._page.store()

    def add_tag(self,tag):
        t = tag_bucket.get_binary(tag)
        if not t.exists():
            # it doesn't exist so it must not be in
            # our list of tags for the page either
            print "creating new tag"
            t = tag_bucket.new(tag,tag)
            t.add_link(self._page)
            t.store()
            self._page.add_link(t).store()
        else:
            print "tag exists"
            # the tag already exists, so we need to check
            # if it's already in the list of tags for this page
            # and avoid double entering it
            if tag not in self.tags():
                print "tag not already there"
                # we can add it
                self._page.add_link(t).store()
                # also add the back-link
                t.add_link(self._page).store()

    def update_tags(self,tags):
        self.clear_tags()
        for tag in tags:
            self.add_tag(tag)

def make_slug(title="no title"):
    title = title.strip().lower()
    slug = re.sub(r"[\W\-]+","-",title)
    slug = re.sub(r"^\-+","",slug)
    slug = re.sub(r"\-+$","",slug)
    if slug == "":
        slug = "-"
    return slug

def get_page(slug):
    p = page_bucket.get_binary(slug)
    return Page(p)

def create_page(slug,title,body,tags):
    created = datetime.now().strftime(DTFORMAT)
    modified = created
    versions = []
    json = dumps({'title' : title,
                  'slug' : slug,
                  'body' : body,
                  'created' : created,
                  'modified' : modified,
                  })
    
    obj = page_bucket.new_binary(slug,json).store()
    # save it, then return a useful object
    p = Page(obj)
    for t in tags:
        p.add_tag(t)
    return p

def exists(slug):
    p = page_bucket.get_binary(slug)
    return p.exists()

def get_tag_pages(tag):
    t = tag_bucket.get_binary(tag)
    if not t.exists():
        return []

    return [Page(p.get()) for p in t.get_links() if p.get_bucket() == "riakipage"]
    
    
