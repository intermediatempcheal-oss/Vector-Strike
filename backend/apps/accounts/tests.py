"""Phase 6 backend tests: vector ID generation, age calculation, transactionality,
validations, guardian/verification flows and unique identifiers."""

from datetime import date

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts import services
from apps.accounts.models import (
    GuardianRelationship,
    IdentityDocumentUpload,
    OnboardingProgress,
    User,
    Verification,
)
from apps.profiles.models import PlayStyle, Profile, UserInterest, UserPlayStyle


class VectorIdTests(TestCase):
    def test_human_format(self):
        candidate = services.generate_vector_id_candidate()
        self.assertRegex(candidate, r"^VS-[A-Z2-9]{8}$")

    def test_no_ambiguous_characters(self):
        for _ in range(200):
            candidate = services.generate_vector_id_candidate()
            self.assertNotIn("0", candidate)
            self.assertNotIn("O", candidate)
            self.assertNotIn("1", candidate)
            self.assertNotIn("I", candidate)
            self.assertNotIn("L", candidate)

    def test_generation_is_unique(self):
        ids = {services.generate_unique_vector_id(lambda c: False) for _ in range(300)}
        self.assertEqual(len(ids), 300)

    def test_avoids_existing_ids(self):
        taken = {"VS-AAAAAAAA", "VS-BBBBBBBB"}
        for _ in range(25):
            cand = services.generate_unique_vector_id(lambda c: c in taken)
            self.assertNotIn(cand, taken)


class AgeCalculationTests(TestCase):
    def test_age_boundaries(self):
        self.assertEqual(
            services.calculate_age(date(2010, 1, 1), date(2026, 1, 1)), 16
        )
        self.assertEqual(
            services.calculate_age(date(2010, 1, 1), date(2025, 12, 31)), 15
        )
        self.assertEqual(
            services.calculate_age(date(2010, 12, 31), date(2026, 12, 30)), 15
        )
        self.assertEqual(
            services.calculate_age(date(2010, 12, 31), date(2026, 12, 31)), 16
        )

    def test_age_group_buckets(self):
        self.assertEqual(services.age_group_from_birthdate(date(2018, 5, 1), date(2026, 1, 1)), "6-9")
        self.assertEqual(services.age_group_from_birthdate(date(2014, 5, 1), date(2026, 1, 1)), "10-12")
        self.assertEqual(services.age_group_from_birthdate(date(2012, 5, 1), date(2026, 1, 1)), "13-15")
        self.assertEqual(services.age_group_from_birthdate(date(2009, 5, 1), date(2026, 1, 1)), "16-17")
        self.assertEqual(services.age_group_from_birthdate(date(2007, 5, 1), date(2026, 1, 1)), "18+")

    def test_branch_guardian_vs_verification(self):
        today = date(2026, 1, 1)
        under = services.choose_onboarding_branch(date(2014, 1, 1), today=today)
        above = services.choose_onboarding_branch(date(2008, 6, 1), today=today)
        boundary = services.choose_onboarding_branch(date(2009, 6, 1), today=today)
        self.assertEqual(under["branch"], "guardian")
        self.assertEqual(under["age"], 12)
        self.assertEqual(above["branch"], "verification")
        self.assertEqual(boundary["age"], 16)
        # age 16 on arbitrary day is under threshold 17 -> guardian
        self.assertEqual(boundary["branch"], "guardian")

    def test_threshold_is_configurable(self):
        self.assertEqual(settings.GUARDIAN_AGE_THRESHOLD, 17)
        self.assertEqual(settings.VERIFICATION_AGE_THRESHOLD, 17)

    def test_region_config(self):
        required, cfg = services.verification_required_for_region(17, "US")
        self.assertTrue(required)
        required, cfg = services.verification_required_for_region(16, "US")
        self.assertFalse(required)
        required, cfg = services.verification_required_for_region(16, "EU")
        self.assertTrue(required)


class UsernameValidationTests(APITestCase):
    def test_valid_usernames(self):
        for name in ["nova_99", "SkyRunner", "m4th.wiz", "player_x_2000"]:
            resp = self.client.post(reverse("username-check"), {"username": name}, format="json")
            self.assertEqual(resp.status_code, 200, name)
            self.assertTrue(resp.data["available"])

    def test_reserved_and_invalid(self):
        for name in ["admin", "VectorStrike", "system", "ab", "bad name!", ""]:
            resp = self.client.post(reverse("username-check"), {"username": name}, format="json")
            self.assertFalse(resp.data["valid"])

    def test_taken_username(self):
        User.objects.create_user(
            email="wind@example.com",
            password="secret-pass-123",
            username="occupied_user",
            phone="+15550001111",
            full_name="Wind User",
            date_of_birth=date(2000, 1, 1),
        )
        resp = self.client.post(reverse("username-check"), {"username": "occupied_user"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data["available"])

    def test_taken_username_case_insensitive(self):
        User.objects.create_user(
            email="wind@example.com",
            password="secret-pass-123",
            username="CamelUser",
            phone="+15550001111",
            full_name="Wind User",
            date_of_birth=date(2000, 1, 1),
        )
        resp = self.client.post(reverse("username-check"), {"username": "cameluser"}, format="json")
        self.assertFalse(resp.data["available"])


class AgeCheckApiTests(APITestCase):
    def test_age_check_guardian(self):
        resp = self.client.post(
            reverse("onboarding-age-check"),
            {"date_of_birth": "2013-04-10"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["branch"], "guardian")
        self.assertEqual(resp.data["age"], services.calculate_age(date(2013, 4, 10)))

    def test_age_check_verification(self):
        resp = self.client.post(
            reverse("onboarding-age-check"),
            {"date_of_birth": "2000-01-01"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["branch"], "verification")

    def test_future_dob_rejected(self):
        resp = self.client.post(
            reverse("onboarding-age-check"),
            {"date_of_birth": "2200-01-01"},
            format="json",
        )
        self.assertIn(resp.status_code, (400, 422))


class RegistrationFlowTests(APITestCase):
    def make_token(self, region="US"):
        resp = self.client.post(
            reverse("verification-upload"),
            {"document": self._fake_png(), "region": region},
            format="multipart",
        )
        if resp.status_code != 201:
            raise AssertionError(resp.content)
        return resp.data["verification_token"]

    def payload(self, dob="2011-05-05", guardian=True, **overrides):
        data = {
            "full_name": "Ava Nova",
            "username": "avanova01",
            "email": "ava@example.com",
            "phone": "+15551234567",
            "date_of_birth": dob,
            "password": "supersecret99",
            "region": "US",
            "interests": ["mathematics", "space", "logic"],
            "play_styles": ["puzzle-solver", "explore"],
            "terms_accepted": True,
        }
        if guardian:
            data.update(
                {
                    "guardian_email": "guardian@example.com",
                    "guardian_name": "Parent Guardian",
                }
            )
        data.update(overrides)
        return data

    def test_successful_17plus_account(self):
        token = self.make_token()
        resp = self.client.post(
            reverse("account-register"),
            self.payload(dob="2005-03-05", guardian=False, verification_token=token),
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        user = User.objects.get(email="ava@example.com")
        self.assertRegex(user.vector_id, r"^VS-[A-Z2-9]{8}$")
        self.assertTrue(user.onboarding_completed)
        self.assertEqual(user.account_status, "active")
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)
        self.assertEqual(UserInterest.objects.filter(user=user).count(), 3)
        self.assertEqual(UserPlayStyle.objects.filter(user=user).count(), 2)
        self.assertEqual(OnboardingProgress.objects.filter(user=user).count(), 1)
        # 17+ requires verification -> pending status, not age_verified yet
        self.assertEqual(user.verification_status, "pending")
        self.assertFalse(user.age_verified)
        # auto-login session established
        self.assertEqual(str(self.client.session["_auth_user_id"]), str(user.id))
        # recommendations returned for first experience
        self.assertEqual(len(resp.data["recommendations"]), 3)

    def test_underage_guardian_flow(self):
        resp = self.client.post(
            reverse("account-register"),
            self.payload(username="kidsky01"),
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        user = User.objects.get(username="kidsky01")
        rel = GuardianRelationship.objects.get(student_user=user)
        self.assertEqual(rel.guardian_email, "guardian@example.com")
        # Email was typed in, NOT verified.
        self.assertEqual(rel.status, "pending")
        self.assertEqual(rel.consent_status, "pending")
        self.assertTrue(user.age_verified)

    def test_missing_guardian_info_rejected_for_underage(self):
        resp = self.client.post(
            reverse("account-register"),
            self.payload(dob="2013-05-05", guardian=False),
            format="json",
        )
        self.assertEqual(resp.status_code, 422)
        fields = resp.data["error"]["fields"]
        self.assertIn("guardian_email", str(fields))
        self.assertEqual(User.objects.filter(email="ava@example.com").count(), 0)

    def test_future_dob_rejected_and_rollback(self):
        resp = self.client.post(
            reverse("account-register"),
            self.payload(dob="2100-01-01"),
            format="json",
        )
        self.assertIn(resp.status_code, (400, 422))
        self.assertEqual(User.objects.count(), 0)

    def test_duplicate_email_rejected(self):
        self.client.post(reverse("account-register"), self.payload(), format="json")
        resp = self.client.post(
            reverse("account-register"),
            self.payload(username="seconduser", phone="+15559876543"),
            format="json",
        )
        self.assertEqual(resp.status_code, 422)
        self.assertIn("email", str(resp.data))

    def test_duplicate_phone_rejected(self):
        self.client.post(reverse("account-register"), self.payload(), format="json")
        resp = self.client.post(
            reverse("account-register"),
            self.payload(username="thirduser", email="third@example.com"),
            format="json",
        )
        self.assertEqual(resp.status_code, 422)

    def test_duplicate_username_rejected(self):
        self.client.post(reverse("account-register"), self.payload(), format="json")
        resp = self.client.post(
            reverse("account-register"),
            self.payload(email="else@example.com", phone="+15556667777"),
            format="json",
        )
        self.assertEqual(resp.status_code, 422)

    def test_minimum_interests_enforced(self):
        resp = self.client.post(
            reverse("account-register"),
            self.payload(interests=["space", "logic"]),
            format="json",
        )
        self.assertEqual(resp.status_code, 422)
        self.assertIn("interests", str(resp.data))

    def test_terms_required(self):
        resp = self.client.post(
            reverse("account-register"), self.payload(terms_accepted=False), format="json"
        )
        self.assertEqual(resp.status_code, 422)

    def test_unknown_interest_slug_rejected(self):
        data = self.payload(interests=["space", "logic", "made-up-category"])
        # avoid raising KeyError on unknown interest in view: validation must catch it
        resp = self.client.post(reverse("account-register"), data, format="json")
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(User.objects.count(), 0)

    def test_verification_required_without_token(self):
        resp = self.client.post(
            reverse("account-register"),
            self.payload(dob="2000-01-01"),
            format="json",
        )
        self.assertEqual(resp.status_code, 422)
        self.assertIn("verification_token", str(resp.data))

    def test_invalid_password_rejected(self):
        resp = self.client.post(
            reverse("account-register"),
            self.payload(password="short"),
            format="json",
        )
        self.assertEqual(resp.status_code, 422)

    def test_duplicate_vector_ids_never_occur(self):
        # 17+ accounts require a document token; create real upload tokens and
        # verify every resulting Vector ID is globally unique.
        ids = []
        for i in range(8):
            upload_resp = self.client.post(
                reverse("verification-upload"),
                data={
                    "document": self._fake_png(),
                    "region": "US",
                },
                format="multipart",
            )
            token = upload_resp.data["verification_token"]
            resp = self.client.post(
                reverse("account-register"),
                self.payload(
                    username=f"tokuser{i}",
                    email=f"tok{i}@example.com",
                    phone=f"+1300{i:07d}",
                    dob="1995-01-01",
                    guardian=False,
                    verification_token=token,
                ),
                format="json",
            )
            self.assertEqual(resp.status_code, 201, resp.content)
            ids.append(resp.data["user"]["vector_id"])
        self.assertEqual(len(ids), len(set(ids)), f"Vector IDs duplicated: {ids}")

    def _fake_png(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        return SimpleUploadedFile(
            "id.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 32, content_type="image/png"
        )

    def test_document_upload_validation(self):
        # invalid magic bytes
        from django.core.files.uploadedfile import SimpleUploadedFile

        bad = SimpleUploadedFile("id.pdf", b"not a pdf at all", content_type="application/pdf")
        resp = self.client.post(reverse("verification-upload"), {"document": bad}, format="multipart")
        self.assertEqual(resp.status_code, 422)
        # unsupported type
        txt = SimpleUploadedFile("id.txt", b"hello", content_type="text/plain")
        resp = self.client.post(reverse("verification-upload"), {"document": txt}, format="multipart")
        self.assertEqual(resp.status_code, 422)

    def test_registration_with_document_token_flow(self):
        token = self.make_token()
        resp = self.client.post(
            reverse("account-register"),
            self.payload(
                username="doctest1",
                email="doc@example.com",
                phone="+15001234567",
                dob="1995-01-01",
                guardian=False,
                verification_token=token,
            ),
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        user = User.objects.get(email="doc@example.com")
        self.assertEqual(user.verification_status, "pending")
        verification = Verification.objects.get(user=user)
        self.assertEqual(verification.provider, "document")
        self.assertFalse(user.age_verified)

    def test_expired_upload_token_rejected(self):
        upload_resp = self.client.post(
            reverse("verification-upload"),
            {"document": self._fake_png()},
            format="multipart",
        )
        token = upload_resp.data["verification_token"]
        upload = IdentityDocumentUpload.objects.get(token=token)
        from django.utils import timezone as tz

        upload.expires_at = tz.now() - tz.timedelta(days=2)
        upload.save()
        resp = self.client.post(
            reverse("account-register"),
            self.payload(
                username="expired1",
                email="exp@example.com",
                phone="+15009876543",
                dob="1995-01-01",
                guardian=False,
                verification_token=token,
            ),
            format="json",
        )
        self.assertIn(resp.status_code, (400, 422))
        self.assertEqual(User.objects.count(), 0)


class DbUniqueConstraintTests(TestCase):
    def test_vector_id_unique_constraint(self):
        u1 = User.objects.create_user(
            email="a@example.com", username="two_vec_a", password="secret-pass-99",
            full_name="A", date_of_birth=date(2000, 1, 1),
        )
        u1.vector_id = "VS-AAAAAAAA"
        u1.save(update_fields=["vector_id"])
        u2 = User(email="b@example.com", username="two_vec_b", vector_id="VS-AAAAAAAA")
        u2.set_password("secret-pass-99")
        with self.assertRaises(Exception):
            u2.save()

    def test_create_user_persists_allocated_vector_id(self):
        u1 = User.objects.create_user(
            email="vec_one@example.com", username="vec_one", password="secret-pass-99",
            full_name="Vec One", date_of_birth=date(2000, 1, 1),
        )
        u2 = User.objects.create_user(
            email="vec_two@example.com", username="vec_two", password="secret-pass-99",
            full_name="Vec Two", date_of_birth=date(2000, 1, 1),
        )
        self.assertTrue(u1.vector_id)
        self.assertTrue(u2.vector_id)
        self.assertNotEqual(u1.vector_id, u2.vector_id)
        self.assertFalse(
            User.objects.filter(vector_id="").exists(),
            "create_user must never persist an empty vector_id (UNIQUE column).",
        )

    def test_username_email_phone_unique(self):
        User.objects.create_user(
            email="one@example.com", username="unique_user", password="secret-pass-99",
            phone="+15550000001", full_name="One", date_of_birth=date(2000, 1, 1),
        )
        for idx, (field, value) in enumerate([
            ("username", "unique_user"),
            ("email", "one@example.com"),
            ("phone", "+15550000001"),
        ]):
            dup_kwargs = {
                "email": f"dup_{field}_{idx}@example.com",
                "username": f"another_user_{idx}",
                "phone": f"+1555{idx:03d}00002",
                "full_name": "Dup",
                "date_of_birth": date(2000, 1, 1),
            }
            dup_kwargs[field] = value  # force the duplicate value
            dup = User(**dup_kwargs)
            dup.set_password("secret-pass-99")
            with self.assertRaises(Exception):
                dup.save()


class ConfigurationApiTests(APITestCase):
    def test_onboarding_config_contains_catalog(self):
        resp = self.client.get(reverse("onboarding-config"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["min_interests"], 3)
        self.assertEqual(resp.data["guardian_age_threshold"], 17)
        self.assertGreaterEqual(len(resp.data["interests"]), 18)
        self.assertGreaterEqual(len(resp.data["play_styles"]), 7)
        self.assertEqual(resp.data["age_ranges"][0]["value"], "6-9")

    def test_interests_endpoint(self):
        resp = self.client.get(reverse("interests"))
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(resp.data["count"], 18)


class SessionTests(APITestCase):
    def _create_account(self, username, email, phone):
        self.client.post(
            reverse("account-register"),
            {
                "full_name": "Login Tester",
                "username": username,
                "email": email,
                "phone": phone,
                "date_of_birth": "2014-01-01",
                "password": "supersecret99",
                "interests": ["mathematics", "space", "logic"],
                "play_styles": ["puzzle-solver"],
                "terms_accepted": True,
                "guardian_email": "guardian@example.com",
            },
            format="json",
        )

    def test_session_anonymous(self):
        resp = self.client.get(reverse("auth-session"))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data["authenticated"])

    def test_login_and_me(self):
        self._create_account("loginuser", "login@example.com", "+15558889999")
        resp = self.client.post(
            reverse("auth-login"),
            {"identifier": "login@example.com", "password": "supersecret99"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(resp.data["authenticated"])
        me = self.client.get(reverse("account-me"))
        self.assertEqual(me.status_code, 200)
        self.assertRegex(me.data["vector_id"], r"^VS-")

    def test_login_wrong_password_friendly(self):
        self._create_account("friendlyuser", "friendly@example.com", "+15557778888")
        resp = self.client.post(
            reverse("auth-login"),
            {"identifier": "friendly@example.com", "password": "wrong-password-x"},
            format="json",
        )
        self.assertIn(resp.status_code, (400, 422))
        self.assertIn("identifier", str(resp.data))


# ---------------------------------------------------------------------------
# Phase 7 — real authentication (JWT access + rotating refresh), e-mail /
# phone verification and password recovery.
# ---------------------------------------------------------------------------
class Phase7AuthTests(APITestCase):
    def _create_account(self, username, email, phone, dob="2014-01-01"):
        self.client.post(
            reverse("account-register"),
            {
                "full_name": "Phase7 Tester",
                "username": username,
                "email": email,
                "phone": phone,
                "date_of_birth": dob,
                "password": "supersecret99",
                "interests": ["mathematics", "space", "logic"],
                "play_styles": ["puzzle-solver"],
                "terms_accepted": True,
                "guardian_email": "guardian@example.com",
            },
            format="json",
        )

    def _login(self, identifier, password="supersecret99", **extra):
        return self.client.post(
            reverse("auth-login"),
            {"identifier": identifier, "password": password},
            format="json",
        )

    def _refresh(self, refresh_token=None):
        body = {"refresh": refresh_token} if refresh_token else {}
        return self.client.post(reverse("token-refresh"), body, format="json")

    def test_register_returns_access_token_and_refresh_cookie(self):
        self._mock_email_backend()
        resp = self.client.post(
            reverse("account-register"),
            {
                "full_name": "Token Tester",
                "username": "tokenuser",
                "email": "token@example.com",
                "phone": "+15550001111",
                "date_of_birth": "2014-01-01",
                "password": "supersecret99",
                "interests": ["mathematics", "space", "logic"],
                "play_styles": ["puzzle-solver"],
                "terms_accepted": True,
                "guardian_email": "guardian@example.com",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertIn("access", resp.data)
        self.assertTrue(resp.data["access"])
        refresh_cookie = self.client.cookies.get("vs_refresh")
        self.assertIsNotNone(refresh_cookie)
        self.assertTrue(refresh_cookie.value)

    def test_login_returns_access_token_and_refresh_cookie(self):
        self._create_account("jwtuser", "jwt@example.com", "+15550002222")
        resp = self._login("jwt@example.com")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertIn("access", resp.data)
        self.assertIsNotNone(self.client.cookies.get("vs_refresh"))

    def test_login_by_each_identifier_form(self):
        self._create_account("vectorman", "vec@example.com", "+15550003333")
        user = User.objects.get(email="vec@example.com")
        for ident in ["vectorman", "vec@example.com", user.vector_id]:
            resp = self._login(ident)
            self.assertEqual(resp.status_code, 200, f"login failed via {ident}")
            self.assertTrue(resp.data["authenticated"])

    def test_login_incorrect_password_friendly(self):
        self._create_account("wrongpass", "wrong@example.com", "+15550004444")
        resp = self._login("wrong@example.com", password="not-the-password")
        self.assertIn(resp.status_code, (400, 422))
        self.assertIn("identifier", str(resp.data))
        self.assertNotIn("access", resp.data)

    def test_login_suspended_account_rejected(self):
        self._create_account("suspendme", "suspend@example.com", "+15550005555")
        User.objects.filter(email="suspend@example.com").update(account_status="suspended")
        resp = self._login("suspendme")
        self.assertIn(resp.status_code, (400, 422))
        self.assertIn("suspended", str(resp.data).lower())

    def test_login_deactivated_account_rejected(self):
        self._create_account("deactme", "deact@example.com", "+15550006666")
        User.objects.filter(email="deact@example.com").update(is_active=False)
        resp = self._login("deactme")
        self.assertIn(resp.status_code, (400, 422))

    def test_me_protected_requires_access_token(self):
        resp = self.client.get(reverse("account-me"))
        self.assertEqual(resp.status_code, 401)

        self._create_account("tokenme", "me@example.com", "+15550007777")
        login_resp = self._login("tokenme")
        access = login_resp.data["access"]
        me = self.client.get(
            reverse("account-me"), HTTP_AUTHORIZATION=f"Bearer {access}"
        )
        self.assertEqual(me.status_code, 200, me.content)
        self.assertRegex(me.data["vector_id"], r"^VS-")

    def test_refresh_rotates_and_blacklists(self):
        self._mock_email_backend()
        self._create_account("rotator", "rotate@example.com", "+15550008888")
        self._logout_clear()
        login_resp = self._login("rotator")
        first_refresh = login_resp.cookies.get("vs_refresh").value

        refreshed = self._refresh(first_refresh)
        self.assertEqual(refreshed.status_code, 200, refreshed.content)
        self.assertIn("access", refreshed.data)
        new_refresh = refreshed.cookies.get("vs_refresh").value
        self.assertNotEqual(first_refresh, new_refresh)

        # The old refresh token is now blacklisted and must be refused.
        again = self._refresh(first_refresh)
        self.assertIn(again.status_code, (401, 422))
        self.assertNotIn("access", again.data if isinstance(again.data, dict) else {})

    def test_logout_blacklists_refresh(self):
        self._mock_email_backend()
        self._create_account("logoutbob", "bob@example.com", "+15550009999")
        self._logout_clear()
        login_resp = self._login("logoutbob")
        refresh = login_resp.cookies.get("vs_refresh").value

        out = self.client.post(reverse("auth-logout"), {}, format="json")
        self.assertIn(out.status_code, (200, 400))
        later = self._refresh(refresh)
        self.assertIn(later.status_code, (401, 422))

    def _logout_clear(self):
        self.client.cookies.clear()

    def _mock_email_backend(self):
        from django.test import override_settings

        cm = override_settings(
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
        )
        cm.enable()
        self.addCleanup(cm.disable)
        return cm

    def test_email_verification_flow(self):
        self._mock_email_backend()
        self._create_account("mailtester", "mail@example.com", "+15551110000")
        user = User.objects.get(email="mail@example.com")
        # A one-time token is issued at registration (architecture step:
        # create → verification request → email sent).
        from apps.accounts.models import OneTimeToken

        token_row = OneTimeToken.objects.filter(
            user=user, purpose="email_verification", used_at__isnull=True
        ).first()
        self.assertIsNotNone(token_row)

        # The confirm endpoint validates the server-side stored hash. The raw
        # value is never persisted, so simulate the exact digest the mailer
        # would have delivered is impractical — issue a new one instead.
        from apps.accounts.authservices import issue_one_time_token

        raw, _ = issue_one_time_token(user, "email_verification")
        resp = self.client.post(
            reverse("email-verify-confirm"), {"token": raw}, format="json"
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        user.refresh_from_db()
        self.assertTrue(user.email_verified)

        # Single-use: consuming the same token again must fail.
        resp = self.client.post(
            reverse("email-verify-confirm"), {"token": raw}, format="json"
        )
        self.assertIn(resp.status_code, (400, 422))

    def test_password_reset_flow(self):
        import re

        from django.core.mail import outbox

        self._mock_email_backend()
        self._create_account("resetuser", "reset@example.com", "+15552220000")
        user = User.objects.get(email="reset@example.com")

        resp = self.client.post(
            reverse("password-reset-request"),
            {"identifier": "reset@example.com"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertTrue(outbox, "a reset e-mail should have been sent")

        match = re.search(r"token=([A-Za-z0-9_-]+)", outbox[-1].body)
        self.assertIsNotNone(match, "reset link should carry the token")
        raw = match.group(1)

        before = user.password
        resp = self.client.post(
            reverse("password-reset-confirm"),
            {"token": raw, "new_password": "brandNewPass99"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        user.refresh_from_db()
        self.assertNotEqual(user.password, before)
        self.assertTrue(user.check_password("brandNewPass99"))

        # Reused token must fail.
        resp = self.client.post(
            reverse("password-reset-confirm"),
            {"token": raw, "new_password": "anotherNew99"},
            format="json",
        )
        self.assertIn(resp.status_code, (400, 422))

    def test_password_reset_request_never_enumerates(self):
        self._mock_email_backend()
        for ident in ["ghost-account", "nobody@nowhere.example"]:
            resp = self.client.post(
                reverse("password-reset-request"), {"identifier": ident}, format="json"
            )
            self.assertEqual(resp.status_code, 200, resp.content)
            self.assertEqual(resp.data, {"sent": True})

    def test_phone_verification_flow(self):
        self._create_account("phoneman", "phone@example.com", "+15553330000")
        login_resp = self._login("phoneman")
        access = login_resp.data["access"]
        headers = {"HTTP_AUTHORIZATION": f"Bearer {access}"}

        req = self.client.post(
            reverse("phone-verify-request"),
            {"phone": "+15554445555"},
            format="json",
            **headers,
        )
        self.assertEqual(req.status_code, 200, req.content)
        self.assertTrue(req.data["development"])
        self.assertIsNotNone(req.data["dev_code"])

        confirm = self.client.post(
            reverse("phone-verify-confirm"),
            {"code": req.data["dev_code"]},
            format="json",
            **headers,
        )
        self.assertEqual(confirm.status_code, 200, confirm.content)
        self.assertTrue(confirm.data["verified"])
        user = User.objects.get(email="phone@example.com")
        self.assertTrue(user.phone_verified)
        self.assertEqual(user.phone, "+15554445555")

    def test_phone_verify_wrong_code_friendly(self):
        self._create_account("phonefail", "pfail@example.com", "+15556660000")
        login_resp = self._login("phonefail")
        access = login_resp.data["access"]
        headers = {"HTTP_AUTHORIZATION": f"Bearer {access}"}
        self.client.post(
            reverse("phone-verify-request"), {"phone": "+15557778888"}, format="json", **headers
        )
        confirm = self.client.post(
            reverse("phone-verify-confirm"), {"code": "000000"}, format="json", **headers
        )
        self.assertIn(confirm.status_code, (400, 422))
        user = User.objects.get(email="pfail@example.com")
        self.assertFalse(user.phone_verified)