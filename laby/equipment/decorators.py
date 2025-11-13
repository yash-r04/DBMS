from django.shortcuts import redirect

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'Admin':
            return view_func(request, *args, **kwargs)
        return redirect('no_permission')
    return wrapper

def staff_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role in ['Admin', 'Staff']:
            return view_func(request, *args, **kwargs)
        return redirect('no_permission')
    return wrapper

def viewer_allowed(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return wrapper
