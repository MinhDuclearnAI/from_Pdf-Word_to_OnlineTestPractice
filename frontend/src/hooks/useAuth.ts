import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import apiClient from "@/lib/api-client";

export interface User {
  id: number;
  email: string;
  role: "student" | "teacher";
  created_at: string;
}

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    if (typeof window !== "undefined") {
      const storedUser = localStorage.getItem("user");
      const token = localStorage.getItem("access_token");
      const storedRole = localStorage.getItem("role") || "";

      if (storedUser && token) {
        try {
          const parsedUser = JSON.parse(storedUser);
          setUser(parsedUser);

          // Always re-sync cookies from localStorage so Next.js middleware
          // sees the same state (prevents blank screen after docker reset)
          document.cookie = `access_token=${token}; path=/; max-age=86400; SameSite=Lax`;
          document.cookie = `role=${parsedUser.role || storedRole}; path=/; max-age=86400; SameSite=Lax`;
        } catch (e) {
          localStorage.removeItem("user");
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
        }
      } else {
        // Ensure cookies are cleared if localStorage is empty
        document.cookie = "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
        document.cookie = "role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
      }
      setLoading(false);
    }
  }, []);

 const login = async (email: string, password: string) => {
  setLoading(true);
  try {
    const { data } = await apiClient.post("/auth/login", {
      email,
      password,
    }); // JSON mặc định, không cần set Content-Type thủ công

    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    localStorage.setItem("user", JSON.stringify(data.user));

    document.cookie = `access_token=${data.access_token}; path=/; max-age=86400; SameSite=Lax`;
    document.cookie = `role=${data.user.role}; path=/; max-age=86400; SameSite=Lax`;

    setUser(data.user);
    router.push("/dashboard");
    return { success: true };
  } catch (error: any) {
    return {
      success: false,
      error: error.response?.data?.detail || "Đăng nhập thất bại. Vui lòng kiểm tra lại.",
    };
  } finally {
    setLoading(false);
  }
};
  const register = async (
    email: string, 
    password: string, 
    role: "student" | "teacher",
    profile: {
      full_name?: string;
      date_of_birth?: string;
      school?: string;
      workplace?: string;
    } = {}
  ) => {
    setLoading(true);
    try {
      await apiClient.post("/auth/register", { 
        email, 
        password, 
        role,
        ...profile
      });
      return { success: true };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.detail || error.response?.data?.message || "Đăng ký thất bại. Vui lòng kiểm tra lại.",
      };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    
    // Clear cookies
    document.cookie = "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    document.cookie = "role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    
    setUser(null);
    router.push("/login");
  };

  return {
    user,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  };
};
export default useAuth;
