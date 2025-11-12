from django.contrib.auth.decorators import user_passes_test

def admin_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.role == 'Admin')(view_func)

def staff_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.role in ['Admin', 'Staff'])(view_func)

def viewer_allowed(view_func):
    return user_passes_test(lambda u: u.is_authenticated)(view_func)
