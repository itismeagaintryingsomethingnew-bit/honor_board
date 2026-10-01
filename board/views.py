from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render

from .models import Branch, Student

PAGE_SIZE = 24


def student_list(request):
    """The public honor board: active students, newest honors first."""
    students = (
        Student.objects.filter(is_active=True)
        .select_related("branch")
        .order_by("-honor_date", "-created_at")
    )

    # Branch filter via ?branch=<id> (invalid or unknown values show all).
    selected_branch = None
    branch_value = request.GET.get("branch", "").strip()
    if branch_value.isdecimal():
        selected_branch = Branch.objects.filter(pk=int(branch_value)).first()
        if selected_branch is not None:
            students = students.filter(branch=selected_branch)

    # Pills: "الكل" plus one per branch that actually has visible students.
    branches = (
        Branch.objects.filter(students__is_active=True)
        .distinct()
        .order_by("order", "name")
    )

    # get_page() tolerates missing/invalid page numbers gracefully.
    page_obj = Paginator(students, PAGE_SIZE).get_page(request.GET.get("page"))

    def page_url(number):
        """Pagination links that keep the current ?branch= filter."""
        params = {"page": number}
        if selected_branch is not None:
            params["branch"] = selected_branch.pk
        return "?" + urlencode(params)

    return render(
        request,
        "board/student_list.html",
        {
            "branches": branches,
            "selected_branch": selected_branch,
            "page_obj": page_obj,
            "students": page_obj.object_list,
            "prev_url": page_url(page_obj.previous_page_number()) if page_obj.has_previous() else None,
            "next_url": page_url(page_obj.next_page_number()) if page_obj.has_next() else None,
        },
    )


def health(request):
    """Cheap liveness probe. Deliberately does not touch the database so it
    stays fast and reliable even while Neon's compute is waking up."""
    return HttpResponse("ok", content_type="text/plain; charset=utf-8")
