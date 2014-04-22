from rest_framework import renderers
from django.core.urlresolvers import resolve, get_script_prefix
from rest_framework.utils import formatting

class BODBBrowsableAPIRenderer(renderers.BrowsableAPIRenderer):

        def get_name(self, view):
            return view.model.__name__
        
        
        def get_breadcrumbs(self, request):
            """
            Given a url returns a list of breadcrumbs, which are each a
            tuple of (name, url).
            """
            url = request.path
        
            #from rest_framework.settings import api_settings
            from rest_framework.views import APIView
        
            #view_name_func = api_settings.VIEW_NAME_FUNCTION
            
            def get_view_name(view_cls, suffix=None):
                """
                Given a view class, return a textual name to represent the view.
                This name is used in the browsable API, and in OPTIONS responses.
                
                This function is the default for the `VIEW_NAME_FUNCTION` setting.
                """
                name = view_cls.__name__
                name = formatting.remove_trailing_string(name, 'View')
                name = formatting.remove_trailing_string(name, 'ViewSet')
                #name = formatting.camelcase_to_spaces(name)
                if suffix:
                    name += ' ' + suffix
            
                return name
        
            def breadcrumbs_recursive(url, breadcrumbs_list, prefix, seen):
                """
                Add tuples of (name, url) to the breadcrumbs list,
                progressively chomping off parts of the url.
                """
        
                try:
                    (view, unused_args, unused_kwargs) = resolve(url)
                except Exception:
                    pass
                else:
                    # Check if this is a REST framework view,
                    # and if so add it to the breadcrumbs
                    cls = getattr(view, 'cls', None)
                    if cls is not None and issubclass(cls, APIView):
                        # Don't list the same view twice in a row.
                        # Probably an optional trailing slash.
                        if not seen or seen[-1] != view:
                            suffix = getattr(view, 'suffix', None)
                            name = get_view_name(cls, suffix)
                            breadcrumbs_list.insert(0, (name, prefix + url))
                            seen.append(view)
        
                if url == '':
                    # All done
                    return breadcrumbs_list
        
                elif url.endswith('/'):
                    # Drop trailing slash off the end and continue to try to
                    # resolve more breadcrumbs
                    url = url.rstrip('/')
                    return breadcrumbs_recursive(url, breadcrumbs_list, prefix, seen)
        
                # Drop trailing non-slash off the end and continue to try to
                # resolve more breadcrumbs
                url = url[:url.rfind('/') + 1]
                return breadcrumbs_recursive(url, breadcrumbs_list, prefix, seen)
        
            prefix = get_script_prefix().rstrip('/')
            url = url[len(prefix):]
            return breadcrumbs_recursive(url, [], prefix, [])
        