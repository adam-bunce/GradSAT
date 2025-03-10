import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Header from "@/components/header";
import Footer from "@/components/footer";
import { Toaster } from "@/components/ui/toaster";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "GradSAT",
  description: "CP-SAT Powered Academic Planning",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased backdrop min-h-screen flex flex-col`}
      >
        <main
          className={"w-full container mx-auto flex-grow max-w-[900px] px-5"}
        >
          <Header />
          <div>{children}</div>
        </main>
        <Toaster />

        <Footer />
      </body>
    </html>
  );
}
