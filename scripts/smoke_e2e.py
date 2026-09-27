"""Full API-contract smoke test for the frontend integration.

Exercises every endpoint the React app calls, using a real cookie jar to
verify CSRF + session behavior, then runs the complete registration flow
(guardian + none branches) exactly as the frontend does.
"""
import http.cookiejar
import io
import json
import uuid
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1"
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

CSRF = {}


def call(path, method="GET", body=None, form=None, token=None, raw=False):
    url = BASE + path
    data = None
    headers = {}
    if form is not None:
        boundary = uuid.uuid4().hex
        data = []
        for k, v in form.items():
            if isinstance(v, bytes):
                data.append(
                    (
                        f"--{boundary}\r\n"
                        f'Content-Disposition: form-data; name="{k}"; filename="doc.png"\r\n'
                        f"Content-Type: image/png\r\n\r\n"
                    ).encode()
                )
                data.append(v + b"\r\n")
            else:
                data.append(
                    (
                        f"--{boundary}\r\n"
                        f'Content-Disposition: form-data; name="{k}"\r\n\r\n'
                        f"{v}\r\n"
                    ).encode()
                )
        data.append(f"--{boundary}--\r\n".encode())
        data = b"".join(data)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    c = jar._cookies.get("127.0.0.1", {}).get("/", {})
    csrf = (c.get("csrftoken") or CSRF.get("csrftoken"))
    if csrf and method != "GET":
        headers["X-CSRFToken"] = csrf.value if csrf and not isinstance(csrf, str) else csrf
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with opener.open(req, timeout=12) as r:
            raw_data = r.read().decode()
            if raw:
                print(f"{method} {path} -> {r.status} (raw {len(raw_data)} bytes)")
                return raw_data
            payload = json.loads(raw_data) if raw_data else None
            print(f"{method} {path} -> {r.status}")
            return payload
    except urllib.error.HTTPError as err:
        raw_data = err.read().decode()
        print(f"{method} {path} -> {err.code} BODY: {raw_data[:1500]}")
        raise


def main():
    def step(label):
        print("\n=== " + label + " ===")

    # 1. CSRF bootstrap (real browser flow)
    step("CSRF bootstrap")
    req = urllib.request.Request(BASE + "/auth/csrf/")
    with opener.open(req, timeout=12) as r:
        payload = json.loads(r.read().decode())
    for c in jar:
        CSRF[c.name] = c
    print("csrf cookie:", bool(payload.get("csrfToken")), "| cookie jar:", [c.name for c in jar])

    # 2. Unauthenticated session
    step("Session (anon)")
    call("/auth/session/")

    # 3. Config
    step("Onboarding config")
    cfg = call("/onboarding/config/")
    adult_dob = "2000-01-01"  # 26 -> no guardian; default region -> no verification
    teen_dob = "2012-06-15"   # 14 -> guardian branch

    # 4. Age checks
    step("Age check adult")
    adult = call("/onboarding/age-check/", "POST", {"date_of_birth": adult_dob})
    print("  age:", adult["age"], "| branch:", adult["branch"])
    none_dob = "2009-01-01"  # 17 -> past guardian gate; IN region disables verification
    step("Age check 17 (region IN -> none)")
    nonecheck = call("/onboarding/age-check/", "POST", {"date_of_birth": none_dob, "region": "IN"})
    print("  age:", nonecheck["age"], "| branch:", nonecheck["branch"])
    step("Age check minor")
    teen = call("/onboarding/age-check/", "POST", {"date_of_birth": teen_dob})
    print("  age:", teen["age"], "| branch:", teen["branch"])

    # 5. Username check
    step("Username check")
    uname = f"smoke{uuid.uuid4().hex[:8]}"
    call("/username/check/", "POST", {"username": uname})
    phone = "+1" + str(uuid.uuid4().int)[-10:]

    # 6a. Full registration NONE branch (17yo, no phone) -> auto-login, Vector ID
    step("Register 17 (none branch, no phone)")
    reg = call(
        "/accounts/register/",
        "POST",
        {
            "full_name": "Smoke Tester",
            "username": uname,
            "email": f"{uname}@example.com",
            "phone": "",
            "date_of_birth": none_dob,
            "password": "supersecret99",
            "region": "IN",
            "age_group": "16-17",
            "interests": ["mathematics", "space", "logic"],
            "play_styles": ["puzzle-solver", "explore"],
            "terms_accepted": True,
        },
    )
    print("  vector_id:", reg["user"]["vector_id"], "| onboarding_complete:", reg["user"]["onboarding_completed"])
    print("  recommendations:", len(reg["recommendations"]))
    print("  register response access token:", bool(reg.get("access")))

    # 6b. Full registration VERIFICATION branch (adult + doc upload)
    step("Upload doc (verification branch)")
    png = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108020000009077")
    up = call("/verification/upload/", "POST", form={"document": png, "region": "US"})
    token = up["verification_token"]
    print("  upload token:", token[:8], "... | expires_hours:", up["expires_in_hours"])
    regA = call(
        "/accounts/register/",
        "POST",
        {
            "full_name": "Adult Smoker",
            "username": f"{uname}x",
            "email": f"{uname}x@example.com",
            "phone": phone,
            "date_of_birth": adult_dob,
            "password": "supersecret99",
            "region": "US",
            "interests": ["coding", "strategy", "puzzles"],
            "play_styles": ["fast-competitive"],
            "terms_accepted": True,
            "verification_token": token,
        },
    )
    print("  adult vector_id:", regA["user"]["vector_id"], "| verification:", regA["user"]["verification_status"])

    # 7. Authenticated session follows the register cookie
    step("Session (authenticated)")
    sess = call("/auth/session/")
    print("  authenticated:", sess["authenticated"], "| uuid fields:", [k for k in sess["user"].keys()])

    # 8. First experience (authenticated)
    step("First experience")
    fe = call("/onboarding/first-experience/")
    print("  interests:", fe["interests"])

    # 9. Logout then login
    step("Logout")
    call("/auth/logout/", "POST")
    step("Login")
    call("/auth/login/", "POST", {"identifier": f"{uname}@example.com", "password": "supersecret99"})
    sess2 = call("/auth/session/")
    print("  re-authenticated:", sess2["authenticated"])

    # 10. Minor (guardian) full registration
    step("Guardian branch register (minor, no upload needed)")
    reg2 = call(
        "/accounts/register/",
        "POST",
        {
            "full_name": "Teen Smoker",
            "username": f"{uname}2",
            "email": f"{uname}2@example.com",
            "phone": "",
            "date_of_birth": teen_dob,
            "password": "supersecret99",
            "region": "",
            "interests": ["science", "puzzles", "logic"],
            "play_styles": ["challenge-myself"],
            "terms_accepted": True,
            "guardian_email": "parent@example.com",
            "guardian_name": "Parent",
        },
    )
    print("  teen vector_id:", reg2["user"]["vector_id"], "| verification:", reg2["user"]["verification_status"])

    # 11. Phase 7 — JWT access + rotating refresh lifecycle
    step("Phase 7 JWT: login -> access token + /accounts/me")
    login_res = call(
        "/auth/login/", "POST", {"identifier": f"{uname}@example.com", "password": "supersecret99"}
    )
    access = login_res["access"]
    print("  access token present:", bool(access))
    me = call("/accounts/me/", token=access)
    print("  me via Bearer:", me["username"], me["vector_id"], "| status:", me["account_status"])

    step("Phase 7 JWT: refresh rotation + revocation")
    old_refresh = jar._cookies.get("127.0.0.1", {}).get("/api/v1/auth/", {}).get("vs_refresh")
    refreshed = call("/auth/token/refresh/", "POST", {})
    print("  rotated access present:", bool(refreshed.get("access")))
    try:
        call("/auth/token/refresh/", "POST", {"refresh": old_refresh.value})
        print("  OLD REFRESH REUSE ACCEPTED — ROTATION BROKEN")
    except urllib.error.HTTPError as err:
        print("  old refresh reuse rejected ->", err.code)

    step("Phase 7 logout revokes refresh")
    call("/auth/logout/", "POST")
    sess_after = call("/auth/session/")
    print("  authenticated after logout:", sess_after["authenticated"])

    # 12. Phase 7 — recovery + verification endpoints (authenticated as adult)
    step("Phase 7 password reset request + email verify (dev providers)")
    loginA = call(
        "/auth/login/",
        "POST",
        {"identifier": f"{uname}x@example.com", "password": "supersecret99"},
    )
    accessA = loginA["access"]
    call("/auth/password/reset/", "POST", {"identifier": f"{uname}x@example.com"})
    call("/auth/email/verify/request/", "POST", {}, token=accessA)

    step("Phase 7 phone verification (dev provider returns code)")
    new_phone = "+1" + str(uuid.uuid4().int)[-10:]
    ph = call("/auth/phone/verify/request/", "POST", {"phone": new_phone}, token=accessA)
    print("  dev_code returned:", bool(ph.get("dev_code")))
    confirm = call("/auth/phone/verify/", "POST", {"code": ph["dev_code"]}, token=accessA)
    print("  phone verified:", confirm["verified"])

    # 13. Phase 8 — Game Hub home feed (authenticated as adult)
    step("Phase 8 Home: authenticated feed")
    home = call("/home/", token=accessA)
    print("  user:", home["user"]["username"], "| vector_id:", home["user"]["vector_id"])
    print("  profile level:", home["profile"]["level"], "| rank:", home["profile"]["rank"])
    print("  avatar_url:", bool(home["profile"]["avatar_url"]))
    print("  stats:", home["stats"])
    print("  continue_playing:", len(home["continue_playing"]))
    print("  recommendations:", len(home["recommendations"]))
    print("  sections:", [s["key"] for s in home["sections"]])
    print("  categories:", len(home["categories"]))
    print("  games:", len(home["games"]))
    print("  trending available:", home["trending"]["available"])
    print("  new_games:", len(home["new_games"]))
    print("  daily_challenge active:", home["daily_challenge"]["active"])
    print("  missions:", len(home["missions"]))
    print("  achievements:", len(home["achievements"]))
    print("  events:", len(home["events"]))

    step("Phase 8 Home: unauthenticated -> 401")
    # Build a fresh opener with no cookies to simulate a truly unauthenticated browser
    import http.cookiejar as _cj
    import urllib.request as _req
    bare_jar = _cj.CookieJar()
    bare_opener = _req.build_opener(_req.HTTPCookieProcessor(bare_jar))
    bare_req = _req.Request(BASE + "/home/", method="GET")
    try:
        with bare_opener.open(bare_req, timeout=12) as r:
            print("  UNAUTHENTICATED ACCESS ACCEPTED — SECURITY BUG")
    except urllib.error.HTTPError as err:
        print("  correctly rejected:", err.code)

    step("Phase 8 avatar endpoint -> SVG")
    av = call("/auth/login/", "POST", {"identifier": f"{uname}@example.com", "password": "supersecret99"})
    av_access = av["access"]
    av_resp = call("/profile/avatar/", token=av_access, raw=True)
    print("  is SVG:", av_resp.startswith("<svg"))
    print("  has initials:", "<text" in av_resp)

    # 14. Phase 9 — Game Hub, category discovery, detail + play flow
    step("Phase 9 Hub: home feed")
    hub = call("/hub/", token=av_access)
    print("  categories:", len(hub["categories"]))
    print("  continue_running:", len(hub["continue_running"]))
    print("  recommended:", len(hub["recommended"]))
    print("  quick_runs:", len(hub["quick_runs"]), "| deep_runs:", len(hub["deep_runs"]))
    print("  new_drops:", len(hub["new_drops"]), "| challenge_mode:", len(hub["challenge_mode"]))
    print("  trending available:", hub["trending"]["available"])
    print("  first category:", hub["categories"][0]["ident"], hub["categories"][0]["label"])

    step("Phase 9 Hub: categories")
    cats = call("/hub/categories/", token=av_access)
    idents = [c["ident"] for c in cats["categories"][:6]]
    print("  identity idents:", idents)

    step("Phase 9 Hub: category LOGIX")
    cat = call("/hub/categories/logix/", token=av_access)
    print("  label:", cat["category"]["label"], "| accent:", cat["category"]["accent"])
    print("  featured:", len(cat["featured"]), "| quick_runs:", len(cat["quick_runs"]), "| deep_runs:", len(cat["deep_runs"]))
    print("  all games:", cat["games"]["total"], "| page results:", len(cat["games"]["results"]), "| has_more:", cat["games"]["has_more"])

    step("Phase 9 Hub: honest empty category (unknown ident)")
    ghost = call("/hub/categories/zzz-nowhere/", token=av_access)
    print("  label:", ghost["category"]["label"], "| games_count:", ghost["category"]["games_count"])

    step("Phase 9 Hub: search")
    found = call("/hub/search/?q=blitz", token=av_access)
    print("  game matches:", [g["slug"] for g in found["games"]])
    print("  category matches:", [c["ident"] for c in found["categories"]])

    step("Phase 9 Hub: catalog pagination")
    page1 = call("/hub/games/", token=av_access)
    page2 = call("/hub/games/?page=2", token=av_access)
    print("  p1:", len(page1["results"]), "| p2:", len(page2["results"]), "| p1 has_more:", page1["has_more"])

    step("Phase 9: game detail (fresh)")
    detail = call("/hub/games/prime-sweeper/", token=av_access)
    print("  title:", detail["title"], "| play_kind:", detail["play_kind"], "| difficulty_stars:", detail["difficulty_stars"])
    print("  play_count:", detail["play_count"], "| best_score:", detail["best_score"])
    print("  related:", len(detail["related_games"]), "| instructions:", bool(detail["instructions"]))

    step("Phase 9: start session")
    sess = call("/hub/games/prime-sweeper/sessions/", "POST", {}, token=av_access)
    sid = sess["session"]["id"]
    print("  session id:", str(sid)[:8], "| status:", sess["session"]["status"], "| score:", sess["session"]["score"])

    step("Phase 9: complete session")
    done = call(
        f"/hub/sessions/{sid}/complete/",
        "POST",
        {"score": 3200, "accuracy": 88, "level_reached": 6, "duration_seconds": 240, "outcome": "completed"},
        token=av_access,
    )
    print("  status:", done["status"], "| score:", done["score"], "| accuracy:", done["accuracy"])
    print("  level:", done["level_reached"], "| xp:", done["xp_earned"])

    step("Phase 9: idempotent repeat returns same result")
    again = call(
        f"/hub/sessions/{sid}/complete/",
        "POST",
        {"score": 1, "accuracy": 1, "level_reached": 1, "duration_seconds": 1, "outcome": "failed"},
        token=av_access,
    )
    print("  repeat xp identical:", again["xp_earned"] == done["xp_earned"])

    step("Phase 9: out-of-range payload is clamped, never trusted")
    sess2 = call("/hub/games/overclock/sessions/", "POST", {}, token=av_access)
    clamped = call(
        f"/hub/sessions/{sess2['session']['id']}/complete/",
        "POST",
        {"score": 999999, "accuracy": 321, "level_reached": 99, "duration_seconds": 999999, "outcome": "completed"},
        token=av_access,
    )
    print("  score:", clamped["score"], "| accuracy:", clamped["accuracy"], "| level:", clamped["level_reached"], "| duration:", clamped["duration_seconds"])

    step("Phase 9: detail now reflects the real run")
    detail2 = call("/hub/games/prime-sweeper/", token=av_access)
    print("  play_count:", detail2["play_count"], "| best_score:", detail2["best_score"], "| last run xp:", detail2["last_result"]["xp_earned"])

    step("Phase 9: hub feed picks up the run")
    hub2 = call("/hub/", token=av_access)
    running = hub2["continue_running"]
    print("  continue_running:", len(running), "| first:", running[0]["title"] if running else "none")

    print("\nALL SMOKE CHECKS COMPLETE")


if __name__ == "__main__":
    main()