"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Header() {
  const path_name = usePathname();

  const pages: Record<string, string> = {
    "/generate": "Generate",
    "/verify": "Verify",
    "/verify_v2": "V2erify",
    "/explore": "Explore",
  };

  return (
    <header className={"flex flex-row mx-auto my-8"}>
      <Link href={"/"} className={"flex items-center"}>
        <img src={"or_tools.svg"} alt={"OR-TOOLS logo"} className={"h-6"} />
      </Link>
      <nav className={"flex flex-row justify-end gap-3 items-center grow h-12"}>
        {Object.entries(pages).map(([path, label]) => (
          <Link
            key={path}
            href={path}
            className={
              "cursor-pointer hover:underline tuo" +
              (path_name == path ? " underline" : "")
            }
          >
            {label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
