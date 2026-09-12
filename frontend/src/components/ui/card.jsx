import React from "react";
import { cn } from "@/lib/utils";

export function Card({ children, className }) {
  return (
    <div
      className={cn(
        "rounded-xl border border-garden-line bg-card p-4 shadow-sm",
        className
      )}
    >
      {children}
    </div>
  );
}

export function CardContent({ children }) {
  return <div className="p-4">{children}</div>;
}