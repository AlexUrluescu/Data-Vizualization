import { cn } from "@/lib/utils";

export default function Home() {
  const isMobile = false;
  return (
    <div style={{ height: "100%", padding: 50 }}>
      <div style={{ display: "flex", justifyContent: "center" }}>
        <div
          className={cn(
            "text-5xl sm:text-6xl md:text-7xl font-extrabold tracking-tight",
            "bg-gradient-to-b from-slate-50 via-white to-slate-50",
            "bg-clip-text text-transparent",
            isMobile
              ? "drop-shadow-[0_10px_10px_rgba(255,140,0,1),0_14px_20px_rgba(255,100,0,1),0_10px_20px_rgba(255,165,0,0.95),0_2px_2px_rgba(255,200,0,1)]"
              : "drop-shadow-[0_10px_22px_rgba(255,140,0,0.8),0_10px_22px_rgba(255,100,0,0.8),0_10px_22px_rgba(255,165,0,0.8),0_1px_1px_rgba(255,200,0,0.8)]"
          )}
        >
          <h1 style={{ fontSize: 80, fontWeight: 700 }}>Urban Bike</h1>
        </div>
      </div>
    </div>
  );
}
