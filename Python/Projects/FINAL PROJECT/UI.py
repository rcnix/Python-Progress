# Import Tkinter to create the graphical user interface (GUI)
import tkinter as tk
from pathlib import Path

# Import messagebox to display warning and error pop-ups
import tkinter.messagebox as messagebox

# Import psycopg2 to connect to the PostgreSQL database
import psycopg2


import customtkinter as ctk

# Import the Queue class to manage ticket queues
from MyQueue2 import Queue

# Import database functions for tickets and login
from database import (
    add_ticket,
    authenticate,
    clear_queue,
    ensure_schema,
    get_waiting_tickets,
    serve_next,
)

# Stores the Windows icon path used in the title bar
LOGO_PATH = Path(__file__).resolve().parent / "logo.ico"


# Centers the window on the user's screen
def center_window(window):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = max((window.winfo_screenwidth() - width) // 2, 0)
    y = max((window.winfo_screenheight() - height) // 2, 0)
    window.geometry(f"{width}x{height}+{x}+{y}")


# Class for creating Log-in window
class LoginFrame(ctk.CTkFrame):
    def __init__(self, root, on_login):
        super().__init__(root, corner_radius=0)
        self.root = root
        self.on_login = on_login
# Sets the title size For the Login Window
        self.root.title("QueueUP Login")
        self.pack(fill="both", expand=True)
    #Creates a centered container for the login controls
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.place(relx=0.5, rely=0.5, anchor="center")

# Displays the title for login screen
        ctk.CTkLabel(
            form,
            text="QueueUP: Log-In",
            font=ctk.CTkFont(family="Trebuchet MS", size=35, weight="bold"),
        ).pack(pady=(8, 15))

# Creates a label and an input field for the username
        ctk.CTkLabel(form, text="Username").pack()
        self.username = ctk.CTkEntry(
            form,
            width=220,
            placeholder_text="Enter Username...",
            border_width=1,
            border_color=("#6FAF7A", "#6FAF7A"),
            corner_radius=4,
        )
        self.username.pack()
        self.username.bind("<Return>", self._submit_with_enter)

# Creates a label and input field for the password
# The 'show="*"' is to hide the password
        ctk.CTkLabel(form, text="Password").pack()
        self.password = ctk.CTkEntry(
            form,
            show="*",
            width=220,
            placeholder_text="Enter Password...",
            border_width=1,
            border_color=("#6FAF7A", "#6FAF7A"),    
            corner_radius=4,
        )
        self.password.pack()
        self.password.bind("<Return>", self._submit_with_enter)

# Creates a Log-in Button
        ctk.CTkButton(
            form,
            text="LOGIN",
            width=150,
            fg_color=("#8FD19E", "#3F8F50"),
            hover_color=("#72C784", "#347A42"),
            text_color=("#17351E", "#F1FBF2"),
            border_width=1,
            border_color=("#4D9B5A", "#8FD19E"),
            command=self.login,
        ).pack(pady=(16, 20))
    def _submit_with_enter(self, _event):
        self.login()
        return "break"

# Function to check and process the Log-in
    def login(self):
        username = self.username.get().strip()
        password = self.password.get()
# Checks if the username or password is empty
        if not username or not password:
            messagebox.showwarning(
                "Missing Information",
                "Enter a username and password!",
                parent=self.root,
            )
            return

        try:
            logged_in = authenticate(username, password)
        except psycopg2.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not connect to PostgreSQL:\n{error}",
                parent=self.root,
            )
            return

        if not logged_in:
            messagebox.showerror(
                "Log-in Failed",
                "Invalid username or password!",
                parent=self.root,
            )
            return

        self.on_login()

# Class for the main QueueUP Registrar Counter System
class MainFrame(ctk.CTkFrame):
#Font used throughout the application
    FONT = "Trebuchet MS"
# Sets the number of registrar counters to six
    COUNTER_COUNT = 6

# Gets the symbol for the appearance-mode button
    @staticmethod
    def _appearance_mode_button_text():
        return "☀" if ctk.get_appearance_mode() == "Dark" else "☾"

# Initializes the main queue dashboard
    def __init__(self, root, on_logout):
        super().__init__(root, corner_radius=0)
        self.root = root
        self.on_logout = on_logout
# Sets the title and size of the main window
        self.root.title("QueueUP: PHINMA-UPang's Registrar Counter System")
        self.pack(fill="both", expand=True)
# Creates six separate queues for each counter
        self.queues = [
            Queue(prefix=f"C{counter_number}")
            for counter_number in range(1, self.COUNTER_COUNT + 1)
        ]
# Stores the latest ticket number for each counter
        self.current_tickets = [
            tk.StringVar(value="No Ticket")
            for _ in range(self.COUNTER_COUNT)
        ]
# Stores the ticket currently being served at each counter
        self.counter_tickets = [
            tk.StringVar(value="No Ticket")
            for _ in range(self.COUNTER_COUNT)
        ]
# Stores the number of waiting tickets for each counter
        self.counts = [
            tk.StringVar(value="Waiting: 0")
            for _ in range(self.COUNTER_COUNT)
        ]
# Stores the Listbox widgets that display waiting tickets
        self.queue_views = []
# Display the current system status
        self.status = tk.StringVar(value="All six counter queues are visible.")
# Build the dashboard interface
        self._build_dashboard()
# Refresh the queues to get the current tickets
        self._refresh_queues()
# Function to create the main dashboard layout
    def _build_dashboard(self):
# Creates the main container for the dashboard
        main = self
# Configures the rows and columns of the dashboard
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)
        header = ctk.CTkFrame(main, fg_color="transparent")
        header.grid(row=0, column=0, pady=(18, 14), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(2, weight=1)
# Displays the main dashboard title
        ctk.CTkLabel(
            header,
            text="Welcome to QueueUP!",
            font=ctk.CTkFont(family=self.FONT, size=22, weight="bold"),
            anchor="center",
        ).grid(row=0, column=1)
        counter_grid = ctk.CTkFrame(main, fg_color="transparent")
        counter_grid.grid(row=1, column=0, sticky="nsew")
        for row in range(2):
            counter_grid.grid_rowconfigure(row, weight=1)
        for column in range(3):
            counter_grid.grid_columnconfigure(column, weight=1)

# Creates the counter panels
        for index in range(self.COUNTER_COUNT):
            self._build_counter_panel(counter_grid, index)

# Creates the bottom controls container
        bottom_controls = ctk.CTkFrame(main, fg_color="transparent")
        bottom_controls.grid(row=3, column=0, padx=20, pady=(8, 4), sticky="ew")
        bottom_controls.grid_columnconfigure(0, weight=1)
        bottom_controls.grid_columnconfigure(2, weight=1)
# Creates the appearance-mode button
        self.appearance_button = ctk.CTkButton(
            bottom_controls,
            text=self._appearance_mode_button_text(),
            width=32,
            height=38,
            font=ctk.CTkFont(size=16),
            fg_color=("#8FD19E", "#3F8F50"),
            hover_color=("#72C784", "#347A42"),
            text_color=("#17351E", "#F1FBF2"),
            border_width=1,
            border_color=("#4D9B5A", "#8FD19E"),
            command=self._toggle_appearance,
        )
        self.appearance_button.grid(
            row=0,
            column=0,
            sticky="w",
        )

#Creates the clear-queues button
        ctk.CTkButton(
            bottom_controls,
            text="Clear All Queues",
            width=180,
            height=38,
            fg_color=("#8FD19E", "#3F8F50"),
            hover_color=("#72C784", "#347A42"),
            text_color=("#17351E", "#F1FBF2"),
            border_width=1,
            border_color=("#4D9B5A", "#8FD19E"),
            command=self._clear_queues,
        ).grid(row=0, column=1)
        ctk.CTkLabel(
            bottom_controls,
            textvariable=self.status,
            font=ctk.CTkFont(family=self.FONT, size=9),
            anchor="center",
        ).grid(
            row=1,
            column=1,
            sticky="ew",
        )
        ctk.CTkButton(
            bottom_controls,
            text="Log Out",
            width=110,
            height=38,
            fg_color=("#D98C8C", "#9B3D3D"),
            hover_color=("#C97676", "#7F3030"),
            text_color=("#4A1717", "#FFF2F2"),
            border_width=1,
            border_color=("#B85C5C", "#D98C8C"),
            command=self._logout,
        ).grid(row=0, column=2, sticky="e")

# Switches between light and dark appearance modes
    def _toggle_appearance(self):
        new_mode = "Dark" if ctk.get_appearance_mode() == "Light" else "Light"
        ctk.set_appearance_mode(new_mode)
        self.appearance_button.configure(text=self._appearance_mode_button_text())

# Creates one counter panel and its controls
    def _build_counter_panel(self, parent, index):
        counter_number = index + 1
# Creates the counter panel container
        window_box = ctk.CTkFrame(parent, fg_color="transparent")
        window_box.grid(
            row=index // 3,
            column=index % 3,
            padx=12,
            pady=12,
            sticky="nsew",
        )
        window_box.grid_columnconfigure(0, weight=1)
        window_box.grid_rowconfigure(0, minsize=12)
        window_box.grid_rowconfigure(1, weight=1)

# Creates the visible counter panel
        panel = ctk.CTkFrame(
            window_box,
            corner_radius=10,
            border_width=2,
            border_color=("gray70", "gray30"),
            fg_color=("#E4F4E7", "#24452D"),
        )
        panel.grid(row=1, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(5, weight=1, minsize=110)

        ctk.CTkLabel(
            window_box,
            text=f"COUNTER {counter_number}",
            font=ctk.CTkFont(family=self.FONT, size=12, weight="bold"),
            fg_color=("#2E8300", "#2E8300"),
            text_color="white",
            corner_radius=4,
            padx=8,
        ).place(relx=0.5, y=0, anchor="n")

# Displays the latest ticket label
        ctk.CTkLabel(
            panel,
            text="Latest Ticket:",
            font=ctk.CTkFont(family=self.FONT, size=12, weight="bold"),
            anchor="center",
            justify="center",
        ).grid(
            row=0,
            column=0,
            padx=16,
            pady=(14, 0),
            sticky="ew",
        )
        ctk.CTkLabel(
            panel,
            textvariable=self.current_tickets[index],
            font=ctk.CTkFont(family=self.FONT, size=22, weight="bold"),
            anchor="center",
        ).grid(row=1, column=0, padx=16, pady=(2, 4), sticky="ew")
# Displays the ticket currently being served
        ctk.CTkLabel(
            panel,
            text="Counter Ticket:",
            font=ctk.CTkFont(family=self.FONT, size=12, weight="bold"),
            anchor="center",
            justify="center",
        ).grid(row=2, column=0, padx=16, sticky="ew")
        ctk.CTkLabel(
            panel,
            textvariable=self.counter_tickets[index],
            font=ctk.CTkFont(family=self.FONT, size=22, weight="bold"),
            anchor="center",
        ).grid(row=3, column=0, padx=16, pady=(2, 4), sticky="ew")
# Displays the number of waiting tickets
        ctk.CTkLabel(
            panel,
            textvariable=self.counts[index],
            font=ctk.CTkFont(family=self.FONT, size=10, weight="bold"),
            anchor="center",
        ).grid(row=4, column=0, padx=16, sticky="ew")

# Creates the waiting-ticket display
        queue_view = ctk.CTkTextbox(
            panel,
            height=110,
            activate_scrollbars=False,
            fg_color=("#F1FBF2", "#193522"),
            border_width=1,
            border_color=("#A8D5AE", "#3D7049"),
            text_color=("#17351E", "#E4F4E7"),
        )
        queue_view.grid(
            row=5,
            column=0,
            padx=16,
            pady=8,
            sticky="nsew",
        )
        queue_view.configure(state="disabled")
        self.queue_views.append(queue_view)
        button_row = ctk.CTkFrame(panel, fg_color="transparent")
        button_row.grid(
            row=6,
            column=0,
            padx=16,
            pady=(0, 14),
            sticky="ew",
        )
        button_row.grid_columnconfigure(0, weight=1)
        button_row.grid_columnconfigure(1, weight=1)
# Creates the button for issuing a ticket
        ctk.CTkButton(
            button_row,
            text=f"GET NUMBER - Counter {counter_number}",
            fg_color=("#8FD19E", "#3F8F50"),
            hover_color=("#72C784", "#347A42"),
            text_color=("#17351E", "#F1FBF2"),
            border_width=1,
            border_color=("#4D9B5A", "#8FD19E"),
            command=lambda counter=index: self._generate_number(counter),
# Creates the button for serving the next ticket
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkButton(
            button_row,
            text="SERVE NEXT",
            fg_color=("#D98C8C", "#9B3D3D"),
            hover_color=("#C97676", "#7F3030"),
            text_color=("#4A1717", "#FFF2F2"),
            border_width=1,
            border_color=("#B85C5C", "#D98C8C"),
            command=lambda counter=index: self._serve_next(counter),
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

# Generates and saves a new queue ticket
    def _generate_number(self, counter_index):
        counter_number = counter_index + 1
        queue = self.queues[counter_index]
        try:
            ticket = queue.generate_number()
            add_ticket(ticket, counter_number)
            self.current_tickets[counter_index].set(ticket)
            self.status.set(f"{ticket} added to Counter {counter_number}.")
            self._refresh_queues()
        except psycopg2.Error as error:
            queue.dequeue()
            messagebox.showerror(
                "Database error",
                f"Could not save the ticket:\n{error}",
                parent=self.root,
            )

# Serves the oldest waiting ticket for one counter
    def _serve_next(self, counter_index):
        counter_number = counter_index + 1
        queue = self.queues[counter_index]
        try:
            ticket = serve_next(counter_number)
            if ticket is None:
                self.status.set(f"No waiting tickets at Counter {counter_number}.")
                return

            if queue.peek() == ticket:
                queue.dequeue()
            self.counter_tickets[counter_index].set(ticket)
            self.status.set(f"{ticket} is now being served at Counter {counter_number}.")
            self._refresh_queues()
        except psycopg2.Error as error:
            messagebox.showerror(
                "Database error",
                f"Could not serve the next ticket:\n{error}",
                parent=self.root,
            )

# Refreshes every counter's waiting-ticket display
    def _refresh_queues(self):
        try:
            for counter_number, view in enumerate(self.queue_views, 1):
                tickets = get_waiting_tickets(counter_number)
                self.counts[counter_number - 1].set(f"Waiting: {len(tickets)}")
                view.configure(state="normal")
                view.delete("1.0", tk.END)
                view.insert(
                    "1.0",
                    "\n".join(
                        f"{position}.  {ticket}"
                        for position, ticket in enumerate(tickets, 1)
                    )
                    or "No waiting tickets!",
                )
                view.configure(state="disabled")
        except psycopg2.Error as error:
            messagebox.showerror(
                "Database error",
                f"Could not refresh the queues:\n{error}",
                parent=self.root,
            )

# Resets every local queue and ticket display
    def _reset_queues(self):
        for queue in self.queues:
            queue.clear()
        for ticket in self.current_tickets + self.counter_tickets:
            ticket.set("No Ticket")

# Clears all tickets from the database and local queues
    def _clear_queues(self):
        try:
            clear_queue()
            self._reset_queues()
            self.status.set("All six queues cleared.")
            self._refresh_queues()
        except psycopg2.Error as error:
            messagebox.showerror(
                "Database error",
                f"Could not clear the queues:\n{error}",
                parent=self.root,
            )

    def _logout(self):
        if messagebox.askyesno(
            "Log-out",
            "Are you sure you want to log out?",
            parent=self.root,
        ):
            try:
                clear_queue()
                self._reset_queues()
                self.on_logout()
            except psycopg2.Error as error:
                messagebox.showerror(
                    "Database error",
                    f"Could not clear the queues before logging out:\n{error}",
                    parent=self.root,
                )
    # def serve_next():

# Starts the QueueUP Application
def main():
#Sets the default appearance and color theme
    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
# Loads the title-bar logo when the icon file is available
    if LOGO_PATH.is_file():
        try:
            root.iconbitmap(default=str(LOGO_PATH))
        except tk.TclError:
            pass
# Prepares the database before opening the login screen
    try:
        ensure_schema()
    except psycopg2.Error as error:
        messagebox.showerror(
            "Database setup error",
            "Could not prepare the PostgreSQL database.\n\n"
            f"{error}\n\n"
            "Check that PostgreSQL is running and that .env has the "
            "correct database, username, password, host, and port!",
            parent=root,
        )
        root.destroy()
        return

    active_frame = None

    def configure_window(title, geometry, minimum_size):
        root.state("normal")
        root.resizable(True, True)
        root.title(title)
        root.minsize(*minimum_size)
        root.geometry(geometry)
        root.update_idletasks()
        center_window(root)

# Replaces the login screen with the main dashboard
    def show_main_frame():
        nonlocal active_frame
        root.withdraw()
        active_frame.destroy()
        configure_window(
            "QueueUP: PHINMA-UPang's Registrar Counter System",
            "990x648",
            (850, 560),
        )
        active_frame = MainFrame(root, show_login_frame)
        root.deiconify()

# Replaces the main dashboard with the login screen
    def show_login_frame():
        nonlocal active_frame
        root.withdraw()
        active_frame.destroy()
        configure_window("QueueUP Login", "400x300", (350, 250))
        active_frame = LoginFrame(root, show_main_frame)
        configure_window("QueueUP Login", "400x300", (350, 250))
        root.deiconify()

# Closes the application when the window is closed
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    configure_window("QueueUP Login", "400x300", (350, 250))
    active_frame = LoginFrame(root, show_main_frame)
    configure_window("QueueUP Login", "400x300", (350, 250))
# Keep the application running
    root.mainloop()

# Run the main function when this file is executed directly
if __name__ == "__main__":
    main()
