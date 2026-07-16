"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation"; 
import Link from "next/link";
import useAuth from "@/hooks/useAuth";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import { GraduationCap, AlertCircle } from "lucide-react";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter(); 
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    console.log("🚀 ĐÃ BẤM NÚT ĐĂNG NHẬP!", email, password); // <-- THÊM DÒNG NÀY
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await login(email, password);
      if (res.success) {
        router.push("/dashboard");              // THÊM — điều hướng khi thành công
      } else {
        setError(res.error || "Đăng nhập thất bại.");
      }
    } catch (err) {
      // THÊM — bắt lỗi network/CORS/backend chưa chạy, tránh "im lặng" không báo gì
      console.error("Lỗi khi gọi API đăng nhập:", err);
      setError("Không thể kết nối đến máy chủ. Vui lòng thử lại.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-slate-950">
      <div className="w-full max-w-md glass-panel rounded-2xl border border-slate-800 p-8 shadow-2xl space-y-6">
        <div className="flex flex-col items-center text-center space-y-2">
          <div className="p-3 bg-brand-500/10 rounded-full text-brand-500 border border-brand-500/20 mb-1">
            <GraduationCap size={28} />
          </div>
          <h2 className="text-2xl font-bold text-slate-100">Chào mừng trở lại</h2>
          <p className="text-sm text-slate-400">Đăng nhập tài khoản AI Exam Platform của bạn</p>
        </div>

        {error && (
          <div className="p-3 bg-red-950/40 border border-red-800/40 rounded-lg flex items-center gap-2.5 text-sm text-red-400">
            <AlertCircle size={18} className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Địa chỉ Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="example@exam.com"
            required
            disabled={loading}
          />
          <Input
            label="Mật khẩu"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
            disabled={loading}
          />
          <Button type="submit" variant="primary" className="w-full py-3 mt-2" disabled={loading}>
            {loading ? "Đang xử lý..." : "Đăng nhập"}
          </Button>
        </form>

        <div className="text-center text-sm text-slate-400">
          Chưa có tài khoản?{" "}
          <Link href="/register" className="text-brand-400 hover:text-brand-300 font-semibold transition-colors">
            Đăng ký ngay
          </Link>
        </div>
      </div>
    </div>
  );
}
