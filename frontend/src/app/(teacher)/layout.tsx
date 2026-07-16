"use client";
import React, { useEffect } from "react";
import useAuth from "@/hooks/useAuth";
import { useRouter } from "next/navigation";

export default function TeacherLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && (!user || user.role !== "teacher")) {
      router.push("/dashboard");
    }
  }, [user, loading, router]);

  if (loading || !user || user.role !== "teacher") {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <span className="text-slate-400">Đang xác thực quyền giáo viên...</span>
      </div>
    );
  }

  return <>{children}</>;
}
