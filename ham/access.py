from functools import wraps

from django.http import Http404

from .services import user_has_ham_access


def enlightened_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not user_has_ham_access(request.user):
            raise Http404
        return view(request, *args, **kwargs)

    return wrapped
