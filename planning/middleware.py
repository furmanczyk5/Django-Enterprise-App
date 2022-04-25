from django.shortcuts import redirect

# from django.views.decorators.csrf import csrf_exempt

class PlanningMiddleware(object):

    def __init__(self, get_response):
        """
        One-time configuration and initialization for this middleware.
        """
        self.get_response = get_response
        

    def __call__(self, request):
        
        # redirect to paths ending in "/"
        if not request.path.endswith('/') and not '.' in request.path:
            return redirect(request.path + '/')

        # TO DO... this is conference/app specific... SHOULD NOT BE IN GENERAL MIDDLEWARE
        # set attribute that specifies mobile app vs regular pages
        if request.path.startswith('/mobile/'):
            request.detect_mobile_app = {
                "is_mobileapp" : True,
                "use_template" : 'newtheme/templates/conference/mobile-app.html',
                "path_root" : '/mobile/'
            }
        else:
            request.detect_mobile_app = {
                "is_mobileapp" : False,
                "use_template" : 'newtheme/templates/conference/page-nosidebar.html',
                "path_root" : '/'
            }

        # set request.contact attribute
        if request.user.is_authenticated() and not hasattr(request, "contact") and request.user.username != "administrator":
            request.contact = request.user.contact 

        response = self.get_response(request)
        return response


