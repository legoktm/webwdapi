#!/data/project/wdapi/python/bin/python
"""
Released in to the public domain by Legoktm, 2013
"""

import cgitb
cgitb.enable()  # TODO flask this maybe.
print "Content-type: application/json\n\n"
import cgi
import hashlib
import memcache
import pywikibot
import simplejson
import wdapi

repo = pywikibot.Site('en', 'wikipedia').data_repository()
form = cgi.FieldStorage()
mc = memcache.Client(['tools-mc'])
CACHE_FOR = 60 * 60 * 24  # Store for 1 day


def md5():
    d = {}
    keys = ['property', 'debug']
    # debug is a random key we can use to bypass caching
    for key in keys:
        if key in form:
            d[key] = form[key].value
    return hashlib.md5(simplejson.dumps(d)).hexdigest()


def run(d, was_cached=False):
    # Save in memcached
    if not was_cached:
        # But don't extend caching for already cached stuff
        mc.set(md5(), d, CACHE_FOR)
    if was_cached and 'debug' in form:
        d['cached'] = ''  # For debugging

    # Set the status
    if 'error' in d:
        d['status'] = 'error'
        # Lets add a documentation link
        d['help'] = 'https://www.wikidata.org/wiki/User:Legoktm/wdapi'
    else:
        d['status'] = 'success'

    # Now print it
    if 'format' in form and form['format'].value == 'jsonfm':
        #pretty print...
        print simplejson.dumps(d, indent=4 * ' ')
    else:
        print simplejson.dumps(d)


def main():
    # Check if it's been cached already
    old = mc.get(md5())
    if old is not None:
        return run(old, was_cached=True)

    # Check that a property was specified
    if not 'property' in form:
        return run({'error': 'noproperty'})
    prop = form['property'].value.lower()
    # Make sure it starts with p
    if not prop.startswith('p'):
        prop = 'p' + prop
    # Make sure its a valid number
    if not prop[1:].isdigit():
        return run({'error': 'invalidproperty'})
    p = wdapi.WDProperty(repo, prop)
    # Make sure it exists
    if not p.exists():
        return run({'error': 'doesnotexist'})
    # At this point, p.get() will already have been called
    # so we can just run the function
    return run({'constraints': p.constraints()})

if __name__ == "__main__":
    main()