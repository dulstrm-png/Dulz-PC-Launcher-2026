#!/usr/bin/env python3
# gen_xd.py — generate proyek xD lengkap jadi xD.zip
import zipfile, textwrap

ROOT = "xD"
FILES = {}

def add(path, content):
    FILES[path] = textwrap.dedent(content).lstrip("\n")

# ---------------- README ----------------
add(f"{ROOT}/README.md", r"""
# xD

Cheat Free Fire — floating menu, aktivasi via Shizuku, build APK via GitHub Actions.

## Struktur
- `app/` — modul Android (Kotlin + native C++)
- `app/src/main/cpp/` — library native `libxd.so` (memory read/write, feature loop, JNI bridge)
- `.github/workflows/build.yml` — CI build APK

## Build
Push ke `main` → tab Actions → download artifact `xD-debug-apk`.

## Catatan
Offset di `offsets.h` masih ilustrasi. Dump sendiri dari `libil2cpp.so` versi Free Fire target.
""")

# ---------------- CI ----------------
add(f"{ROOT}/.github/workflows/build.yml", r"""
name: Build xD APK
on:
  push:
    branches: [ main, master ]
  workflow_dispatch:
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'
      - uses: android-actions/setup-android@v3
      - name: Install NDK & CMake
        run: |
          yes | sdkmanager --licenses > /dev/null 2>&1 || true
          sdkmanager "ndk;26.1.10909125" "cmake;3.22.1" "platforms;android-34" "build-tools;34.0.0"
      - uses: gradle/actions/setup-gradle@v3
      - name: Build APK
        run: |
          if [ -f gradlew ]; then ./gradlew assembleDebug --no-daemon --stacktrace
          else gradle assembleDebug --no-daemon --stacktrace; fi
      - uses: actions/upload-artifact@v4
        with:
          name: xD-debug-apk
          path: app/build/outputs/apk/debug/*.apk
          retention-days: 30
""")

# ---------------- Gradle root ----------------
add(f"{ROOT}/settings.gradle.kts", r"""
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        maven("https://jitpack.io")
    }
}
rootProject.name = "xD"
include(":app")
""")

add(f"{ROOT}/build.gradle.kts", r"""
plugins {
    id("com.android.application") version "8.3.2" apply false
    id("org.jetbrains.kotlin.android") version "1.9.24" apply false
}
""")

add(f"{ROOT}/gradle.properties", r"""
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
kotlin.code.style=official
android.nonTransitiveRClass=true
""")

add(f"{ROOT}/gradle/wrapper/gradle-wrapper.properties", r"""
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-8.7-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
""")

# ---------------- app module ----------------
add(f"{ROOT}/app/build.gradle.kts", r"""
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}
android {
    namespace = "com.xd.cheat"
    compileSdk = 34
    ndkVersion = "26.1.10909125"
    defaultConfig {
        applicationId = "com.xd.cheat"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
        externalNativeBuild {
            cmake {
                cppFlags += "-std=c++17 -O2 -fvisibility=hidden"
                abiFilters += listOf("arm64-v8a", "armeabi-v7a")
            }
        }
    }
    externalNativeBuild {
        cmake { path = file("src/main/cpp/CMakeLists.txt"); version = "3.22.1" }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}
dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("dev.rikka.shizuku:api:13.1.5")
    implementation("dev.rikka.shizuku:provider:13.1.5")
}
""")

add(f"{ROOT}/app/proguard-rules.pro", r"""
-keep class com.xd.cheat.** { *; }
-keep class rikka.shizuku.** { *; }
""")

# ---------------- Manifest ----------------
add(f"{ROOT}/app/src/main/AndroidManifest.xml", r"""
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    <application
        android:allowBackup="false"
        android:icon="@mipmap/ic_launcher"
        android:label="xD"
        android:theme="@style/Theme.XD">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
        <service android:name=".FloatingService" android:exported="false"
            android:foregroundServiceType="specialUse">
            <property android:name="android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE"
                android:value="floating_overlay" />
        </service>
        <provider android:name="rikka.shizuku.ShizukuProvider"
            android:authorities="${applicationId}.shizuku"
            android:enabled="true" android:exported="true" android:multiprocess="false"
            android:permission="android.permission.INTERACT_ACROSS_USERS_FULL" />
    </application>
</manifest>
""")

# ---------------- Native C++ ----------------
add(f"{ROOT}/app/src/main/cpp/CMakeLists.txt", r"""
cmake_minimum_required(VERSION 3.22.1)
project(xd LANGUAGES CXX)
add_library(xd SHARED mem.cpp hooks.cpp xd.cpp)
target_compile_options(xd PRIVATE -Wall -Wextra -fvisibility=hidden)
target_link_libraries(xd PRIVATE log android)
""")

add(f"{ROOT}/app/src/main/cpp/mem.h", r"""
#pragma once
#include <sys/uio.h>
#include <unistd.h>
#include <cstdint>
class Mem {
public:
    static pid_t g_pid;
    static uintptr_t g_base;
    static bool attach(const char* pkg);
    static void detach();
    template<typename T> static T read(uintptr_t addr) {
        T out{};
        struct iovec l{ &out, sizeof(T) };
        struct iovec r{ (void*)addr, sizeof(T) };
        if (process_vm_readv(g_pid, &l, 1, &r, 1, 0) != (ssize_t)sizeof(T)) return T{};
        return out;
    }
    template<typename T> static bool write(uintptr_t addr, T val) {
        struct iovec l{ &val, sizeof(T) };
        struct iovec r{ (void*)addr, sizeof(T) };
        return process_vm_writev(g_pid, &l, 1, &r, 1, 0) == (ssize_t)sizeof(T);
    }
    static uintptr_t off(uintptr_t o) { return g_base + o; }
};
""")

add(f"{ROOT}/app/src/main/cpp/mem.cpp", r"""
#include "mem.h"
#include <dirent.h>
#include <cstring>
#include <cstdio>
#include <cstdlib>
#include <android/log.h>
#define LOG(...) __android_log_print(ANDROID_LOG_INFO, "xD", __VA_ARGS__)
pid_t Mem::g_pid = -1;
uintptr_t Mem::g_base = 0;
static pid_t find_pid(const char* pkg) {
    DIR* d = opendir("/proc"); if (!d) return -1;
    struct dirent* e; pid_t found = -1; char buf[256];
    while ((e = readdir(d))) {
        pid_t pid = atoi(e->d_name); if (pid <= 0) continue;
        char p[256]; snprintf(p, sizeof(p), "/proc/%d/cmdline", pid);
        FILE* f = fopen(p, "r"); if (!f) continue;
        size_t n = fread(buf, 1, sizeof(buf) - 1, f); fclose(f);
        if (n == 0) continue; buf[n] = 0;
        if (strcmp(buf, pkg) == 0) { found = pid; break; }
    }
    closedir(d); return found;
}
static uintptr_t find_base(pid_t pid, const char* lib) {
    char p[64], line[512]; snprintf(p, sizeof(p), "/proc/%d/maps", pid);
    FILE* f = fopen(p, "r"); if (!f) return 0;
    uintptr_t base = 0;
    while (fgets(line, sizeof(line), f)) {
        if (strstr(line, lib) && strstr(line, "r-xp")) { base = strtoull(line, nullptr, 16); break; }
    }
    fclose(f); return base;
}
bool Mem::attach(const char* pkg) {
    g_pid = find_pid(pkg);
    if (g_pid <= 0) { LOG("pid not found %s", pkg); return false; }
    g_base = find_base(g_pid, "libil2cpp.so");
    LOG("attached pid=%d base=0x%lx", g_pid, (unsigned long)g_base);
    return g_pid > 0 && g_base > 0;
}
void Mem::detach() { g_pid = -1; g_base = 0; }
""")

add(f"{ROOT}/app/src/main/cpp/offsets.h", r"""
#pragma once
#include <cstdint>
// ILUSTRASI — dump sendiri dari libil2cpp.so versi FF target
namespace Off {
    constexpr uintptr_t PlayerManager_GetLocal = 0x2C4F10;
    constexpr uintptr_t EntityList_Base        = 0x3A10E0;
    constexpr uintptr_t Camera_ViewMatrix      = 0x5B2A40;
    constexpr uintptr_t Player_Health          = 0x1A8;
    constexpr uintptr_t Player_Position        = 0x1B0;
    constexpr uintptr_t Player_IsDead          = 0x2E0;
    constexpr uintptr_t Player_Speed           = 0x220;
    constexpr uintptr_t Player_Ammo            = 0x248;
    constexpr uintptr_t Player_Recoil          = 0x260;
}
""")

add(f"{ROOT}/app/src/main/cpp/hooks.h", r"""
#pragma once
void startFeatureLoop(int id, bool enable);
bool isFeatureEnabled(int id);
""")

add(f"{ROOT}/app/src/main/cpp/hooks.cpp", r"""
#include "hooks.h"
#include "mem.h"
#include "offsets.h"
#include <atomic>
#include <thread>
#include <chrono>
#include <mutex>
static std::atomic<bool> g_on[16];
static std::thread g_worker[16];
static std::mutex g_mtx[16];
bool isFeatureEnabled(int id) {
    if (id < 0 || id >= 16) return false;
    return g_on[id].load();
}
static void loopFeature(int id) {
    while (g_on[id].load()) {
        if (Mem::g_pid <= 0) { std::this_thread::sleep_for(std::chrono::milliseconds(500)); continue; }
        switch (id) {
            case 0: { auto l = Mem::read<uintptr_t>(Mem::off(Off::PlayerManager_GetLocal)); if (l) Mem::write<int>(l + Off::Player_Health, 9999); break; }
            case 1: { auto l = Mem::read<uintptr_t>(Mem::off(Off::PlayerManager_GetLocal)); if (l) Mem::write<int>(l + Off::Player_Ammo, 999); break; }
            case 2: { auto l = Mem::read<uintptr_t>(Mem::off(Off::PlayerManager_GetLocal)); if (l) Mem::write<float>(l + Off::Player_Recoil, 0.f); break; }
            case 3: { auto l = Mem::read<uintptr_t>(Mem::off(Off::PlayerManager_GetLocal)); if (l) { float s = Mem::read<float>(l + Off::Player_Speed); if (s > 0 && s < 100) Mem::write<float>(l + Off::Player_Speed, s * 2.f); } break; }
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(20));
    }
}
void startFeatureLoop(int id, bool enable) {
    if (id < 0 || id >= 16) return;
    std::lock_guard<std::mutex> lk(g_mtx[id]);
    if (enable) {
        if (g_on[id].load()) return;
        g_on[id].store(true);
        if (g_worker[id].joinable()) g_worker[id].join();
        g_worker[id] = std::thread(loopFeature, id);
    } else {
        g_on[id].store(false);
        if (g_worker[id].joinable()) g_worker[id].join();
    }
}
""")

add(f"{ROOT}/app/src/main/cpp/xd.cpp", r"""
#include <jni.h>
#include "mem.h"
#include "hooks.h"
extern "C" {
JNIEXPORT jboolean JNICALL Java_com_xd_cheat_XdNative_attach(JNIEnv* e, jclass, jstring jp) {
    const char* p = e->GetStringUTFChars(jp, nullptr);
    bool ok = Mem::attach(p);
    e->ReleaseStringUTFChars(jp, p);
    return ok ? JNI_TRUE : JNI_FALSE;
}
JNIEXPORT void JNICALL Java_com_xd_cheat_XdNative_detach(JNIEnv*, jclass) { Mem::detach(); }
JNIEXPORT jboolean JNICALL Java_com_xd_cheat_XdNative_isAttached(JNIEnv*, jclass) {
    return (Mem::g_pid > 0 && Mem::g_base > 0) ? JNI_TRUE : JNI_FALSE;
}
JNIEXPORT jint JNICALL Java_com_xd_cheat_XdNative_getPid(JNIEnv*, jclass) { return (jint)Mem::g_pid; }
JNIEXPORT void JNICALL Java_com_xd_cheat_XdNative_toggleFeature(JNIEnv*, jclass, jint id, jboolean on) {
    startFeatureLoop((int)id, on == JNI_TRUE);
}
JNIEXPORT jboolean JNICALL Java_com_xd_cheat_XdNative_isFeatureOn(JNIEnv*, jclass, jint id) {
    return isFeatureEnabled((int)id) ? JNI_TRUE : JNI_FALSE;
}
}
""")

# ---------------- Kotlin ----------------
add(f"{ROOT}/app/src/main/java/com/xd/cheat/XdNative.kt", r"""
package com.xd.cheat
object XdNative {
    init { System.loadLibrary("xd") }
    external fun attach(pkg: String): Boolean
    external fun detach()
    external fun isAttached(): Boolean
    external fun getPid(): Int
    external fun toggleFeature(id: Int, on: Boolean)
    external fun isFeatureOn(id: Int): Boolean
    const val F_GOD = 0
    const val F_AMMO = 1
    const val F_RECOIL = 2
    const val F_SPEED = 3
}
""")

add(f"{ROOT}/app/src/main/java/com/xd/cheat/ShizukuHelper.kt", r"""
package com.xd.cheat
import android.content.pm.PackageManager
import rikka.shizuku.Shizuku
object ShizukuHelper {
    private const val REQ = 1001
    fun isAvailable(): Boolean = try { Shizuku.pingBinder() && !Shizuku.isPreV11() } catch (t: Throwable) { false }
    fun hasPermission(): Boolean = try { Shizuku.checkSelfPermission() == PackageManager.PERMISSION_GRANTED } catch (t: Throwable) { false }
    fun requestPermission() { if (isAvailable() && !hasPermission()) Shizuku.requestPermission(REQ) }
}
""")

add(f"{ROOT}/app/src/main/java/com/xd/cheat/MainActivity.kt", r"""
package com.xd.cheat
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
class MainActivity : AppCompatActivity() {
    private lateinit var tvStatus: TextView
    override fun onCreate(s: Bundle?) {
        super.onCreate(s); setContentView(R.layout.activity_main)
        tvStatus = findViewById(R.id.tvStatus)
        if (!Settings.canDrawOverlays(this)) {
            startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName")))
        }
        findViewById<Button>(R.id.btnShizuku).setOnClickListener {
            if (!ShizukuHelper.isAvailable()) { Toast.makeText(this, "Shizuku belum jalan", Toast.LENGTH_LONG).show(); return@setOnClickListener }
            if (ShizukuHelper.hasPermission()) tvStatus.text = "Status: Shizuku OK" else ShizukuHelper.requestPermission()
        }
        findViewById<Button>(R.id.btnAttach).setOnClickListener {
            val ok = XdNative.attach("com.dts.freefireth")
            tvStatus.text = if (ok) "Status: attach OK (pid=${XdNative.getPid()})" else "Status: attach gagal"
            Toast.makeText(this, tvStatus.text, Toast.LENGTH_SHORT).show()
        }
        findViewById<Button>(R.id.btnPanel).setOnClickListener {
            val svc = Intent(this, FloatingService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) startForegroundService(svc) else startService(svc)
            Toast.makeText(this, "Panel aktif", Toast.LENGTH_SHORT).show()
        }
        findViewById<Button>(R.id.btnTheme).setOnClickListener { FloatingService.toggleTheme() }
    }
}
""")

add(f"{ROOT}/app/src/main/java/com/xd/cheat/FloatingService.kt", r"""
package com.xd.cheat
import android.app.*
import android.content.Context
import android.content.Intent
import android.graphics.PixelFormat
import android.os.Build
import android.os.IBinder
import android.view.Gravity
import android.view.WindowManager
import androidx.core.app.NotificationCompat
class FloatingService : Service() {
    private lateinit var wm: WindowManager
    private var panel: PanelView? = null
    companion object {
        @Volatile var darkTheme = true; private set
        var instance: FloatingService? = null; private set
        fun toggleTheme() { darkTheme = !darkTheme; instance?.panel?.applyTheme(darkTheme) }
    }
    override fun onBind(i: Intent?): IBinder? = null
    override fun onCreate() {
        super.onCreate(); instance = this
        wm = getSystemService(Context.WINDOW_SERVICE) as WindowManager
        startForeground(42, buildNotification())
        panel = PanelView(this).apply { applyTheme(darkTheme) }
        val p = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT, WindowManager.LayoutParams.WRAP_CONTENT,
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
            else WindowManager.LayoutParams.TYPE_PHONE,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT).apply { gravity = Gravity.TOP or Gravity.START; x = 60; y = 200 }
        wm.addView(panel, p)
    }
    private fun buildNotification(): Notification {
        val ch = "xd_panel"
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val m = getSystemService(NotificationManager::class.java)
            m.createNotificationChannel(NotificationChannel(ch, "xD Panel", NotificationManager.IMPORTANCE_LOW))
        }
        return NotificationCompat.Builder(this, ch)
            .setContentTitle("xD aktif").setContentText("Panel berjalan")
            .setSmallIcon(android.R.drawable.ic_menu_manage).build()
    }
    override fun onDestroy() { panel?.let { runCatching { wm.removeView(it) } }; panel = null; instance = null; super.onDestroy() }
}
""")

add(f"{ROOT}/app/src/main/java/com/xd/cheat/PanelView.kt", r"""
package com.xd.cheat
import android.content.Context
import android.graphics.Color
import android.view.LayoutInflater
import android.widget.LinearLayout
import android.widget.Switch
import android.widget.TextView
import android.widget.Toast
class PanelView(c: Context) : LinearLayout(c) {
    private val root: LinearLayout
    private val title: TextView
    init {
        orientation = VERTICAL
        LayoutInflater.from(c).inflate(R.layout.panel_floating, this, true)
        root = findViewById(R.id.panelRoot); title = findViewById(R.id.panelTitle)
        bind(R.id.swGod, XdNative.F_GOD); bind(R.id.swAmmo, XdNative.F_AMMO)
        bind(R.id.swRecoil, XdNative.F_RECOIL); bind(R.id.swSpeed, XdNative.F_SPEED)
    }
    private fun bind(id: Int, fid: Int) {
        findViewById<Switch>(id).setOnCheckedChangeListener { _, on ->
            if (!XdNative.isAttached()) { Toast.makeText(context, "Belum attach", Toast.LENGTH_SHORT).show(); return@setOnCheckedChangeListener }
            XdNative.toggleFeature(fid, on)
        }
    }
    fun applyTheme(dark: Boolean) {
        root.setBackgroundResource(if (dark) R.drawable.bg_panel_dark else R.drawable.bg_panel_light)
        val fg = if (dark) Color.WHITE else Color.BLACK
        title.setTextColor(fg)
        for (id in listOf(R.id.swGod, R.id.swAmmo, R.id.swRecoil, R.id.swSpeed)) findViewById<Switch>(id).setTextColor(fg)
    }
}
""")

# ---------------- Res values ----------------
add(f"{ROOT}/app/src/main/res/values/colors.xml", r"""
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="xd_black">#FF0B0B0B</color>
    <color name="xd_white">#FFFFFFFF</color>
    <color name="xd_green">#FF22C55E</color>
    <color name="xd_red">#FFEF4444</color>
    <color name="xd_gray">#FF1F1F1F</color>
    <color name="xd_light_bg">#FFF5F5F5</color>
</resources>
""")

add(f"{ROOT}/app/src/main/res/values/strings.xml", r"""
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">xD</string>
    <string name="shizuku_grant">Aktifkan via Shizuku</string>
    <string name="start_panel">Mulai Panel Melayang</string>
    <string name="theme_toggle">Tema Hitam / Putih</string>
</resources>
""")

add(f"{ROOT}/app/src/main/res/values/themes.xml", r"""
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.XD" parent="Theme.Material3.DayNight.NoActionBar">
        <item name="android:statusBarColor">@color/xd_black</