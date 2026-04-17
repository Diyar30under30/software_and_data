# Import necessary modules
from rich.console import Console  # Import Console from the rich library for styled console output
from rich.table import Table  # Import Table from the rich library for creating styled tables
from database import get_connection  # Import the database connection function

def print_registration_report():
    conn = get_connection()
    cursor = conn.cursor()

    # Execute a query to fetch registration data, including student names, course names, and registration dates
    cursor.execute(
        """
        SELECT r.id, 
               s.first_name || ' ' || s.last_name AS student, 
               c.name AS course, 
               r.registration_date 
        FROM Registrations r
        JOIN Students s ON r.student_id = s.id
        JOIN Courses c ON r.course_id = c.id
        """
    )
    rows = cursor.fetchall()  
    conn.close()  

    # Create a console object for printing styled output
    console = Console()

    table = Table(title="Student Registration Report")

    # Add columns to the table with styles
    table.add_column("ID", style="cyan", no_wrap=True)  
    table.add_column("Student", style="magenta")  
    table.add_column("Course", style="green")
    table.add_column("Date", style="yellow")  

    # Add rows to the table using the fetched data
    for row in rows:
        table.add_row(str(row[0]), row[1], row[2], row[3])  # Convert ID to string and add all columns

    console.print(table)