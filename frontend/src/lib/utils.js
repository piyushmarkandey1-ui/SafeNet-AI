import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Utility to securely merge tailwind classes with dynamic classes.
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
