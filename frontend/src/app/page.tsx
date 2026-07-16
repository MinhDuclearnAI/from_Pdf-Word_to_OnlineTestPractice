"use client";
import React from "react";
import Link from "next/link";
import useAuth from "@/hooks/useAuth";
import { Brain, FileText, BarChart3, GraduationCap } from "lucide-react";

export default function Home() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between">
      {/* Navbar */}
      <header className="max-w-7xl mx-auto w-full px-6 py-5 flex items-center justify-between border-b border-slate-900">
        <div className="flex items-center gap-2">
          <GraduationCap className="text-brand-500" size={32} />
          <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-slate-100 to-slate-400 bg-clip-text text-transparent">
            AI Exam Platform
          </span>
        </div>
        <nav className="flex items-center gap-4">
          {user ? (
            <Link
              href="/dashboard"
              className="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-semibold rounded-lg shadow-lg shadow-brand-500/20 transition-all duration-200"
            >
              Vào hệ thống
            </Link>
          ) : (
            <>
              <Link href="/login" className="text-sm font-semibold text-slate-350 hover:text-slate-100 transition-colors">
                Đăng nhập
              </Link>
              <Link
                href="/register"
                className="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-semibold rounded-lg shadow-lg shadow-brand-500/20 transition-all duration-200"
              >
                Đăng ký
              </Link>
            </>
          )}
        </nav>
      </header>

      {/* Hero Section */}
      <main className="flex-grow max-w-7xl mx-auto w-full px-6 py-20 flex flex-col items-center justify-center text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-brand-500/10 border border-brand-500/20 rounded-full text-brand-400 text-xs font-semibold mb-6">
          <Brain size={14} /> Trợ lý AI chấm thi & Luyện tập tối tân
        </div>
        <h1 className="text-4xl sm:text-6xl font-black tracking-tight max-w-3xl leading-tight mb-6 bg-gradient-to-b from-slate-100 to-slate-400 bg-clip-text text-transparent">
          Bóc Tách File Đề Thi & Chấm Bài Tự Luận Bằng AI
        </h1>
        <p className="text-slate-400 text-lg sm:text-xl max-w-2xl leading-relaxed mb-10">
          Chỉ cần tải lên file PDF/Word đề kiểm tra vật lý, hệ thống AI sẽ tự động phân loại, trích xuất câu hỏi, tạo bài thi trực tuyến và chấm điểm chi tiết bằng Claude.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 mb-20 w-full sm:w-auto">
          {user ? (
            <Link
              href="/dashboard"
              className="px-8 py-3.5 bg-brand-500 hover:bg-brand-600 text-white text-base font-bold rounded-lg shadow-lg shadow-brand-500/20 transition-all duration-200"
            >
              Vào Dashboard làm bài
            </Link>
          ) : (
            <>
              <Link
                href="/register"
                className="px-8 py-3.5 bg-brand-500 hover:bg-brand-600 text-white text-base font-bold rounded-lg shadow-lg shadow-brand-500/20 transition-all duration-200"
              >
                Bắt đầu miễn phí
              </Link>
              <Link
                href="/login"
                className="px-8 py-3.5 bg-slate-900 border border-slate-800 hover:bg-slate-800/80 text-slate-200 text-base font-bold rounded-lg transition-all duration-200"
              >
                Trải nghiệm Demo
              </Link>
            </>
          )}
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full">
          <div className="glass-card rounded-xl p-6 border border-slate-800 text-left">
            <div className="p-3 bg-brand-500/10 rounded-lg text-brand-400 w-fit mb-4">
              <FileText size={24} />
            </div>
            <h3 className="font-bold text-lg text-slate-100 mb-2">Bóc tách tự động</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Trích xuất đề kiểm tra từ file PDF scan hoặc Word thành bài thi online chỉ trong vài giây thông qua pipeline AI 2 bước.
            </p>
          </div>

          <div className="glass-card rounded-xl p-6 border border-slate-800 text-left">
            <div className="p-3 bg-brand-500/10 rounded-lg text-brand-400 w-fit mb-4">
              <Brain size={24} />
            </div>
            <h3 className="font-bold text-lg text-slate-100 mb-2">Chấm tự luận bằng Claude</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Tự động đối chiếu bài thi tự luận của học sinh với đáp án mẫu và chấm điểm theo rubric bằng mô hình AI tiên tiến.
            </p>
          </div>

          <div className="glass-card rounded-xl p-6 border border-slate-800 text-left">
            <div className="p-3 bg-brand-500/10 rounded-lg text-brand-400 w-fit mb-4">
              <BarChart3 size={24} />
            </div>
            <h3 className="font-bold text-lg text-slate-100 mb-2">Thống kê & Phổ điểm</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Hệ thống tự động vẽ biểu đồ phổ điểm, tính toán điểm trung bình/cao nhất/thấp nhất và xếp hạng kết quả lớp học.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="max-w-7xl mx-auto w-full px-6 py-8 border-t border-slate-900 text-center text-xs text-slate-500">
        © {new Date().getFullYear()} AI Exam Platform. All rights reserved.
      </footer>
    </div>
  );
}
