from django.contrib import admin
from django.utils.html import format_html

from .models import Branch, Student


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "students_count")
    list_editable = ("order",)
    ordering = ("order", "name")

    @admin.display(description="عدد الطلاب")
    def students_count(self, obj):
        return obj.students.count()


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "photo_thumbnail",
        "name",
        "branch",
        "achievement",
        "honor_date",
        "is_active",
    )
    list_display_links = ("name",)
    list_editable = ("is_active",)
    list_filter = ("branch", "is_active", "honor_date")
    search_fields = ("name", "achievement")
    list_per_page = 50
    list_select_related = ("branch",)
    date_hierarchy = "honor_date"
    ordering = ("-honor_date", "-created_at")
    actions = ("hide_from_board", "show_on_board")
    fieldsets = (
        (None, {"fields": ("name", "branch", "achievement")}),
        ("الصورة والتكريم", {"fields": ("photo", "photo_preview", "honor_date", "is_active")}),
    )
    readonly_fields = ("photo_preview",)

    # -- display helpers ----------------------------------------------------
    @admin.display(description="الصورة")
    def photo_thumbnail(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" alt="صورة {}" '
                'style="width:52px;height:52px;border-radius:50%;'
                'object-fit:cover;display:block" />',
                obj.photo.url,
                obj.name,
            )
        return format_html(
            '<span style="display:inline-flex;width:52px;height:52px;'
            'border-radius:50%;align-items:center;justify-content:center;'
            'background:#efe7d8;color:#8a7a6b;font-weight:700">{}</span>',
            obj.first_letter,
        )

    @admin.display(description="معاينة الصورة")
    def photo_preview(self, obj):
        if obj.pk and obj.photo:
            return format_html(
                '<img src="{}" alt="صورة {}" '
                'style="max-width:220px;max-height:220px;border-radius:12px;'
                'object-fit:cover;display:block" />',
                obj.photo.url,
                obj.name,
            )
        return "—"

    # -- bulk actions --------------------------------------------------------
    @admin.action(description="إخفاء المحدد من اللوحة")
    def hide_from_board(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"تم إخفاء {count} من الطلاب من اللوحة.")

    @admin.action(description="إظهار المحدد في اللوحة")
    def show_on_board(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"تم إظهار {count} من الطلاب في اللوحة.")
