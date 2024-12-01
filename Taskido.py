import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
import pickle
import os
import time
from plyer import notification
import threading


# Task class to represent each task
class Task:
    def __init__(self, title, description, deadline=None, time=None):
        self.title = title
        self.description = description
        self.deadline = deadline
        self.time = time
        self.completed = False

# Task manager to handle tasks
class TaskManager:
    def __init__(self):
        self.tasks = self.load_tasks()

    def add_task(self, title, description, deadline=None, time=None, position=None):
        new_task = Task(title, description, deadline, time)
        if position is not None:
            self.tasks.insert(position, new_task)
        else:
            self.tasks.append(new_task)
        self.save_tasks()

    def save_tasks(self):
        with open("tasks.pkl", "wb") as f:
            pickle.dump(self.tasks, f)

    def load_tasks(self):
        if os.path.exists("tasks.pkl"):
            with open("tasks.pkl", "rb") as f:
                tasks = pickle.load(f)
                for task in tasks:
                    if not hasattr(task, 'time'):
                        task.time = None
                return tasks
        return []


# GUI class to handle the interface
class TaskApp:
    def __init__(self, root, task_manager):
        self.root = root
        self.task_manager = task_manager
        self.root.title("Taskadoo") # A fun and catchy blend of "task" and "to-do."

        # Set window size
        self.root.geometry("1050x550")

        # Left section for adding tasks
        self.left_frame = tk.Frame(self.root)
        self.left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # Right section for showing tasks with a scrollable frame
        self.right_frame = tk.Frame(self.root)
        self.right_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.canvas = tk.Canvas(self.right_frame, height=600)  # Increased height here
        self.scrollbar = tk.Scrollbar(self.right_frame, orient="vertical", command=self.canvas.yview)
        self.task_list_frame = tk.Frame(self.canvas)

        self.task_list_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.task_list_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Create entries for task details
        self.title_entry = tk.Entry(self.left_frame, width=60, font=("Arial", 12))
        self.title_entry.grid(row=0, column=0, columnspan=2, padx=10, pady=5)
        self.title_entry.insert(0, "Task Title")
        self.title_entry.bind("<FocusIn>", lambda event: self.clear_placeholder(self.title_entry, "Task Title"))

        self.description_entry = tk.Text(self.left_frame, width=60, height=4, font=("Arial", 12))
        self.description_entry.grid(row=1, column=0, columnspan=2, padx=10, pady=5)
        self.description_entry.insert("1.0", "Task Description")
        self.description_entry.bind("<FocusIn>", lambda event: self.clear_placeholder(self.description_entry, "Task Description", is_text=True))

        self.deadline_entry = tk.Entry(self.left_frame, width=60, font=("Arial", 12))
        self.deadline_entry.grid(row=2, column=0, columnspan=2, padx=10, pady=5)
        self.deadline_entry.insert(0, "Deadline (DD-MM-YYYY)")
        self.deadline_entry.bind("<FocusIn>", lambda event: self.clear_placeholder(self.deadline_entry, "Deadline (DD-MM-YYYY)"))

        self.time_entry = tk.Entry(self.left_frame, width=60, font=("Arial", 12))
        self.time_entry.grid(row=3, column=0, columnspan=2, padx=10, pady=5)
        self.time_entry.insert(0, "Time (HH:MM AM/PM)")
        self.time_entry.bind("<FocusIn>", lambda event: self.clear_placeholder(self.time_entry, "Time (HH:MM AM/PM)"))

        # Buttons for adding and clearing tasks
        self.add_button = tk.Button(self.left_frame, text="Add Task", width=20, bg="dark green", fg="white", command=self.add_task)
        self.add_button.grid(row=4, column=0, padx=10, pady=5)

        self.clear_button = tk.Button(self.left_frame, text="Clear Completed Tasks", width=20,bg="light blue", command=self.clear_completed_tasks)
        self.clear_button.grid(row=4, column=1, padx=10, pady=5)
        
        # Create a button
        button = tk.Button(root, text="info", bg="light blue" ,command=show_message)

        # Place the button in the top-right corner
        button.place(relx=1.0, rely=0.0, anchor="ne")  # Top-right alignment


        self.refresh_task_list()

        # Start background thread to check reminders
        self.start_reminder_check()
        
    
    def clear_placeholder(self, widget, placeholder, is_text=False):
        if is_text:
            if widget.get("1.0", tk.END).strip() == placeholder:
                widget.delete("1.0", tk.END)
        else:
            if widget.get() == placeholder:
                widget.delete(0, tk.END)

    def add_task(self):
        title = self.title_entry.get().strip()
        description = self.description_entry.get("1.0", tk.END).strip()
        deadline = self.deadline_entry.get().strip()
        time_input = self.time_entry.get().strip()

        if deadline:
            try:
                deadline = datetime.strptime(deadline, "%d-%m-%Y")
            except ValueError:
                messagebox.showerror("Invalid Date", "Please enter a valid date (DD-MM-YYYY).")
                return
        else:
            deadline = None

        if time_input:
            try:
                time_obj = datetime.strptime(time_input, "%I:%M %p").time()  # 12-hour format (AM/PM)
            except ValueError:
                messagebox.showerror("Invalid Time", "Please enter a valid time (HH:MM AM/PM).")
                return
        else:
            time_obj = None

        self.task_manager.add_task(title, description, deadline, time_obj)

        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, "Task Title")

        self.description_entry.delete("1.0", tk.END)
        self.description_entry.insert("1.0", "Task Description")

        self.deadline_entry.delete(0, tk.END)
        self.deadline_entry.insert(0, "Deadline (DD-MM-YYYY)")

        self.time_entry.delete(0, tk.END)
        self.time_entry.insert(0, "Time (HH:MM AM/PM)")

        self.refresh_task_list()

    def refresh_task_list(self):
        for widget in self.task_list_frame.winfo_children():
            widget.destroy()

        for idx, task in enumerate(self.task_manager.tasks):
            task_var = tk.IntVar(value=1 if task.completed else 0)

            task_title = tk.Label(self.task_list_frame, text=f"{task.title}", font=("Arial", 12, "bold"), fg="blue")
            task_title.grid(row=idx * 6, column=0, sticky="w", padx=10, pady=5)

            deadline_text = f"Deadline: {task.deadline.strftime('%d-%m-%Y')}" if task.deadline else "No deadline"
            task_deadline = tk.Label(self.task_list_frame, text=deadline_text, font=("Arial", 12,"bold"), fg="red")
            task_deadline.grid(row=idx * 6 + 1, column=0, sticky="w", padx=10, pady=2)

            time_text = f"Time: {task.time.strftime('%I:%M %p')}" if task.time else "No time set"
            task_time = tk.Label(self.task_list_frame, text=time_text, font=("Arial", 12), fg="purple")
            task_time.grid(row=idx * 6 + 2, column=0, sticky="w", padx=10, pady=2)

            task_description = tk.Label(self.task_list_frame, text=task.description, font=("Arial", 10), wraplength=400)
            task_description.grid(row=idx * 6 + 3, column=0, sticky="w", padx=10, pady=2)

            check_button = tk.Checkbutton(
                self.task_list_frame, text="Completed", variable=task_var, onvalue=1, offvalue=0, 
                command=lambda idx=idx, var=task_var: self.toggle_task_completed(idx, var)
            )
            check_button.grid(row=idx * 6 + 4, column=0, padx=10, pady=5)

            edit_button = tk.Button(self.task_list_frame, text="Edit", width=10,bg="white", command=lambda idx=idx: self.edit_task(idx))
            edit_button.grid(row=idx * 6 + 5, column=0, padx=10, pady=5)

            # Add delete button
            delete_button = tk.Button(self.task_list_frame, text="Delete", width=10, bg="red", fg="black", command=lambda idx=idx: self.delete_task(idx))
            delete_button.grid(row=idx * 6 + 5, column=1, padx=10, pady=5)

    def toggle_task_completed(self, idx, var):
        task = self.task_manager.tasks[idx]
        task.completed = bool(var.get())
        self.task_manager.save_tasks()

    def clear_completed_tasks(self):
        self.task_manager.tasks = [task for task in self.task_manager.tasks if not task.completed]
        self.task_manager.save_tasks()
        self.refresh_task_list()

    def edit_task(self, idx):
        task = self.task_manager.tasks[idx]
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, task.title)
        self.description_entry.delete("1.0", tk.END)
        self.description_entry.insert("1.0", task.description)
        self.deadline_entry.delete(0, tk.END)
        self.deadline_entry.insert(0, task.deadline.strftime("%d-%m-%Y") if task.deadline else "")
        self.time_entry.delete(0, tk.END)
        self.time_entry.insert(0, task.time.strftime("%I:%M %p") if task.time else "")

        self.task_manager.tasks.pop(idx)
        self.task_manager.save_tasks()
        self.refresh_task_list()

    def delete_task(self, idx):
        del self.task_manager.tasks[idx]
        self.task_manager.save_tasks()
        self.refresh_task_list()

    def start_reminder_check(self):
        def check_reminders():
            while True:
                now = datetime.now()
                for task in self.task_manager.tasks:
                    if task.deadline and task.time and not task.completed:
                        task_datetime = datetime.combine(task.deadline, task.time)  # Combine date and time
                        if now >= task_datetime and now < task_datetime + timedelta(minutes=1):  # Remind in the exact minute
                            notification.notify(
                                title=f"Reminder: {task.title}",
                                message=f"Time to do: {task.description}",
                                timeout=10
                            )
                            self.task_manager.save_tasks()
                time.sleep(60)  # Check every minute

        reminder_thread = threading.Thread(target=check_reminders, daemon=True)
        reminder_thread.start()

def show_message():
    messagebox.showinfo("Information", "Devoloped by ENG. Ammar Haggag.")

# Create the main window
root = tk.Tk()

# Create task manager and app instances
task_manager = TaskManager()
app = TaskApp(root, task_manager)

# Run the GUI
root.mainloop()
