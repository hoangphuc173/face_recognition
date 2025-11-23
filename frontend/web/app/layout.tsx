'use client';
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import { usePathname } from "next/navigation";

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();
  const isAuthPage = pathname === '/' || pathname?.startsWith('/register') || pathname?.startsWith('/forgot-password') || pathname?.startsWith('/auth');

  return (
    <html lang="en">
      <body className={inter.className}>
        {!isAuthPage && <Sidebar />}
        <main className={!isAuthPage ? "lg:ml-64 transition-all duration-300" : ""}>
          {children}
        </main>
      </body>
    </html>
  );
}
