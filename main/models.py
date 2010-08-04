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
    def __init__(self,json):
        data = loads(json)
        self.slug = data['slug']
        self.title = data['title']
        self.body = data.get('body','')
        self.tags = data.get('tags',[])
        self.created = datetime.strptime(data['created'],DTFORMAT)
        self.modified = datetime.strptime(data['modified'],DTFORMAT)
        self.versions = data.get('versions',[])

    def data(self):
        # suitable for json serialization
        return {'title' : self.title,
                'slug' : self.slug,
                'body' : self.body,
                'tags' : self.tags,
                'created' : self.created.strftime(DTFORMAT),
                'modified' : self.modified.strftime(DTFORMAT),
            }

    def save(self,comment=""):
        v = self.create_version(comment)
        self.versions.append(v)
        data = self.data()
        data['versions'] = self.versions
        data['modified'] = datetime.now().strftime(DTFORMAT)
        obj = page_bucket.get_binary(self.slug)
        obj.set_data(dumps(data))
        obj.store()
        self.update_tags()

    def create_version(self,comment=""):
        id = self.slug + '-version-' + str(len(self.versions))
        d = {
            'id' : id,
            'created' : datetime.now().strftime(DTFORMAT),
            'comment' : comment,
            }
        v = version_bucket.new_binary(id,dumps(self.data())).store()
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
        return " ".join(self.tags)

    def update_tags(self):
        for tag in self.tags:
            t = tag_bucket.get_binary(tag)
            if not t.exists():
                print "doesn't exist"
                d = {"pages" : [{"title" : self.title, "slug" : self.slug}]}
                t = tag_bucket.new_binary(tag,dumps(d))
                t.store()
            else:
                print "exists"
                d = loads(t.get_data())
                already_there = False
                for page in d['pages']:
                    if page["slug"] == self.slug:
                        already_there = True
                        break
                if not already_there:
                    print "not already there"
                    d['pages'].append({"title" : self.title, "slug" : self.slug})
                    t.set_data(dumps(d))
                    t.store()
                else:
                    print "already there"
                    
            

def make_slug(title="no title"):
    title = title.strip().lower()
    slug = re.sub(r"[\W\-]+","-",title)
    slug = re.sub(r"^\-+","",slug)
    slug = re.sub(r"\-+$","",slug)
    if slug == "":
        slug = "-"
    return slug

def get_page(slug):
    json = page_bucket.get_binary(slug).get_data()
    return Page(json=json)

def create_page(slug,title,body,tags):
    created = datetime.now().strftime(DTFORMAT)
    modified = created
    versions = []
    json = dumps({'title' : title,
                        'slug' : slug,
                        'body' : body,
                        'tags' : tags,
                        'created' : created,
                        'modified' : modified,
                        'versions' : [],
                        'tags' : tags})
    obj = page_bucket.new_binary(slug,json).store()
    # save it, then return a useful object
    return Page(json)

def exists(slug):
    p = page_bucket.get_binary(slug)
    return p.exists()

def get_tag_pages(tag):
    t = tag_bucket.get_binary(tag)
    if not t.exists():
        return []
    return [get_page(p['slug']) for p in loads(t.get_data())['pages']]
    
    
