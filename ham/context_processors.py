from .services import user_has_ham_access


def ham_clearance(request):
    return {"ham_access": user_has_ham_access(request.user)}
