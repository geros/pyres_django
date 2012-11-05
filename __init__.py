from pyres import ResQ
from pyres_scheduler import PyresScheduler

"""
Copyright (c) 2007-2008, Dj Gilcrease
All rights reserved.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

def autodiscover():
    """
    Auto-discover INSTALLED_APPS cron.py modules and fail silently when
    not present. This forces an import on them to register any cron jobs they
    may want.
    """
    import imp
    from django.conf import settings

    for app in settings.INSTALLED_APPS:
        # For each app, we need to look for an cron.py inside that app's
        # package. We can't use os.path here -- recall that modules may be
        # imported different ways (think zip files) -- so we need to get
        # the app's __path__ and look for cron.py on that path.

        # Step 1: find out the app's __path__ Import errors here will (and
        # should) bubble up, but a missing __path__ (which is legal, but weird)
        # fails silently -- apps that do weird things with __path__ might
        # need to roll their own cron registration.
        try:
            app_path = __import__(app, {}, {}, [app.split('.')[-1]]).__path__
        except AttributeError:
            continue

        # Step 2: use imp.find_module to find the app's admin.py. For some
        # reason imp.find_module raises ImportError if the app can't be found
        # but doesn't actually try to import the module. So skip this app if
        # its admin.py doesn't exist
        try:
            fp, pathname, description = imp.find_module('tasks', app_path)
        except ImportError:
            continue

        # Step 3: import the app's task file. If this has errors we want them
        # to bubble up.

        modulename = imp.load_module('tasks', fp, pathname, description)
        # Step 4: iterate though tasks.py module and find all classes with their names
        # starting with 'Periodic' and 'Interval'.
        for item in dir(modulename):
            if 'Periodic' or 'Interval' in item and hasattr(item, '__class__'):
                pyres_sched = PyresScheduler()
                resque = ResQ()
                pyres_sched.add_resque(resque)
                pyres_sched.start()

                classname = getattr(modulename, item)
                if hasattr(classname, 'run_every'):
                    run_every = getattr(classname, 'run_every')

                if 'Periodic' in item:
                    print 'periodic'
                    pyres_sched.add_cron_job(classname, args=None, **run_every)
                elif 'Interval' in item:
                    pyres_sched.add_interval_job(classname, args=None, **run_every)




