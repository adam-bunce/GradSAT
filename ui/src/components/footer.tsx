"use client";

import Link from "next/link";

export default function Header() {
  return (
    <footer className={"py-4 px-5 mt-8 bg-black text-white"}>
      Powered by{" "}
      <Link href={"https://developers.google.com/optimization"}>OR-Tools</Link>
    </footer>
  );
}
