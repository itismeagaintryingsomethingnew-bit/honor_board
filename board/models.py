from django.db import models
from django.utils import timezone


class Branch(models.Model):
    """A center branch (managed from the admin so the staff can add or
    rename branches without touching code)."""

    name = models.CharField("الاسم", max_length=100, unique=True)
    order = models.PositiveIntegerField("الترتيب", default=0)

    class Meta:
        verbose_name = "فرع"
        verbose_name_plural = "الفروع"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Student(models.Model):
    """An honored student shown on the public board."""

    name = models.CharField("اسم الطالب", max_length=200)
    branch = models.ForeignKey(
        Branch,
        verbose_name="الفرع",
        on_delete=models.PROTECT,
        related_name="students",
    )
    achievement = models.CharField(
        "الإنجاز",
        max_length=200,
        help_text="سبب التكريم، مثال: أتم حفظ جزء عم كاملًا",
    )
    photo = models.ImageField("الصورة", upload_to="students/", blank=True)
    honor_date = models.DateField("تاريخ التكريم", default=timezone.localdate)
    is_active = models.BooleanField("ظاهر في اللوحة", default=True)
    created_at = models.DateTimeField("تاريخ الإضافة", auto_now_add=True)

    class Meta:
        verbose_name = "طالب"
        verbose_name_plural = "الطلاب"
        ordering = ["-honor_date", "-created_at"]

    def __str__(self):
        return self.name

    @property
    def first_letter(self):
        """First letter of the name, used for the placeholder avatar."""
        return (self.name or "").strip()[:1] or "؟"
