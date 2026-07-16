"use client";
import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import useAuth from "@/hooks/useAuth";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import { GraduationCap, AlertCircle, CheckCircle } from "lucide-react";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"student" | "teacher">("student");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);
  const [loading, setLoading] = useState(false);

  const [fullName, setFullName] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [school, setSchool] = useState("");
  const [workplace, setWorkplace] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const profile = {
      full_name: fullName,
      ...(role === "student" && { date_of_birth: dateOfBirth, school }),
      ...(role === "teacher" && { workplace }),
    };

    const res = await register(email, password, role, profile);
    if (res.success) {
      setSuccess(true);
      setTimeout(() => {
        router.push("/login");
      }, 2000);
    } else {
      setError(res.error || "Đăng ký tài khoản thất bại.");
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
          <h2 className="text-2xl font-bold text-slate-100">Tạo tài khoản mới</h2>
          <p className="text-sm text-slate-400">Đăng ký hệ thống thi trực tuyến bằng AI</p>
        </div>

        {error && (
          <div className="p-3 bg-red-950/40 border border-red-800/40 rounded-lg flex items-center gap-2.5 text-sm text-red-400">
            <AlertCircle size={18} className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="p-3 bg-green-950/40 border border-green-800/40 rounded-lg flex items-center gap-2.5 text-sm text-green-400">
            <CheckCircle size={18} className="shrink-0" />
            <span>Đăng ký thành công! Đang chuyển sang Đăng nhập...</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Họ và tên"
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Ví dụ: Nguyễn Văn A"
            required
            disabled={loading || success}
          />
          <Input
            label="Địa chỉ Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="example@exam.com"
            required
            disabled={loading || success}
          />
          <Input
            label="Mật khẩu"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Tối thiểu 6 ký tự"
            required
            disabled={loading || success}
            minLength={6}
          />

          <div className="w-full">
            <label className="block text-sm font-medium text-slate-300 mb-1.5">Vai trò thành viên</label>
            <div className="grid grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => setRole("student")}
                className={`py-2.5 rounded-lg border text-sm font-semibold transition-all duration-200 ${
                  role === "student"
                    ? "bg-brand-500/10 border-brand-500 text-slate-100 ring-1 ring-brand-500"
                    : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
                disabled={loading || success}
              >
                Học sinh
              </button>
              <button
                type="button"
                onClick={() => setRole("teacher")}
                className={`py-2.5 rounded-lg border text-sm font-semibold transition-all duration-200 ${
                  role === "teacher"
                    ? "bg-brand-500/10 border-brand-500 text-slate-100 ring-1 ring-brand-500"
                    : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
                disabled={loading || success}
              >
                Giáo viên
              </button>
            </div>
          </div>

          {role === "student" && (
            <>
              <Input
                label="Ngày tháng năm sinh"
                type="date"
                value={dateOfBirth}
                onChange={(e) => setDateOfBirth(e.target.value)}
                required
                disabled={loading || success}
              />
              <Input
                label="Trường lớp"
                type="text"
                value={school}
                onChange={(e) => setSchool(e.target.value)}
                placeholder="Ví dụ: Lớp 12A1, THPT Chuyên"
                required
                disabled={loading || success}
              />
            </>
          )}

          {role === "teacher" && (
            <Input
              label="Nơi công tác"
              type="text"
              value={workplace}
              onChange={(e) => setWorkplace(e.target.value)}
              placeholder="Ví dụ: Trường THPT A"
              required
              disabled={loading || success}
            />
          )}

          <Button type="submit" variant="primary" className="w-full py-3 mt-2" disabled={loading || success}>
            {loading ? "Đang xử lý..." : "Đăng ký"}
          </Button>
        </form>

        <div className="text-center text-sm text-slate-400">
          Đã có tài khoản?{" "}
          <Link href="/login" className="text-brand-400 hover:text-brand-300 font-semibold transition-colors">
            Đăng nhập
          </Link>
        </div>
      </div>
    </div>
  );
}
