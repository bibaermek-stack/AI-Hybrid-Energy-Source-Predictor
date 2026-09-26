#!/usr/bin/env bash
# Drives the built APK on an Android emulator (see build-android.yml):
#   1. the app launches and stays up,
#   2. Back from a tab returns Home instead of closing the app,
#   3. Back from a More screen returns to More,
#   4. Back on Home closes the app,
#   5. the camera opens and a capture reaches the diagnosis (reported, not fatal).
# Screenshots, UI dumps and logcat go to $OUT for the workflow artifact.
set -uo pipefail

OUT="${OUT:-emulator-artifacts}"
mkdir -p "$OUT"
UI="python3 scripts/android_ui.py"

APK="$(ls mobile/build/apk/*.apk | head -n 1)"
BUILD_TOOLS="$(ls -d "$ANDROID_HOME"/build-tools/* | sort -V | tail -n 1)"
PKG="$("$BUILD_TOOLS/aapt2" dump packagename "$APK")"
echo "APK=$APK PKG=$PKG"

failures=0
pass() { echo "PASS: $*"; }
fail() { echo "FAIL: $*"; failures=$((failures + 1)); }
shot() { adb exec-out screencap -p > "$OUT/$1.png"; adb shell uiautomator dump /sdcard/ui.xml >/dev/null 2>&1; adb exec-out cat /sdcard/ui.xml > "$OUT/$1.xml"; }
in_front() { adb shell dumpsys window | grep -E "mCurrentFocus=|mFocusedApp=" | grep -q "$PKG"; }
launch() {
  adb shell monkey -p "$PKG" -c android.intent.category.LAUNCHER 1 >/dev/null
  # Python start-up plus the splash and first health check take a while on
  # an emulator; wait for the bottom bar rather than a fixed delay.
  for _ in $(seq 1 60); do
    if $UI has "Басты" --prefix >/dev/null 2>&1; then return 0; fi
    sleep 3
  done
  return 1
}
tap_tab() {  # label, index
  $UI tap "$1" --prefix || $UI tab "$2"
}

adb install -r "$APK" || { echo "FAIL: install"; exit 1; }
# Pre-grant so the camera step is not stuck on the permission dialog.
adb shell pm grant "$PKG" android.permission.CAMERA || true
adb logcat -c

# 1. launch
if launch; then pass "app launched and shows the bottom bar"; else fail "app did not reach the home screen"; fi
sleep 5
shot 01_home
in_front && pass "app is in front after launch" || fail "app not in front after launch"

# 2. Back from the Forecast tab -> Home, app stays open
tap_tab "Болжам" 1
sleep 6
shot 02_forecast
adb shell input keyevent KEYCODE_BACK
sleep 4
shot 03_after_back_from_forecast
if in_front; then pass "Back on Forecast kept the app open"; else fail "Back on Forecast closed the app"; fi

# 3. Back from a More screen -> More
tap_tab "Тағы" 4
sleep 4
$UI tap "Баптаулар" --prefix || fail "Settings tile not found under More"
sleep 4
shot 04_settings
adb shell input keyevent KEYCODE_BACK
sleep 4
shot 05_after_back_from_settings
if in_front && $UI has "Барлық бөлімдер" >/dev/null; then
  pass "Back on Settings returned to More"
else
  fail "Back on Settings did not return to More"
fi

# 4. Back from More -> Home, then Back on Home -> app closes
adb shell input keyevent KEYCODE_BACK
sleep 4
adb shell input keyevent KEYCODE_BACK
sleep 4
shot 06_after_back_on_home
if in_front; then fail "Back on Home did not close the app"; else pass "Back on Home closed the app"; fi

# 5. camera (informational: the emulator's camera is a synthetic scene)
if launch; then
  tap_tab "Тағы" 4
  sleep 4
  $UI tap "YOLO" --prefix || echo "NOTE: YOLO tile not found"
  sleep 4
  if $UI tap "Камера" --prefix; then
    sleep 10
    shot 07_camera_preview
    $UI tap "Түсіру" --prefix || echo "NOTE: Capture button not found"
    sleep 25
    shot 08_after_capture
    echo "CAMERA: see 07_camera_preview.png / 08_after_capture.png"
  else
    echo "NOTE: Camera button not found"
    shot 07_no_camera_button
  fi
else
  echo "NOTE: relaunch for the camera step failed"
fi

adb logcat -d > "$OUT/logcat.txt"
grep -iE "Traceback|Exception|flutter.*error|FATAL" "$OUT/logcat.txt" | head -50 > "$OUT/logcat_errors.txt" || true
echo "---- logcat errors (first lines) ----"
head -20 "$OUT/logcat_errors.txt" || true

echo "failures: $failures"
exit "$failures"
