import EventCreationForm from "@/app/ui/components/EventCreation/EventCreationForm";
import EventUpdateForm from "@/app/ui/components/EventCreation/EventUpdateForm";

export default function page() {
  return (
    <main className="w-full gap-4 grid tablet:grid-cols-2 m-4 ">
      <EventCreationForm />
      <EventUpdateForm />
    </main>
  );
}
