import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Home, Settings, User, LogOut } from "lucide-react";
import Image from "next/image";

export default function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-white dark:bg-neutral-900 border-r border-gray-200 dark:border-neutral-800 p-4 flex flex-col justify-between">
      <div>
        <div style={{ display: "flex", justifyContent: "center" }}>
          <Image src={"/logo2.png"} height={70} width={70} alt="Logo" />
        </div>
        <nav className="flex flex-col space-y-2">
          <Button variant="ghost" className="justify-start" asChild>
            <Link href="/">
              <Home className="mr-2 h-4 w-4" />
              Dashboard
            </Link>
          </Button>
          <Button variant="ghost" className="justify-start" asChild>
            <Link href="/profile">
              <User className="mr-2 h-4 w-4" />
              Profile
            </Link>
          </Button>
          <Button variant="ghost" className="justify-start" asChild>
            <Link href="/settings">
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </Link>
          </Button>
        </nav>
      </div>
    </aside>
  );
}
