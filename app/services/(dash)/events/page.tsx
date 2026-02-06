import EventsList from "@/app/ui/components/EventsList";

export default function Page() {
  return (
    <div className="m-0 tablet:m-4 laptop:m-8 flex-1">
      <EventsList
        headerText={"Events and Workshops"}
        showOnlyRegisteredEvents={false} // show all public events & don't show the link to ourself
        showMeetingLinks={false} // show register buttons
      ></EventsList>
    </div>
  );
}
