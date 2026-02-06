import {
  createEvent,
  deleteEvent,
  getAllEvents,
  updateEvent,
} from "@/app/lib/events";
import { NextRequest, NextResponse } from "next/server"; // Import NextRequest and NextResponse
//  // Import your functions

// POST - Create an Event
export async function POST(req: NextRequest) {
  try {
    const eventData = await req.json(); // Parse the request body
    const result = await createEvent(eventData);

    if (result.success) {
      return NextResponse.json(result, { status: 201 }); // Event created successfully
    } else {
      return NextResponse.json(result, { status: 400 }); // Error creating event
    }
  } catch (error) {
    console.error("Error creating event:", error);
    return NextResponse.json(
      { success: false, error: "Internal Server Error" },
      { status: 500 },
    );
  }
}

// GET - Retrieve All Events
export async function GET() {
  const result = await getAllEvents(false);
  if (result.success) {
    return NextResponse.json(result, { status: 200 });
  } else {
    return NextResponse.json(result, { status: 404 });
  }
}

// DELETE - Delete an Event
export async function DELETE(req: NextRequest) {
  try {
    const { eventId } = await req.json(); // Assuming the client sends the eventId in the body
    if (!eventId) {
      return NextResponse.json(
        { success: false, error: "Event ID is required" },
        { status: 400 },
      );
    }

    const result = await deleteEvent(eventId);
    if (result.success) {
      return NextResponse.json(result); // Event deleted successfully
    } else {
      return NextResponse.json(result, { status: 400 }); // Error deleting event
    }
  } catch (error) {
    console.error("Error deleting event:", error);
    return NextResponse.json(
      { success: false, error: "Internal Server Error" },
      { status: 500 },
    );
  }
}

// PUT - Update an Event
export async function PUT(req: NextRequest) {
  try {
    const { eventId, updatedData } = await req.json(); // Assuming the client sends eventId and updated fields
    if (!eventId || !updatedData) {
      return NextResponse.json(
        { success: false, error: "Event ID and updated data are required" },
        { status: 400 },
      );
    }

    const result = await updateEvent(eventId, updatedData);
    if (result.success) {
      return NextResponse.json(result); // Event updated successfully
    } else {
      return NextResponse.json(result, { status: 400 }); // Error updating event
    }
  } catch (error) {
    console.error("Error updating event:", error);
    return NextResponse.json(
      { success: false, error: "Internal Server Error" },
      { status: 500 },
    );
  }
}
