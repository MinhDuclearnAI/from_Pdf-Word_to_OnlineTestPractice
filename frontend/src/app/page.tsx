"use client";
import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import useAuth from "@/hooks/useAuth";
import Image from "next/image";
import { FileSearch, ClipboardCheck, TrendingUp, Facebook, Instagram, Bell, User as UserIcon, Mail, LogOut } from "lucide-react";

export default function Home() {
  const { user, logout } = useAuth();
  
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const profileMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (profileMenuRef.current && !profileMenuRef.current.contains(event.target as Node)) {
        setShowProfileMenu(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="min-h-screen bg-[#F4F8FB] text-slate-800 font-sans">
      {/* Navbar */}
      <header className="w-full bg-[#F4F8FB] px-8 md:px-16 py-6 flex items-center justify-between sticky top-0 z-30">
        <div className="flex items-center">
          <Link href="/">
            <div className="text-[#0052CC] font-black text-2xl tracking-tight cursor-pointer">
              TeecoAI
            </div>
          </Link>
        </div>
        <nav className="hidden md:flex items-center gap-10 font-bold text-gray-800 text-[15px]">
          <Link href="/" className="hover:text-[#0052CC] transition-colors">
            Trang chủ
          </Link>
          <Link href="/blogs" className="hover:text-[#0052CC] transition-colors">
            Blogs
          </Link>
          <Link href="/guide" className="hover:text-[#0052CC] transition-colors">
            Hướng dẫn
          </Link>
        </nav>
        <div className="flex items-center gap-6">
          {user ? (
            <div className="flex items-center gap-6">
              <button className="text-gray-600 hover:text-black">
                <Bell size={22} />
              </button>
              <div className="relative" ref={profileMenuRef}>
                <button
                  onClick={() => setShowProfileMenu(!showProfileMenu)}
                  className="w-12 h-12 rounded-full bg-[#0052CC] cursor-pointer hover:opacity-90 flex items-center justify-center text-white font-bold transition-opacity shadow-md"
                >
                  {user.full_name?.charAt(0) || user.email?.charAt(0).toUpperCase()}
                </button>
                
                {showProfileMenu && (
                  <div className="absolute right-0 top-full mt-3 w-72 bg-white border border-slate-100 rounded-2xl shadow-2xl z-50 overflow-hidden transform origin-top-right transition-all">
                    <div className="p-5 border-b border-slate-100 bg-slate-50">
                      <h4 className="font-bold text-slate-900 text-[17px] mb-1">{user.full_name || user.email}</h4>
                      <div className="flex items-center text-slate-500 text-xs font-medium">
                        <Mail size={12} className="mr-1.5" />
                        {user.email}
                      </div>
                    </div>
                    <div className="p-2">
                      <Link href="/dashboard">
                        <button className="w-full text-left px-4 py-3 text-sm font-semibold text-gray-700 hover:bg-gray-50 rounded-xl flex items-center gap-3 mb-1 transition-colors">
                           Vào Dashboard
                        </button>
                      </Link>
                      <button
                        onClick={logout}
                        className="w-full text-left px-4 py-3 text-sm font-semibold text-red-600 hover:bg-red-50 rounded-xl flex items-center gap-3 transition-colors"
                      >
                        <LogOut size={16} /> Đăng xuất
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-8">
              <Link
                href="/login"
                className="text-gray-800 font-bold text-[15px] hover:text-[#0052CC] transition-colors"
              >
                Đăng nhập
              </Link>
              <Link
                href="/register"
                className="px-7 py-3 bg-[#0052CC] hover:bg-blue-700 text-white text-[15px] font-bold rounded-full transition-all duration-200 shadow-md hover:-translate-y-0.5"
              >
                Đăng ký
              </Link>
            </div>
          )}
        </div>
      </header>

      {/* Hero Section */}
      <div 
        className="w-full bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: "url('/bg-hero.jpg')" }}
      >
        <main className="max-w-[1300px] mx-auto w-full px-8 md:px-16 pt-16 pb-24">
          <div className="flex flex-col md:flex-row items-center justify-between">
            <div className="md:w-[55%] pr-8">
              <h1 className="text-5xl md:text-[68px] font-extrabold text-[#0052CC] leading-[1.05] tracking-tight mb-8">
                Mọi đề bài.<br />Một nơi để làm.
              </h1>
              <p className="text-gray-600 font-medium text-[18px] md:text-[22px] leading-relaxed mb-10 max-w-[90%]">
                Biến đề PDF, Word hay tài liệu của bạn thành bài làm trực tuyến nhờ AI. Dành cho thầy cô giao bài và học sinh tự luyện tập.
              </p>

              <div className="flex items-center gap-6 mb-16">
                {user ? (
                  <Link
                    href="/dashboard"
                    className="px-10 py-4 bg-[#0052CC] hover:bg-blue-700 text-white text-[17px] font-bold rounded-full shadow-[0_8px_20px_rgba(0,82,204,0.3)] transition-all duration-300 hover:-translate-y-1"
                  >
                    Vào Dashboard
                  </Link>
                ) : (
                  <>
                    <Link
                      href="/register"
                      className="px-10 py-4 bg-[#0052CC] hover:bg-blue-700 text-white text-[17px] font-bold rounded-full shadow-[0_8px_20px_rgba(0,82,204,0.3)] transition-all duration-300 hover:-translate-y-1"
                    >
                      Bắt đầu ngay
                    </Link>
                    <Link
                      href="/dashboard"
                      className="text-gray-800 hover:text-[#0052CC] text-[17px] font-bold flex items-center gap-2 transition-colors"
                    >
                      Tìm hiểu thêm →
                    </Link>
                  </>
                )}
              </div>

              {/* Stats / Process Row */}
              <div className="flex flex-wrap gap-12 md:gap-20">
                <div>
                  <div className="font-extrabold text-gray-900 text-2xl mb-1">Upload</div>
                  <div className="text-gray-500 font-medium text-sm">chỉ trong vài giây</div>
                </div>
                <div>
                  <div className="font-extrabold text-gray-900 text-2xl mb-1">Chấm điểm</div>
                  <div className="text-gray-500 font-medium text-sm">AI tự động 100%</div>
                </div>
                <div>
                  <div className="font-extrabold text-gray-900 text-2xl mb-1">Kết quả</div>
                  <div className="text-gray-500 font-medium text-sm">thống kê chi tiết</div>
                </div>
              </div>
            </div>
            <div className="md:w-[45%] flex justify-end mt-16 md:mt-0">
              <Image
                src="/student_illustration.svg"
                alt="Học sinh đang học"
                width={650}
                height={500}
                className="object-contain"
                priority
              />
            </div>
          </div>
        </main>
      </div>

      {/* Feature Section */}
      <div className="mt-12 mb-16 max-w-[1300px] mx-auto w-full px-6">
          {/* Pills Box */}
          <div className="bg-white rounded-3xl p-8 mb-6 shadow-md border border-gray-100">
            <h2 className="text-[#0052CC] font-bold text-xl text-center mb-6">
              Hỗ trợ giao diện các loại đề thi môn học bất kì
            </h2>
            <div className="flex flex-wrap justify-center gap-6">
              {['Bài kiểm tra', 'THPTQG', 'IELTS', 'HSA', 'Tự luyện tập'].map((tag) => (
                <span
                  key={tag}
                  className="bg-[#DDEBFA] text-gray-800 px-8 py-2.5 rounded-full text-[15px] font-medium shadow-sm hover:shadow-md transition-shadow cursor-default"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* Cards Box */}
          <div className="bg-[#EAF2FF] rounded-3xl p-10 shadow-inner">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {/* Card 1 */}
              <div className="bg-white rounded-2xl p-8 flex flex-col items-center text-center shadow-xl hover:-translate-y-1 transition-all duration-300">
                <div className="w-16 h-16 bg-[#F0F6FF] rounded-xl flex items-center justify-center mb-6 text-[#0052CC] shadow-inner">
                  <FileSearch size={32} strokeWidth={1.5} />
                </div>
                <h3 className="font-black text-xl text-gray-900 mb-3">Bóc tách tự động</h3>
                <p className="text-gray-600 text-sm leading-relaxed">
                  Trích xuất đề thi từ file PDF scan thành bài thi online nhờ AI
                </p>
              </div>

              {/* Card 2 */}
              <div className="bg-white rounded-2xl p-8 flex flex-col items-center text-center shadow-xl hover:-translate-y-1 transition-all duration-300">
                <div className="w-16 h-16 bg-[#F0F6FF] rounded-xl flex items-center justify-center mb-6 text-[#0052CC] shadow-inner">
                  <ClipboardCheck size={32} strokeWidth={1.5} />
                </div>
                <h3 className="font-black text-xl text-gray-900 mb-3">AI chấm bài tự động</h3>
                <p className="text-gray-600 text-sm leading-relaxed">
                  Chấm tự động theo đáp án mẫu hoặc chấm tự luận theo barem sẵn nhờ AI
                </p>
              </div>

              {/* Card 3 */}
              <div className="bg-white rounded-2xl p-8 flex flex-col items-center text-center shadow-xl hover:-translate-y-1 transition-all duration-300">
                <div className="w-16 h-16 bg-[#F0F6FF] rounded-xl flex items-center justify-center mb-6 text-[#0052CC] shadow-inner">
                  <TrendingUp size={32} strokeWidth={1.5} />
                </div>
                <h3 className="font-black text-xl text-gray-900 mb-3">Thống kê kết quả</h3>
                <p className="text-gray-600 text-sm leading-relaxed">
                  Tự động đưa ra thống kê, biểu đồ, tính toán kết quả học tập.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="w-full border-t border-gray-200 bg-white mt-12">
          <div className="max-w-[1300px] mx-auto w-full px-6 py-10 flex flex-col md:flex-row justify-between text-[14px] text-gray-600">
            <div className="leading-relaxed">
              <p className="font-bold text-[#0052CC] text-lg mb-2">AI Exam Platform</p>
              <p>Sản phẩm thuộc một sinh viên AI-UET VNU</p>
              <p>Trụ sở: 1194, Phường Láng, Hà Nội</p>
              <p>SĐT: 0973908835</p>
              <p>Email: minhducteco@gmail.com</p>
            </div>
            <div className="flex flex-col items-start md:items-end gap-3 mt-8 md:mt-0">
              <span className="font-semibold text-gray-900">Theo dõi chúng tôi</span>
              <div className="flex gap-4 mt-2">
                <div className="w-10 h-10 bg-black text-white rounded-full flex items-center justify-center shadow-md hover:-translate-y-1 transition-transform cursor-pointer">
                  <span className="font-bold text-lg">X</span>
                </div>
                <div className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center shadow-md hover:-translate-y-1 transition-transform cursor-pointer">
                  <Facebook size={20} fill="currentColor" strokeWidth={0} />
                </div>
                <div className="w-10 h-10 bg-gradient-to-tr from-yellow-400 via-pink-500 to-purple-600 text-white rounded-full flex items-center justify-center shadow-md hover:-translate-y-1 transition-transform cursor-pointer">
                  <Instagram size={20} />
                </div>
              </div>
            </div>
          </div>
          <div className="border-t border-gray-100 py-5 text-center text-sm text-gray-500 bg-gray-50">
            © 2026 TeecoAI. All rights reserved.
          </div>
        </footer>
    </div>
  );
}

