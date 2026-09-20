#Import Tkinter to create the graphical user interface (GUI)
import tkinter as tk

#Import messagebox to display warning and error pop-ups
import tkinter.messagebox as messagebox

#Import psycopg2 to connect to the PostgreSQL database
import psycopg2


import customtkinter as ctk

#Import the Queue class to manage ticket queues
from MyQueue2 import Queue

#Import database functions for tickets and login
from database import (
    add_ticket,
    authenticate,
    clear_queue,
    ensure_schema,
    get_waiting_tickets,
)

#Class for creating Log-in window
class LoginFrame(ctk.CTkFrame):
    def __init__(self, root, on_login):
        super().__init__(root, corner_radius=0)
        self.root = root
        self.on_login = on_login
#Sets the title size For the Login Window
        self.root.title("QueueUP Login")
        self.root.geometry("360x240")
        self.pack(fill="both", expand=True)

#Displays the title for login screen
        ctk.CTkLabel(
            self,
            text="QueueUP: Log In",
            font=ctk.CTkFont(family="Trebuchet MS", size=30, weight="bold"),
        ).pack(pady=(8, 12))

#Creates a label and input field for the username
        ctk.CTkLabel(self, text="Username").pack()
        self.username = ctk.CTkEntry(
            self,
            width=220,
            placeholder_text="Enter Username...",
            border_width=1,
            border_color=("#6FAF7A", "#6FAF7A"),
            corner_radius=4,
        )
        self.username.pack()
        self.username.bind("<Return>", self._submit_with_enter)

#Creates a label and input field for the password
#The show="*" is to hide the password
        ctk.CTkLabel(self, text="Password").pack()
        self.password = ctk.CTkEntry(
            self,
            show="*",
            width=220,
            placeholder_text="Enter Password...",
            border_width=1,
            border_color=("#6FAF7A", "#6FAF7A"),    
            corner_radius=4,
        )
        self.password.pack()
        self.password.bind("<Return>", self._submit_with_enter)

#Creates a Log-in Button
        ctk.CTkButton(
            self,
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

#Function to check and process the Log-in
    def login(self):
        username = self.username.get().strip()
        password = self.password.get()
#Checks if the username or password is empty
        if not username or not password:
            messagebox.showwarning(
                "Missing information",
                "Enter a username and password.",
                parent=self.root,
            )
            return

        try:
            logged_in = authenticate(username, password)
        except psycopg2.Error as error:
            messagebox.showerror(
                "Database error",
                f"Could not connect to PostgreSQL:\n{error}",
                parent=self.root,
            )
            return

        if not logged_in:
            messagebox.showerror(
                "Login failed",
                "Invalid username or password.",
                parent=self.root,
            )
            return

        self.on_login()

#Class for the main QueueUP Registrar Counter System
class MainFrame(ctk.CTkFrame):
#Font used throughout the application
    FONT = "Trebuchet MS"
#Sets the number of registrar counters to six
    COUNTER_COUNT = 6

    @staticmethod
    def _appearance_mode_button_text():
        return (
            "Light Mode"
            if ctk.get_appearance_mode() == "Dark"
            else "Dark Mode"
        )

    def __init__(self, root):
        super().__init__(root, corner_radius=0)
        self.root = root
#Sets the title and size of the main window
        self.root.title("QueueUP: Registrar Counter System")
        self.root.geometry("1100x720")
        self.root.minsize(850, 560)
        self.pack(fill="both", expand=True)
#Creates six separate queues for each counter
        self.queues = [
            Queue(prefix=f"C{counter_number}")
            for counter_number in range(1, self.COUNTER_COUNT + 1)
        ]
#Stores the latest ticket number for each counter
        self.current_tickets = [
            tk.StringVar(value="No Ticket")
            for _ in range(self.COUNTER_COUNT)
        ]
#Stores the number of waiting tickets for each counter
        self.counts = [
            tk.StringVar(value="Waiting: 0")
            for _ in range(self.COUNTER_COUNT)
        ]
#Stores the Listbox widgets that display waiting tickets
        self.queue_views = []
#Display the current system status
        self.status = tk.StringVar(value="All five counter queues are visible.")
#Build the dashboard interface
        self._build_dashboard()
#Refresh the queues to get the current tickets
        self._refresh_queues()

#Function to create the main dashboard layout
    def _build_dashboard(self):
#Creates the main container for the dashboard
        main = self
#Configures the rows and columns of the dashboard
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)
        header = ctk.CTkFrame(main, fg_color="transparent")
        header.grid(row=0, column=0, pady=(18, 14), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(2, weight=1)
#Displays the main dashboard title
        ctk.CTkLabel(
            header,
            text="Welcome to QueueUP!",
            font=ctk.CTkFont(family=self.FONT, size=22, weight="bold"),
            anchor="center",
        ).grid(row=0, column=1)
        self.appearance_button = ctk.CTkButton(
            header,
            text=self._appearance_mode_button_text(),
            width=110,
            height=30,
            fg_color=("#8FD19E", "#3F8F50"),
            hover_color=("#72C784", "#347A42"),
            text_color=("#17351E", "#F1FBF2"),
            border_width=1,
            border_color=("#4D9B5A", "#8FD19E"),
            command=self._toggle_appearance,
        )
        self.appearance_button.grid(row=0, column=2, padx=(20, 42), sticky="e")

        counter_grid = ctk.CTkFrame(main, fg_color="transparent")
        counter_grid.grid(row=1, column=0, sticky="nsew")
        for row in range(2):
            counter_grid.grid_rowconfigure(row, weight=1)
        for column in range(3):
            counter_grid.grid_columnconfigure(column, weight=1)

        for index in range(self.COUNTER_COUNT):
            self._build_counter_panel(counter_grid, index)

        ctk.CTkButton(
            main,
            text="Clear All Queues",
            width=180,
            height=38,
            fg_color=("#8FD19E", "#3F8F50"),
            hover_color=("#72C784", "#347A42"),
            text_color=("#17351E", "#F1FBF2"),
            border_width=1,
            border_color=("#4D9B5A", "#8FD19E"),
            command=self._clear_queues,
        ).grid(row=2, column=0, pady=(14, 4))
        ctk.CTkLabel(
            main,
            textvariable=self.status,
            font=ctk.CTkFont(family=self.FONT, size=9),
            anchor="center",
        ).grid(
            row=3,
            column=0,
            sticky="ew",
        )

    def _toggle_appearance(self):
        new_mode = "Dark" if ctk.get_appearance_mode() == "Light" else "Light"
        ctk.set_appearance_mode(new_mode)
        self.appearance_button.configure(text=self._appearance_mode_button_text())

    def _build_counter_panel(self, parent, index):
        counter_number = index + 1
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

        panel = ctk.CTkFrame(
            window_box,
            corner_radius=10,
            border_width=2,
            border_color=("gray70", "gray30"),
            fg_color=("#E4F4E7", "#24452D"),
        )
        panel.grid(row=1, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(3, weight=1, minsize=110)

        ctk.CTkLabel(
            window_box,
            text=f"COUNTER {counter_number}",
            font=ctk.CTkFont(family=self.FONT, size=12, weight="bold"),
            fg_color=("#2E8300", "#2E8300"),
            text_color="white",
            corner_radius=4,
            padx=8,
        ).place(relx=0.5, y=0, anchor="n")

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
        ).grid(row=1, column=0, padx=16, pady=(2, 6), sticky="ew")
        ctk.CTkLabel(
            panel,
            textvariable=self.counts[index],
            font=ctk.CTkFont(family=self.FONT, size=10, weight="bold"),
            anchor="center",
        ).grid(row=2, column=0, padx=16, sticky="ew")

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
            row=3,
            column=0,
            padx=16,
            pady=8,
            sticky="nsew",
        )
        queue_view.configure(state="disabled")
        self.queue_views.append(queue_view)
        ctk.CTkButton(
            panel,
            text=f"GET NUMBER - Counter {counter_number}",
            fg_color=("#8FD19E", "#3F8F50"),
            hover_color=("#72C784", "#347A42"),
            text_color=("#17351E", "#F1FBF2"),
            border_width=1,
            border_color=("#4D9B5A", "#8FD19E"),
            command=lambda counter=index: self._generate_number(counter),
        ).grid(row=4, column=0, padx=16, pady=(0, 14), sticky="ew")

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
                    or "No waiting tickets",
                )
                view.configure(state="disabled")
        except psycopg2.Error as error:
            messagebox.showerror(
                "Database error",
                f"Could not refresh the queues:\n{error}",
                parent=self.root,
            )

    def _clear_queues(self):
        try:
            clear_queue()
            for queue in self.queues:
                queue.clear()
            for current_ticket in self.current_tickets:
                current_ticket.set("No Ticket")
            self.status.set("All five queues cleared.")
            self._refresh_queues()
        except psycopg2.Error as error:
            messagebox.showerror(
                "Database error",
                f"Could not clear the queues:\n{error}",
                parent=self.root,
            )
    # def serve_next():

def main():
    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
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

    def show_main_frame():
        login_frame.destroy()
        MainFrame(root)

    root.protocol("WM_DELETE_WINDOW", root.destroy)
    login_frame = LoginFrame(root, show_main_frame)
#Keep the application running
    root.mainloop()

#Run the main function when this file is executed directly
if __name__ == "__main__":
    main()
