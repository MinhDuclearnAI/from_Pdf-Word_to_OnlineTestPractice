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
      className="p-2 rounded-full bg-slate-800 text-slate-300 hover:text-brand-400 hover:bg-slate-700 transition-colors border border-slate-700 shadow-lg flex items-center justify-center fixed bottom-6 right-6 z-50"
      title={isLightMode ? "Chuyển sang Giao diện Tối" : "Chuyển sang Giao diện Sáng"}
    >
      {isLightMode ? <Moon size={24} /> : <Sun size={24} />}
    </button>
  );
}
