import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bell, BellOff, Check, X } from "lucide-react";
import useReminder from "../hooks/useReminder";

export default function ReminderSettings({ isOpen, onClose }) {
  const { settings, updateSettings, permission, requestPermission, sendTestNotification, isSupported } =
    useReminder();
  const [testState, setTestState] = useState("idle"); // idle | sent

  const handleToggle = async () => {
    if (!settings.enabled) {
      const result = permission === "granted" ? "granted" : await requestPermission();
      if (result !== "granted") return;
    }
    updateSettings({ enabled: !settings.enabled });
  };

  const handleTest = () => {
    const sent = sendTestNotification();
    setTestState(sent ? "sent" : "idle");
    if (sent) setTimeout(() => setTestState("idle"), 4000);
  };

  const permissionMismatch = settings.enabled && permission !== "granted";

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
          />
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-label="تنظیمات یادآوری روزانه"
            className="fixed z-50 top-1/2 left-1/2 w-[90%] max-w-sm -translate-x-1/2 -translate-y-1/2
              glass-strong rounded-2xl p-5 border border-white/10"
            initial={{ opacity: 0, scale: 0.94 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.94 }}
            transition={{ duration: 0.18 }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Bell size={15} className="text-mood-neutral" />
                <h2 className="text-[13.5px] font-semibold text-white/85">یادآوری روزانه</h2>
              </div>
              <button
                onClick={onClose}
                className="flex items-center justify-center w-7 h-7 rounded-lg text-white/40 hover:text-white hover:bg-white/[0.06] transition-colors"
                aria-label="بستن"
              >
                <X size={14} />
              </button>
            </div>

            {!isSupported ? (
              <div className="flex items-center gap-2 text-[12px] text-white/40 py-4">
                <BellOff size={14} />
                مرورگر شما از نوتیفیکیشن پشتیبانی نمی‌کند.
              </div>
            ) : (
              <div className="flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-[12.5px] text-white/70">فعال کردن یادآوری</span>
                    <span
                      className={`text-[10px] font-medium px-1.5 py-[1px] rounded-full transition-colors duration-200
                        ${settings.enabled
                          ? "bg-emerald-500/15 text-emerald-400"
                          : "bg-white/[0.06] text-white/35"}`}
                    >
                      {settings.enabled ? "فعال" : "غیرفعال"}
                    </span>
                  </div>
                  <button
                    onClick={handleToggle}
                    aria-pressed={settings.enabled}
                    aria-label="فعال/غیرفعال کردن یادآوری روزانه"
                    className={`relative w-11 h-6 rounded-full transition-colors duration-200 cursor-pointer
                      ring-1 ring-inset
                      ${settings.enabled
                        ? "bg-emerald-500 ring-emerald-400/40"
                        : "bg-white/[0.10] ring-white/10"}`}
                  >
                    <motion.span
                      className="absolute top-[3px] w-[18px] h-[18px] rounded-full bg-white shadow-sm
                        flex items-center justify-center"
                      animate={{ right: settings.enabled ? "3px" : "calc(100% - 21px)" }}
                      transition={{ duration: 0.18 }}
                    >
                      {settings.enabled ? (
                        <Check size={11} strokeWidth={3} className="text-emerald-500" />
                      ) : (
                        <X size={11} strokeWidth={3} className="text-white/40" />
                      )}
                    </motion.span>
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-[12.5px] text-white/70">ساعت یادآوری</span>
                  <input
                    type="time"
                    value={settings.time}
                    onChange={(e) => updateSettings({ time: e.target.value })}
                    className="glass rounded-lg px-2.5 py-1.5 text-[12.5px] text-white/85 outline-none
                      focus:ring-1 focus:ring-mood-neutral/50 [color-scheme:dark]"
                  />
                </div>

                {permission === "denied" && (
                  <p className="text-[11px] text-mood-stressed/90 leading-relaxed">
                    مجوز نوتیفیکیشن رد شده. برای فعال‌سازی باید از تنظیمات مرورگر اجازه‌ی نوتیفیکیشن این سایت را بدهید.
                  </p>
                )}

                {permissionMismatch && permission !== "denied" && (
                  <p className="text-[11px] text-amber-400/90 leading-relaxed">
                    یادآوری فعاله ولی مجوز نوتیفیکیشن مرورگر تاییدشده نیست (وضعیت: {permission === "default" ? "هنوز درخواست نشده" : permission}).
                    یک بار خاموش/روشنش کن تا دوباره مجوز گرفته بشه.
                  </p>
                )}

                <div className="flex items-center justify-between border-t border-white/[0.06] pt-3">
                  <span className="text-[11px] text-white/40">
                    {testState === "sent" ? "ارسال شد — اگه ندیدیش، تنظیمات نوتیفیکیشن ویندوز/مرورگر رو چک کن." : "برای اطمینان یه نوتیف آزمایشی بفرست"}
                  </span>
                  <button
                    onClick={handleTest}
                    disabled={permission !== "granted"}
                    className="shrink-0 text-[11px] px-2.5 py-1.5 rounded-lg glass text-white/70 hover:text-white
                      hover:bg-white/[0.06] transition-colors disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:bg-transparent"
                  >
                    تست نوتیف
                  </button>
                </div>

                <p className="text-[10.5px] text-white/30 leading-relaxed border-t border-white/[0.06] pt-3">
                  این یادآوری فقط وقتی تب یا مرورگر باز باشد کار می‌کند (نوتیفیکیشن مرورگری، نه Push).
                </p>
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
