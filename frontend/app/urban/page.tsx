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
  const res = await fetch("http://127.0.0.1:5001/api/v1/cities");

  if (!res.ok) throw new Error("Failed to fetch");
  return res.json();
}

export default async function Urban() {
  const cities = await getCities();

  // Your mock data
  const mockData: MockData = {
    users: [
      { id: 1, name: "John", age: 28, purchases: 15 },
      { id: 2, name: "Sarah", age: 34, purchases: 23 },
    ],
    revenue: 45000,
    period: "Q4 2024",
  };

  const isMobile = false;
  return (
    <div
      style={{ display: "flex", flexDirection: "column", gap: 20 }}
      className="h-full p-6 sm:p-12 lg:p-16"
    >
      <SibiuTrafficMap />
      <ChatWithAI
        data={mockData}
        dataDescription="user analytics and revenue data"
      />
    </div>
  );
}
