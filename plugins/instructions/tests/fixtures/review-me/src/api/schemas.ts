import { z } from "zod";

export const NewAccount = z.object({ name: z.string().min(1) });
export const NewEntry = z.object({
  amountCents: z.number().int(),
  bookedOn: z.string().date(),
});
