import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Header from "@/components/header";
import Footer from "@/components/footer";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Course Search",
  description: "CP-SAT Powered Information Portal",
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
          <div className={"container"}>{children}</div>
        </main>

        <Footer />
      </body>
    </html>
  );
}
