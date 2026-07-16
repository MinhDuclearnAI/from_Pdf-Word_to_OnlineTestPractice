import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const token = request.cookies.get("access_token")?.value;
  const role = request.cookies.get("role")?.value;

  const authRoutes = ["/login", "/register"];
  const isAuthPage = authRoutes.includes(pathname);

  // If accessing a protected route without token, redirect to login
  if (!token && !isAuthPage && pathname !== "/") {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  // If accessing auth pages with token, redirect to dashboard
  if (token && isAuthPage) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  // Role-based protection:
  if (token && role) {
    // Teacher trying to access student pages (practice/upload, etc.)
    if (role === "teacher" && (pathname.startsWith("/practice") || (pathname.startsWith("/exam/") && pathname.includes("/play")))) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    }
    // Student trying to access teacher pages (classes, exams/new, exams/[id]/edit, exams/[id]/stats)
    if (role === "student" && (pathname.startsWith("/classes") || pathname.startsWith("/exams"))) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/practice/:path*",
    "/exam/:path*",
    "/result/:path*",
    "/classes/:path*",
    "/exams/:path*",
    "/login",
    "/register",
  ],
};
