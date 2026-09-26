#!/usr/bin/env bash
# Drives the built APK on an Android emulator (see build-android.yml):
#   1. the app launches and stays up,
#   2. Back from a tab returns Home instead of closing the app,
#   3. Back from a More screen returns to More,
#   4. Back on Home closes the app,
#   5. the camera opens and a capture reaches the diagnosis,
#   6. the labs: the list loads, lab 1 runs on the server, Back returns to the
#      list, and lab 12's 3D model loads in the WebView with WebGL. Until the
#      server the APK talks to serves /labs this step is reported, not failed.
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
# Visible labels of a saved UI dump, one per line (for evidence in the log).
labels_of() { grep -oE '(text|content-desc)="[^"]+"' "$OUT/$1.xml" | sed -E 's/^[a-z-]+="//; s/"$//' | tr '\n' '|' ; echo; }
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
if in_front && grep -q "ЭкоЭнергия" "$OUT/03_after_back_from_forecast.xml"; then
  pass "Back on Forecast returned Home"
elif in_front; then
  fail "Back on Forecast kept the app open but did not show Home"
else
  fail "Back on Forecast closed the app"
fi

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
    echo "camera screen: $(labels_of 07_camera_preview)"
    if grep -q "Камера ашылмады" "$OUT/07_camera_preview.xml"; then
      fail "camera did not open"
    else
      $UI tap "Түсіру" --prefix || echo "NOTE: Capture button not found"
      sleep 25
      shot 08_after_capture
      echo "after capture: $(labels_of 08_after_capture)"
      if grep -qE "Анықталды|Ақау табылмады" "$OUT/08_after_capture.xml"; then
        pass "camera capture went through YOLO and got an answer"
      elif grep -q "Диагноз орындалмады" "$OUT/08_after_capture.xml"; then
        echo "NOTE: capture uploaded but the server did not diagnose it (see labels above)"
      else
        echo "NOTE: no diagnosis on screen after capture (see labels above)"
      fi
    fi
  else
    echo "NOTE: Camera button not found"
    shot 07_no_camera_button
  fi
else
  echo "NOTE: relaunch for the camera step failed"
fi

# 6. labs
labs_step() {
  launch || { echo "NOTE: relaunch for the labs step failed"; return; }
  tap_tab "Тағы" 4
  sleep 3
  $UI tap "Зертханалар" --prefix || { fail "Labs tile not found under More"; return; }
  local loaded=""
  for _ in $(seq 1 20); do
    if $UI has "Күн қуаты және ауа райы" --contains >/dev/null 2>&1; then loaded=yes; break; fi
    if $UI has "Зертханалар жүктелмеді" --contains >/dev/null 2>&1; then break; fi
    sleep 2
  done
  shot 09_labs_list
  if [ -z "$loaded" ]; then
    echo "NOTE: the labs list did not load: $(labels_of 09_labs_list)"
    echo "NOTE: the server the APK uses does not serve /labs yet (deploy main, then rerun)"
    return
  fi
  pass "labs list loaded from the server"

  $UI tap "Күн қуаты және ауа райы" --contains || { fail "lab 1 card not tappable"; return; }
  sleep 5
  $UI tap "Іске қосу" --prefix || fail "Run button not found in lab 1"
  local ran=""
  for _ in $(seq 1 15); do
    if $UI has "DC қуаты P_DC" --contains >/dev/null 2>&1; then ran=yes; break; fi
    sleep 2
  done
  shot 10_lab1_result
  [ -n "$ran" ] && pass "lab 1 ran on the server and shows its result" || fail "lab 1 result not shown: $(labels_of 10_lab1_result)"

  adb shell input keyevent KEYCODE_BACK
  sleep 3
  shot 11_after_back_from_lab
  if in_front && grep -q "12 зертхана" "$OUT/11_after_back_from_lab.xml"; then
    pass "Back in a lab returned to the labs list"
  else
    fail "Back in a lab did not return to the list"
  fi

  for _ in 1 2 3; do $UI swipe up; sleep 1; done
  $UI tap "Күн инверторы жүйесі 3D-де" --contains || { fail "lab 12 card not found"; return; }
  adb logcat -c
  local ready=""
  for _ in $(seq 1 30); do
    ready="$(adb logcat -d | grep -o 'LAB3D {[^}]*"type":"ready"[^}]*}' | tail -n 1)"
    [ -n "$ready" ] && break
    sleep 3
  done
  shot 12_lab3d
  echo "3D viewer: ${ready:-no LAB3D ready message}"
  echo "lab 12 screen: $(labels_of 12_lab3d)"
  if echo "$ready" | grep -q '"webgl":true'; then
    pass "3D model loaded in the WebView with WebGL"
  elif echo "$ready" | grep -q '"webgl":false'; then
    echo "NOTE: the viewer loaded but this emulator's WebView has no WebGL (software GPU)"
  else
    fail "the 3D viewer did not report ready"
  fi
}
labs_step

adb logcat -d > "$OUT/logcat.txt"
grep -iE "Traceback|Exception|flutter.*error|FATAL" "$OUT/logcat.txt" | head -50 > "$OUT/logcat_errors.txt" || true
echo "---- logcat errors (first lines) ----"
head -20 "$OUT/logcat_errors.txt" || true

echo "failures: $failures"
exit "$failures"
