import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Demand Forecasting",
  description: "Inventory demand forecasting platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans">{children}</body>
    </html>
  );
}
