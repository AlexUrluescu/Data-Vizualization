"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Home, Menu, X, Sparkles } from "lucide-react";
import Image from "next/image";
import { useState } from "react";

export default function Sidebar() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-md bg-white dark:bg-neutral-900 border border-gray-200 dark:border-neutral-800 shadow-lg"
      >
        {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
      </button>

      {isOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-30"
          onClick={() => setIsOpen(false)}
        />
      )}

      <aside
        className={`
          fixed left-0 top-0 h-screen w-64 
          bg-white dark:bg-neutral-900 
          border-r border-gray-200 dark:border-neutral-800 
          p-4 flex flex-col justify-between
          transition-transform duration-300 ease-in-out
          z-40
          ${isOpen ? "translate-x-0" : "-translate-x-full"}
          lg:translate-x-0
        `}
      >
        <div>
          <div className="flex justify-center mb-8 mt-2">
            <Image src={"/logo.png"} height={70} width={70} alt="Logo" />
          </div>
          <nav className="flex flex-col space-y-2">
            <Button
              variant="ghost"
              className="justify-start"
              asChild
              onClick={() => setIsOpen(false)}
            >
              <Link href="/">
                <Home className="mr-2 h-4 w-4" />
                Dashboard
              </Link>
            </Button>
            <Button
              variant="ghost"
              className="justify-start"
              asChild
              onClick={() => setIsOpen(false)}
            >
              <Link href="/profile">
                <Sparkles className="mr-2 h-4 w-4" />
                Urban AI
              </Link>
            </Button>
          </nav>
        </div>
      </aside>
    </>
  );
}
