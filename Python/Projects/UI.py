import tkinter as tk
from tkinter import ttk
from PIL import ImageTk, Image 
from MyQueue import RegistrarQueue


class RegistrarQueueApp:
    """Tkinter interface for issuing and serving registrar tickets."""

    def __init__(self, root):
        self.root = root
        self.root.title("Registrar Office Queue")
        self.root.geometry("980x560")
        self.root.minsize(820, 480)

        self.queues = [RegistrarQueue(prefix=f"C{i}") for i in range(1, 6)]
        self.current_tickets = [
            tk.StringVar(value="None") for _ in self.queues
        ]
        self.status = tk.StringVar(value="Ready to issue a ticket.")
        self.count = tk.StringVar(value="Total waiting: 0")
        self.queue_lists = []

        self._build_interface()
        self._refresh_queue()

    def _build_interface(self):
        main = ttk.Frame(self.root, padding=20)
        main.pack(fill="both", expand=True)

        ttk.Label(
            main,
            text="REGISTRAR OFFICE",
            font=("Segoe UI", 20, "bold"),
        ).pack(pady=(0, 4))
        ttk.Label(
            main,
            text="First In, First Out (F.I.F.O.) Queueing System",
        ).pack(pady=(0, 18))

        queues_frame = ttk.LabelFrame(
            main, text="Registrar Service Queues (FIFO)", padding=8
        )
        queues_frame.pack(fill="both", expand=True, pady=(0, 12))
        queues_frame.columnconfigure(1, weight=1)

        for index, queue in enumerate(self.queues):
            row = index
            ttk.Label(
                queues_frame,
                text=f"Counter {index + 1}",
                font=("Segoe UI", 11, "bold"),
            ).grid(row=row, column=0, padx=(4, 12), pady=5, sticky="w")
            listbox = tk.Listbox(
                queues_frame,
                height=2,
                font=("Consolas", 11),
                activestyle="none",
                exportselection=False,
            )
            listbox.grid(row=row, column=1, padx=4, pady=3, sticky="ew")
            self.queue_lists.append(listbox)
            ttk.Label(
                queues_frame,
                textvariable=self.current_tickets[index],
                width=12,
            ).grid(row=row, column=2, padx=8, pady=5)
            ttk.Button(
                queues_frame,
                text="Get Number",
                command=lambda queue_index=index: self._get_number(queue_index),
            ).grid(row=row, column=3, padx=3, pady=5)
            ttk.Button(
                queues_frame,
                text="Serve Next",
                command=lambda queue_index=index: self._serve_next(queue_index),
            ).grid(row=row, column=4, padx=(3, 4), pady=5)

        ttk.Button(main, text="Clear All Queues", command=self._clear_queues).pack(
            pady=(0, 8)
        )
        ttk.Label(main, textvariable=self.count).pack(pady=(0, 2))
        ttk.Label(main, textvariable=self.status).pack()

    def _get_number(self, queue_index):
        ticket = self.queues[queue_index].generate_number()
        self.status.set(
            f"{ticket} added to the end of Counter {queue_index + 1}."
        )
        self._refresh_queue()

    def _serve_next(self, queue_index):
        ticket = self.queues[queue_index].serve_next()
        if ticket is None:
            self.status.set(
                f"Counter {queue_index + 1} is empty. Issue a number first."
            )
            return
        self.current_tickets[queue_index].set(ticket)
        self.status.set(
            f"{ticket} from Counter {queue_index + 1} is now being served."
        )
        self._refresh_queue()

    def _clear_queues(self):
        for queue in self.queues:
            queue.clear()
        self.status.set("All waiting queues have been cleared.")
        self._refresh_queue()

    def _refresh_queue(self):
        total_waiting = 0
        for listbox, queue in zip(self.queue_lists, self.queues):
            listbox.delete(0, tk.END)
            for position, ticket in enumerate(queue.tickets(), start=1):
                listbox.insert(tk.END, f"{position}. {ticket}")
            total_waiting += len(queue)
        self.count.set(f"Total waiting: {total_waiting}")


def main():
    root = tk.Tk()
    RegistrarQueueApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()