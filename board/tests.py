from datetime import timedelta

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from .models import Branch, Student


class HealthEndpointTests(TestCase):
    def test_health_returns_ok_without_touching_the_database(self):
        with self.assertNumQueries(0):
            response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")


class StudentListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.branch_a = Branch.objects.create(name="فرع أ", order=0)
        cls.branch_b = Branch.objects.create(name="فرع ب", order=1)
        cls.visible = Student.objects.create(
            name="طالب ظاهر", branch=cls.branch_a, achievement="إنجاز تجريبي"
        )
        Student.objects.create(
            name="طالب مخفي", branch=cls.branch_b, achievement="إنجاز تجريبي", is_active=False
        )

    def test_only_active_students_are_listed(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "طالب ظاهر")
        self.assertNotContains(response, "طالب مخفي")

    def test_branch_filter_shows_only_that_branch(self):
        Student.objects.create(name="طالب فرع ب", branch=self.branch_b, achievement="إنجاز")
        response = self.client.get("/", {"branch": self.branch_b.pk})
        self.assertContains(response, "طالب فرع ب")
        self.assertNotContains(response, "طالب ظاهر")

    def test_unknown_branch_id_shows_all_active_students(self):
        response = self.client.get("/", {"branch": 99999})
        self.assertContains(response, "طالب ظاهر")

    def test_empty_state_is_friendly(self):
        Student.objects.update(is_active=False)
        response = self.client.get("/")
        self.assertContains(response, "لا توجد أسماء في اللوحة بعد")

    def test_pagination_24_per_page_and_branch_param_kept(self):
        for i in range(30):
            Student.objects.create(
                name=f"طالب صف {i}", branch=self.branch_a, achievement="إنجاز"
            )
        response = self.client.get("/", {"branch": self.branch_a.pk})
        self.assertEqual(len(response.context["students"]), 24)
        self.assertTrue(response.context["page_obj"].has_next())

        page_two = self.client.get(
            "/", {"branch": self.branch_a.pk, "page": 2}
        )
        self.assertEqual(len(page_two.context["students"]), 7)
        # The next/previous links must keep the branch filter.
        self.assertIn(f"branch={self.branch_a.pk}", page_two.context["prev_url"])
        self.assertIn("page=1", page_two.context["prev_url"])


class SeedDemoTests(TestCase):
    def test_seed_demo_refuses_to_run_when_debug_is_off(self):
        # The Django test runner always runs with DEBUG=False.
        with self.assertRaises(CommandError):
            call_command("seed_demo")


class StudentModelTests(TestCase):
    def test_first_letter_for_placeholder_avatar(self):
        branch = Branch.objects.create(name="فرع", order=0)
        student = Student.objects.create(
            name="أحمد", branch=branch, achievement="إنجاز"
        )
        self.assertEqual(student.first_letter, "أ")

    def test_honor_date_defaults_to_today(self):
        branch = Branch.objects.create(name="فرع", order=0)
        student = Student.objects.create(
            name="طالب", branch=branch, achievement="إنجاز"
        )
        self.assertEqual(student.honor_date, timezone.localdate())
        self.assertLessEqual(
            student.created_at.date() - timezone.localdate(), timedelta(days=1)
        )
