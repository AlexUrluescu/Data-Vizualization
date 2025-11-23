import { cn } from "@/lib/utils";
import HomeView from "@/views/home";

async function getCities() {
  const apiUrl = process.env.API_URL || "http://localhost:3000";

  try {
    const res = await fetch(`${apiUrl}/api/cities`, {
      next: { revalidate: 3600 },
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

export default async function Home() {
  const cities1 = await getCities();

  const cities = cities1.filter(
    (city: any) => city._id === "6908d624c8c026b45976c717"
  );

  const isMobile = false;

  return (
    <div className="h-full p-6 sm:p-12 lg:p-16">
      <div className="flex flex-col gap-12 sm:gap-20 lg:gap-24">
        <div className="flex justify-center">
          <div
            className={cn(
              "text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight",
              "bg-gradient-to-b from-slate-50 via-white to-slate-50",
              "bg-clip-text text-transparent",
              isMobile
                ? "drop-shadow-[0_10px_10px_rgba(255,140,0,1),0_14px_20px_rgba(255,100,0,1),0_10px_20px_rgba(255,165,0,0.95),0_2px_2px_rgba(255,200,0,1)]"
                : "drop-shadow-[0_10px_22px_rgba(255,140,0,0.8),0_10px_22px_rgba(255,100,0,0.8),0_10px_22px_rgba(255,165,0,0.8),0_1px_1px_rgba(255,200,0,0.8)]"
            )}
          >
            <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold">
              Urban.ai
            </h1>
          </div>
        </div>

        <HomeView citiesEntities={cities} />
      </div>
    </div>
  );
}
