import { CardSkeleton } from "@/components/skeletons";

export default function Loading() {
  return (
    <div className="space-y-6">
      <CardSkeleton hasHeader lines={2} />
      <CardSkeleton hasHeader lines={3} />
      <div className="grid gap-6 md:grid-cols-2">
        <CardSkeleton hasHeader lines={5} />
        <CardSkeleton hasHeader lines={5} />
      </div>
    </div>
  );
}
