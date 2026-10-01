"""Create obvious fake demo data (3 branches + 8 students) for local
screenshots and first impressions. Never runs automatically anywhere, and it
refuses to run outside local development (DEBUG=True)."""

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from board.models import Branch, Student

DEMO_BRANCHES = [
    ("الفرع الرئيسي", 0),
    ("فرع النور", 1),
    ("فرع السلام", 2),
]

# (student name, branch index, achievement, days since the honor)
DEMO_STUDENTS = [
    ("طالب تجريبي ١", 0, "أتم حفظ جزء عم كاملًا", 28),
    ("طالب تجريبي ٢", 0, "المركز الأول في مسابقة الحفظ", 24),
    ("طالب تجريبي ٣", 1, "حفظ سورة الكهف كاملة", 18),
    ("طالب تجريبي ٤", 1, "أتم حفظ خمسة أجزاء", 14),
    ("طالب تجريبي ٥", 2, "مثالية في الحضور والانضباط", 10),
    ("طالب تجريبي ٦", 0, "أتم حفظ القرآن الكريم كاملًا", 7),
    ("طالب تجريبي ٧", 1, "تحسن ملحوظ في التلاوة والتجويد", 4),
    ("طالب تجريبي ٨", 2, "حفظ سورة يس كاملة", 1),
]


class Command(BaseCommand):
    help = "ينشئ ٣ فروع و٨ طلاب بأسماء تجريبية للتجربة المحلية فقط (بدون صور)"

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "هذا الأمر مخصص للتطوير المحلي فقط (يتطلب DEBUG=True) "
                "ولا يعمل في الإنتاج مطلقًا."
            )

        branches = []
        for name, order in DEMO_BRANCHES:
            branch, _created = Branch.objects.get_or_create(name=name, defaults={"order": order})
            branches.append(branch)

        created = 0
        for name, branch_index, achievement, days_ago in DEMO_STUDENTS:
            _student, was_created = Student.objects.get_or_create(
                name=name,
                defaults={
                    "branch": branches[branch_index],
                    "achievement": achievement,
                    "honor_date": timezone.localdate() - timedelta(days=days_ago),
                },
            )
            created += 1 if was_created else 0

        self.stdout.write(
            self.style.SUCCESS(
                f"تم تجهيز البيانات التجريبية: {len(branches)} فروع و٨ طلاب "
                f"(منهم {created} جديد). افتح الصفحة الرئيسية لمعاينتها."
            )
        )
