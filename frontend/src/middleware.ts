export { default } from "next-auth/middleware";

export const config = {
  matcher: [
    "/chat/:path*",
    "/knowledge/:path*",
    "/approvals/:path*",
    "/analytics/:path*",
    "/executive/:path*",
    "/marketplace/:path*",
    "/settings/:path*",
  ],
};
