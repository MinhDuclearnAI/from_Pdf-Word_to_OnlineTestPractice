"use client";
import React, { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";

export default function ThemeToggle() {
  const [isLightMode, setIsLightMode] = useState(false);

  useEffect(() => {
    // Check local storage on mount
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "light") {
      setIsLightMode(true);
      document.documentElement.classList.add("light-mode");
    }
  }, []);

  const toggleTheme = () => {
    if (isLightMode) {
      document.documentElement.classList.remove("light-mode");
      localStorage.setItem("theme", "dark");
      setIsLightMode(false);
    } else {
      document.documentElement.classList.add("light-mode");
      localStorage.setItem("theme", "light");
      setIsLightMode(true);
    }
  };

  return (
    <button
      onClick={toggleTheme}
      className="p-2.5 rounded-full bg-slate-900/90 text-slate-200 hover:text-brand-300 hover:bg-slate-800 hover:border-brand-500/50 transition-all border border-slate-700/80 shadow-2xl flex items-center justify-center fixed bottom-6 right-6 z-50 backdrop-blur"
      title={isLightMode ? "Chuyển sang Giao diện Đỏ Đô Tối" : "Chuyển sang Giao diện Sáng"}
    >
      {isLightMode ? <Moon size={20} /> : <Sun size={20} />}
    </button>
  );
}
