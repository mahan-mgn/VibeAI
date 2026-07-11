import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "vibeai_reminder";
const CHECK_INTERVAL_MS = 20_000;
const DEFAULT_SETTINGS = { enabled: false, time: "20:00", lastFiredDate: null };

function loadSettings() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_SETTINGS;
    return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
  } catch {
    return DEFAULT_SETTINGS;
  }
}

function saveSettings(settings) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  } catch {
    // localStorage در دسترس نیست (مثلا حالت خصوصی) - نادیده گرفته می‌شود
  }
}

function todayKey() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

const isNotificationSupported = typeof window !== "undefined" && "Notification" in window;

export default function useReminder() {
  const [settings, setSettings] = useState(loadSettings);
  const [permission, setPermission] = useState(
    isNotificationSupported ? Notification.permission : "unsupported"
  );

  const updateSettings = useCallback((partial) => {
    setSettings((prev) => {
      const next = { ...prev, ...partial };
      saveSettings(next);
      return next;
    });
  }, []);

  const requestPermission = useCallback(async () => {
    if (!isNotificationSupported) return "unsupported";
    const result = await Notification.requestPermission();
    setPermission(result);
    return result;
  }, []);

  const sendTestNotification = useCallback(() => {
    if (!isNotificationSupported || Notification.permission !== "granted") return false;
    const notification = new Notification("این یک نوتیفیکیشن آزمایشی است 🔔", {
      body: "اگر این پیام رو می‌بینی، نوتیفیکیشن مرورگر درست کار می‌کنه.",
      icon: "/favicon.svg",
    });
    notification.onclick = () => {
      window.focus();
      notification.close();
    };
    return true;
  }, []);

  // بررسی دوره‌ای برای فایر کردن یادآوری روزانه (فقط وقتی تب/مرورگر باز است)
  useEffect(() => {
    if (!isNotificationSupported) return;

    const check = () => {
      const current = loadSettings();
      if (!current.enabled || Notification.permission !== "granted") return;

      const today = todayKey();
      if (current.lastFiredDate === today) return;

      const now = new Date();
      const [hour, minute] = current.time.split(":").map(Number);
      const scheduled = new Date(now);
      scheduled.setHours(hour, minute, 0, 0);

      if (now >= scheduled) {
        const notification = new Notification("وقت چک‌این با VibeAI 💜", {
          body: "امروز حالت چطوره؟ بیا یه پیام بفرست تا پیشنهاد بدم.",
          icon: "/favicon.svg",
        });
        notification.onclick = () => {
          window.focus();
          notification.close();
        };
        const next = { ...current, lastFiredDate: today };
        saveSettings(next);
        setSettings(next);
      }
    };

    check();
    const interval = setInterval(check, CHECK_INTERVAL_MS);
    return () => clearInterval(interval);
  }, []);

  return {
    settings,
    updateSettings,
    permission,
    requestPermission,
    sendTestNotification,
    isSupported: isNotificationSupported,
  };
}
