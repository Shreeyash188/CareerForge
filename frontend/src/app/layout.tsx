import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const outfit = Outfit({ subsets: ["latin"], variable: "--font-outfit" });

export const metadata: Metadata = {
  title: "CareerForge - AI Job Application Assistant",
  description: "Automate your job application process with AI-powered resume tailoring and cover letter generation",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.variable} ${outfit.variable} min-h-full flex flex-col font-sans antialiased`}>
        {/* Animated Background Elements */}
        <div className="fixed inset-0 overflow-hidden -z-10 pointer-events-none bg-base">
          <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-purple-600/20 rounded-full blur-[120px] mix-blend-screen animate-blob"></div>
          <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-600/20 rounded-full blur-[120px] mix-blend-screen animate-blob animation-delay-2000"></div>
          <div className="absolute top-[20%] left-[60%] w-[30%] h-[30%] bg-pink-600/20 rounded-full blur-[120px] mix-blend-screen animate-blob animation-delay-4000"></div>
        </div>
        {children}
      </body>
    </html>
  );
}