import re
import csv

# Example input: lines of text from OCR or structured text file
input_lines = [
    "Monday 08:00-09:30 ITS142 BM4 MPO506",
    "Tuesday 10:00-12:00 ITC101 AM1 ONLINE",
    "Wednesday 13:00-16:00 ITC200 PM2 VIR",
    "Thursday 09:00-11:00 ITC300 AM2 MPOTUT1",
    "Friday 14:00-17:00 ITC400 BM2 305"
]

# Room type detection function
def get_room_type(room):
    room = room.upper()
    if 'ONLINE' in room or 'VIR' in room:
        return 'Virtual'
    if room.startswith('MPO') or room.startswith('MPOTUT'):
        return 'Thesis'
    return 'Physical'

# Regex to parse each line
pattern = re.compile(
    r'^(?P<day>\w+)\s+(?P<start>\d{2}:\d{2})-(?P<end>\d{2}:\d{2})\s+(?P<course>\w+)\s+(?P<section>\w+)\s+(?P<room>\w+)$'
)

parsed_rows = []

for line in input_lines:
    match = pattern.match(line.strip())
    if match:
        day = match.group('day')
        start = match.group('start')
        end = match.group('end')
        course = match.group('course')
        section = match.group('section')
        room = match.group('room')
        room_type = get_room_type(room)
        parsed_rows.append([day, start, end, course, section, room, room_type])
    else:
        print(f"Could not parse line: {line}")

# Write to CSV
with open('student_schedule.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Day', 'Start Time', 'End Time', 'Course Code', 'Section', 'Room', 'Room Type'])
    writer.writerows(parsed_rows)

print("Schedule saved to student_schedule.csv")