from icalendar import Calendar, Event, vCalAddress, vText, Alarm
from datetime import datetime, timedelta, timezone



def make_interview_ics(
    uid: str,
    title: str,
    description: str,
    start_dt: datetime,
    duration_minutes: int = 60,
    organizer_email: str = "no-reply@example.com",
    location: str = "Online / TBD",
):
    """
    Returns bytes of a .ics with 3 alarms:
      - 1 day before
      - 8:00 AM on the day
      - 5 minutes before
    NOTE: start_dt should be timezone-aware.
    """
    if start_dt.tzinfo is None or start_dt.tzinfo.utcoffset(start_dt) is None:
        # fall back to UTC if naive
        start_dt = start_dt.replace(tzinfo=timezone.utc)

    cal = Calendar()
    cal.add("prodid", "-//JobTrack//EN")
    cal.add("version", "2.0")
    cal.add("method", "REQUEST")

    event = Event()
    event.add("uid", uid)
    event.add("summary", title)
    event.add("description", description)
    event.add("dtstart", start_dt)
    event.add("dtend", start_dt + timedelta(minutes=duration_minutes))
    event.add("dtstamp", datetime.now(timezone.utc))
    event.add("location", location)

    organizer = vCalAddress(f"MAILTO:{organizer_email}")
    organizer.params["cn"] = vText("JobTrack")
    event["organizer"] = organizer

    # Alarm: 1 day before
    alarm1 = Alarm()
    alarm1.add("action", "DISPLAY")
    alarm1.add("description", "Interview tomorrow")
    alarm1.add("trigger", timedelta(days=-1))
    event.add_component(alarm1)

    # Alarm: 8:00 AM on the day (relative trigger)
    alarm2 = Alarm()
    alarm2.add("action", "DISPLAY")
    alarm2.add("description", "Interview today")
    # Trigger from event start to 8am same day:
    # If interview is at, say, 1pm, we want a trigger at 8am -> -X minutes relative
    minutes_before = int(((start_dt.replace(hour=8, minute=0, second=0, microsecond=0)) - start_dt).total_seconds() / 60)
    # If interview is before 8am, just do 30 min before
    if minutes_before > 0:
        alarm2.add("trigger", timedelta(minutes=minutes_before * -1))
    else:
        alarm2.add("trigger", timedelta(minutes=-30))
    event.add_component(alarm2)

    # Alarm: 5 minutes before
    alarm3 = Alarm()
    alarm3.add("action", "DISPLAY")
    alarm3.add("description", "Interview in 5 minutes")
    alarm3.add("trigger", timedelta(minutes=-5))
    event.add_component(alarm3)

    cal.add_component(event)
    return cal.to_ical()