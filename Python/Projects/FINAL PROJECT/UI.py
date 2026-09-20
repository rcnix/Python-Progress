import tkinter as tk
import tkinter.messagebox as messagebox
import psycopg2
from MyQueue2 import Queue
from database import (
    add_ticket,
    authenticate,
    clear_queue,
    get_waiting_tickets,
)


class LoginFrame:
    def __init__(self, root):
        self.root = root
        self.root.title("QueueUP Login")
        self.root.geometry("360x240")

        tk.Label(
            root,
            text="QueueUP Login",
            font=("Trebuchet MS", 20, "bold"),
        ).pack(pady=20)
        tk.Label(root, text="Username").pack()
        self.username = tk.Entry(root)
        self.username.pack()
        tk.Label(root, text="Password").pack()
        self.password = tk.Entry(root, show="*")
        self.password.pack()
        tk.Button(root, text="Login", width=15, command=self.login).pack(pady=20)

    def login(self):
        username = self.username.get().strip()
        password = self.password.get()
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

        for widget in self.root.winfo_children():
            widget.destroy()
        MainFrame(self.root)


class MainFrame:
    FONT = "Trebuchet MS"
    COUNTER_COUNT = 5

    def __init__(self, root):
        self.root = root
        self.root.title("QueueUP: Registrar Counter System")
        self.root.geometry("1100x720")
        self.root.minsize(850, 560)
        self.queues = [
            Queue(prefix=f"C{counter_number}")
            for counter_number in range(1, self.COUNTER_COUNT + 1)
        ]
        self.current_tickets = [
            tk.StringVar(value="No ticket yet")
            for _ in range(self.COUNTER_COUNT)
        ]
        self.counts = [
            tk.StringVar(value="Waiting: 0")
            for _ in range(self.COUNTER_COUNT)
        ]
        self.queue_views = []
        self.status = tk.StringVar(value="All five counter queues are visible.")
        self._build_dashboard()
        self._refresh_queues()

    def _build_dashboard(self):
        main = tk.Frame(self.root, padx=22, pady=20)
        main.pack(fill="both", expand=True)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)
        main.grid_rowconfigure(2, weight=1)

        tk.Label(
            main,
            text="QueueUP Registrar Counters",
            font=(self.FONT, 22, "bold"),
        ).grid(row=0, column=0, pady=(0, 14))

        counter_grid = tk.Frame(main)
        counter_grid.grid(row=1, column=0, rowspan=2, sticky="nsew")
        for row in range(2):
            counter_grid.grid_rowconfigure(row, weight=1)
        for column in range(3):
            counter_grid.grid_columnconfigure(column, weight=1)

        for index in range(self.COUNTER_COUNT):
            self._build_counter_panel(counter_grid, index)

        tk.Button(
            main,
            text="Clear All Queues",
            width=18,
            height=2,
            command=self._clear_queues,
        ).grid(row=4, column=0, pady=(14, 4))
        tk.Label(main, textvariable=self.status, font=(self.FONT, 9)).grid(
            row=5,
            column=0,
        )

    def _build_counter_panel(self, parent, index):
        counter_number = index + 1
        panel = tk.LabelFrame(
            parent,
            text=f"  COUNTER {counter_number}  ",
            font=(self.FONT, 12, "bold"),
            padx=12,
            pady=10,
        )
        panel.grid(
            row=index // 3,
            column=index % 3,
            padx=8,
            pady=8,
            sticky="nsew",
        )
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(3, weight=1)

        tk.Label(panel, text="Latest ticket", font=(self.FONT, 9)).grid(
            row=0,
            column=0,
        )
        tk.Label(
            panel,
            textvariable=self.current_tickets[index],
            font=(self.FONT, 22, "bold"),
        ).grid(row=1, column=0, pady=(2, 6))
        tk.Label(
            panel,
            textvariable=self.counts[index],
            font=(self.FONT, 10, "bold"),
        ).grid(row=2, column=0)

        queue_view = tk.Listbox(panel, height=6, activestyle="none")
        queue_view.grid(row=3, column=0, pady=8, sticky="nsew")
        self.queue_views.append(queue_view)
        tk.Button(
            panel,
            text=f"Get Number - Counter {counter_number}",
            command=lambda counter=index: self._generate_number(counter),
        ).grid(row=4, column=0, sticky="ew")

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
                view.delete(0, tk.END)
                for position, ticket in enumerate(tickets, 1):
                    view.insert(tk.END, f"{position}.  {ticket}")
                if not tickets:
                    view.insert(tk.END, "No waiting tickets")
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
                current_ticket.set("No ticket yet")
            self.status.set("All five queues cleared.")
            self._refresh_queues()
        except psycopg2.Error as error:
            messagebox.showerror(
                "Database error",
                f"Could not clear the queues:\n{error}",
                parent=self.root,
            )


def main():
    root = tk.Tk()
    LoginFrame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
