"""
Test Cases for VibeAI Mood Analysis Engine
حداقل 20 تست مطابق مستند پروژه (بخش 32)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mood.analyzer import MoodAnalyzer


def run_tests():
    analyzer = MoodAnalyzer()
    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"PASS - {name}")
        else:
            failed += 1
            print(f"FAIL - {name}")

    # 1. تشخیص خستگی ساده
    r = analyzer.analyze("خسته‌ام")
    check("تشخیص mood خستگی", r["mood"] == "tired")

    # 2. نفی خستگی
    r = analyzer.analyze("خسته نیستم")
    check("نفی خستگی -> neutral/fallback", r["mood"] == "neutral")

    # 3. تشخیص استرس
    r = analyzer.analyze("استرس دارم")
    check("تشخیص mood استرس", r["mood"] == "stressed")

    # 4. نفی استرس
    r = analyzer.analyze("استرس ندارم")
    check("نفی استرس -> neutral/fallback", r["mood"] == "neutral")

    # 5. فعالیت برنامه‌نویسی
    r = analyzer.analyze("دارم برنامه‌نویسی می‌کنم")
    check("تشخیص activity کدنویسی", r["activity"] == "coding")

    # 6. زمان: ساعت ۱ شب
    r = analyzer.analyze("الان ساعت ۱ شبه")
    check("تشخیص time_period شب از متن", r["time_period"] == "night")

    # 7. چند Mood همزمان: استرس و خستگی
    r = analyzer.analyze("استرس دارم و خسته‌ام")
    check("تشخیص چند mood (stressed dominant)", r["mood"] == "stressed")
    check("هر دو mood در moods وجود دارند", "tired" in r["moods"] and "stressed" in r["moods"])

    # 8. ناراحت نبودم (نفی غم)
    r = analyzer.analyze("ناراحت نبودم")
    check("نفی ناراحتی -> neutral/fallback", r["mood"] == "neutral")

    # 9. نه اینکه خسته باشم
    r = analyzer.analyze("نه اینکه خسته باشم ولی یه فیلم خوب می‌خوام")
    check("الگوی 'نه اینکه خسته باشم' شناسایی شود", "نه اینکه" in r["negations_detected"])

    # 10. تشخیص شادی
    r = analyzer.analyze("امروز خیلی خوشحالم")
    check("تشخیص mood شادی", r["mood"] == "happy")

    # 11. تشخیص آرامش
    r = analyzer.analyze("خیلی آرامش دارم و حس خوبیه")
    check("تشخیص mood آرامش", r["mood"] == "calm")

    # 12. تشخیص فعالیت مطالعه
    r = analyzer.analyze("دارم درس می‌خونم برای امتحان")
    check("تشخیص activity مطالعه", r["activity"] == "studying")

    # 13. تشخیص فعالیت ورزش
    r = analyzer.analyze("الان رفتم باشگاه ورزش می‌کنم")
    check("تشخیص activity ورزش", r["activity"] == "exercise")

    # 14. تشخیص انرژی پایین
    r = analyzer.analyze("خیلی خسته‌ام و انرژی ندارم")
    check("تشخیص energy پایین", r["energy"] == "low")

    # 15. تشخیص انرژی بالا
    r = analyzer.analyze("خیلی هیجان زده و پرانرژی هستم")
    check("تشخیص energy بالا", r["energy"] == "high")

    # 16. متن خنثی -> fallback
    r = analyzer.analyze("سلام چطوری")
    check("متن خنثی -> fallback با confidence پایین", r["confidence"] < 0.40 and r["mood"] == "neutral")

    # 17. متن خالی
    r = analyzer.analyze("")
    check("متن خالی -> fallback", r["mood"] == "neutral" and r["confidence"] == 0.30)

    # 18. استرس شدید (Content Safety)
    r = analyzer.analyze("استرس دارم استرس دارم خیلی استرس دارم")
    check(
        "Content Safety Layer برای استرس شدید فعال شود",
        analyzer.requires_safety_layer(r["mood"], r["moods"]) is True,
    )

    # 19. عدم false-positive برای 'ترس' داخل 'استرس'
    r = analyzer.analyze("امروز استرس داشتم")
    check("'ترس' داخل 'استرس' نباید anxious را فعال کند", "anxious" not in r["moods"])

    # 20. تشخیص هیجان (excited)
    r = analyzer.analyze("خیلی ذوق دارم و هیجان‌زده‌ام")
    check("تشخیص mood هیجان (excited)", r["mood"] == "excited")

    # 21. تشخیص دلشوره/نگرانی (anxious)
    r = analyzer.analyze("دلشوره دارم و خیلی نگرانم")
    check("تشخیص mood نگرانی (anxious)", r["mood"] == "anxious")

    # 22. تشخیص بی‌حوصلگی (bored)
    r = analyzer.analyze("حوصلم سر رفته خیلی")
    check("تشخیص mood بی‌حوصلگی (bored)", r["mood"] == "bored")

    # 23. اولویت زمان متن بر زمان سیستم
    r = analyzer.analyze("صبح بخیر، امروز چه روزیه")
    check("اولویت زمان ذکر شده در متن (صبح)", r["time_period"] == "morning")

    print(f"\n{passed} passed, {failed} failed out of {passed + failed}")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)