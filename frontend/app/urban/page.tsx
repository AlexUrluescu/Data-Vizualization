import ChatWithAI from "@/components/custom/chat-ai";
import SibiuTrafficMap from "@/components/custom/map";

interface User {
  id: number;
  name: string;
  age: number;
  purchases: number;
}

interface MockData {
  users: User[];
  revenue: number;
  period: string;
}

async function getCities() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000";

  try {
    const res = await fetch(`${apiUrl}/api/cities`, {
      next: { revalidate: 3600 }, // Cache for 1 hour
    });

    if (!res.ok) {
      console.error("Failed to fetch cities");
      return [];
    }

    return res.json();
  } catch (error) {
    console.error("Error fetching cities:", error);
    return [];
  }
}

export default async function Urban() {
  const cities = await getCities();

  const isMobile = false;
  return (
    <div
      style={{ display: "flex", flexDirection: "column", gap: 20 }}
      className="h-full p-6 sm:p-12 lg:p-16"
    >
      <SibiuTrafficMap />
      <ChatWithAI dataDescription="user analytics and revenue data" />
    </div>
  );
}
