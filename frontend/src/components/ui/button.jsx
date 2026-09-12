import React from "react";
import { cn } from "@/lib/utils";

export function Button({ children, className, ...props }) {
  return (
    <button
      {...props}
      className={cn(
        "rounded-md px-4 py-2 font-medium transition-all bg-garden-moss text-garden-paper hover:bg-garden-mossdeep disabled:opacity-50",
        className
      )}
    >
      {children}
    </button>
  );
}