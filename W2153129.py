import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime
import uuid

# Task class
class Task:
    def __init__(self, name, description, priority, due_date, task_id=None):
        self.id = task_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.priority = priority
        self.due_date = due_date

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "due_date": self.due_date
        }

# Task Manager
class TaskManager:
    def __init__(self, filename="tasks.json"):
        self.filename = filename
        self.tasks = self.load_tasks()

    def load_tasks(self):
        try:
            with open(self.filename, "r") as file:
                data = json.load(file)
                return [Task(
                    name=task["name"],
                    description=task["description"],
                    priority=task["priority"],
                    due_date=task["due_date"],
                    task_id=task["id"]
                ) for task in data]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_tasks(self):
        with open(self.filename, "w") as file:
            json.dump([task.to_dict() for task in self.tasks], file, indent=4)

    def add_task(self, task):
        self.tasks.append(task)
        self.save_tasks()

    def update_task(self, task_id, updated_task):
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                self.tasks[i] = updated_task
                self.save_tasks()
                return True
        return False

    def delete_task(self, task_id):
        self.tasks = [task for task in self.tasks if task.id != task_id]
        self.save_tasks()

    def filter_tasks(self, name_filter="", priority_filter="All", due_date_filter=""):
        filtered = self.tasks
        if name_filter:
            filtered = [t for t in filtered if name_filter.lower() in t.name.lower()]
        if priority_filter != "All":
            filtered = [t for t in filtered if t.priority == priority_filter]
        if due_date_filter:
            filtered = [t for t in filtered if t.due_date == due_date_filter]
        return filtered

    def sort_tasks(self, key):
        return sorted(self.tasks, key=lambda task: getattr(task, key))

# GUI class with color and frame
class TaskGUI:
    def __init__(self, root):
        self.manager = TaskManager()
        self.root = root
        self.root.title("Personal Task Manager")

        # Style
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Try different themes like 'clam', 'alt', 'default', 'classic'

        # Configure colors for different priority levels
        self.style.configure("High.Treeview.TLabel", foreground="red")
        self.style.configure("Medium.Treeview.TLabel", foreground="orange")
        self.style.configure("Low.Treeview.TLabel", foreground="green")

        # Add/Edit/Delete Frame
        add_frame = tk.Frame(root, padx=10, pady=10) # Added padding
        add_frame.pack(pady=10, fill="x") # Fill makes it expand horizontally

        self.name_entry = tk.Entry(add_frame)
        self.name_entry.insert(0, "Task Name")
        self.name_entry.bind("<FocusIn>", self.clear_name_placeholder)
        self.name_entry.bind("<FocusOut>", self.reset_name_placeholder)
        self.name_entry.grid(row=0, column=0, padx=5, sticky="ew") # Sticky makes it expand

        self.desc_entry = tk.Entry(add_frame)
        self.desc_entry.insert(0, "Description")
        self.desc_entry.bind("<FocusIn>", self.clear_desc_placeholder)
        self.desc_entry.bind("<FocusOut>", self.reset_desc_placeholder)
        self.desc_entry.grid(row=0, column=1, padx=5, sticky="ew")

        self.prio_cb_add = ttk.Combobox(add_frame, values=["High", "Medium", "Low"])
        self.prio_cb_add.set("Medium")
        self.prio_cb_add.grid(row=0, column=2, padx=5, sticky="ew")

        self.date_entry = tk.Entry(add_frame)
        self.date_entry.insert(0, "YYYY-MM-DD")
        self.date_entry.bind("<FocusIn>", self.clear_date_placeholder)
        self.date_entry.bind("<FocusOut>", self.reset_date_placeholder)
        self.date_entry.grid(row=0, column=3, padx=5, sticky="ew")

        tk.Button(add_frame, text="Add Task", command=self.add_task).grid(row=0, column=4, padx=5, sticky="ew")
        tk.Button(add_frame, text="Edit Task", command=self.edit_task).grid(row=0, column=5, padx=5, sticky="ew")
        tk.Button(add_frame, text="Delete Task", command=self.delete_task).grid(row=0, column=6, padx=5, sticky="ew")

        # Treeview Frame
        tree_frame = tk.Frame(root, padx=10, pady=10) # Separate frame for the Treeview
        tree_frame.pack(pady=10, fill="both", expand=True) # Fill and expand to take available space

        columns = ("ID", "Name", "Description", "Priority", "Due Date")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings") # Treeview inside tree_frame
        self.tree.column("ID", width=0, stretch=tk.NO)
        for col in columns[1:]:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=120)
        self.tree.pack(fill="both", expand=True) # Fill and expand inside its frame
        self.tree.bind("<<TreeviewSelect>>", self.populate_fields_from_selection)
        self.load_table()

        # Search Filter Frame
        filter_frame = tk.Frame(root, padx=10, pady=10) # Separate frame for filters
        filter_frame.pack(pady=10, fill="x")

        tk.Label(filter_frame, text="Search:").grid(row=0, column=0)
        self.search_entry = tk.Entry(filter_frame)
        self.search_entry.grid(row=0, column=1, sticky="ew")

        tk.Label(filter_frame, text="Priority:").grid(row=0, column=2, padx=5)
        self.priority_cb = ttk.Combobox(filter_frame, values=["All", "High", "Medium", "Low"])
        self.priority_cb.set("All")
        self.priority_cb.grid(row=0, column=3, sticky="ew")

        tk.Label(filter_frame, text="Due Date (YYYY-MM-DD):").grid(row=0, column=4, padx=5)
        self.due_entry = tk.Entry(filter_frame)
        self.due_entry.grid(row=0, column=5, sticky="ew")

        tk.Button(filter_frame, text="Filter", command=self.apply_filters).grid(row=0, column=6, padx=5, sticky="ew")

        # Configure row tags for coloring based on priority
        self.tree.tag_configure("high", foreground="red")
        self.tree.tag_configure("medium", foreground="orange")
        self.tree.tag_configure("low", foreground="green")

    def load_table(self, tasks=None):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for task in tasks or self.manager.tasks:
            tag = task.priority.lower()
            self.tree.insert("", "end", values=(task.id, task.name, task.description, task.priority, task.due_date), tags=(tag,))

    def apply_filters(self):
        name = self.search_entry.get()
        priority = self.priority_cb.get()
        due_date = self.due_entry.get()

        # Validate the due date format in the filter
        if due_date:
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Filter Error", "Due date filter must be in YYYY-MM-DD format.")
                return

        filtered = self.manager.filter_tasks(name, priority, due_date)
        self.load_table(filtered)

    def sort_by_column(self, column):
        col_key = column.lower().replace(" ", "_")                        # 
        sorted_tasks = self.manager.sort_tasks(col_key)
        self.load_table(sorted_tasks)

    def add_task(self):
        name = self.name_entry.get()
        description = self.desc_entry.get()
        priority = self.prio_cb_add.get()
        due_date = self.date_entry.get()

        if not name or name == "Task Name" or not due_date or due_date == "YYYY-MM-DD":
            messagebox.showerror("Missing Info", "Task name and due date are required.")
            return

        if not priority:
            messagebox.showerror("Missing Info", "Priority is required.")
            return

        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Date Error", "Enter date in %Y-%m-%d format.")
            return

        task = Task(name, description, priority, due_date)
        self.manager.add_task(task)
        self.load_table()
        self.clear_add_fields()

    def edit_task(self):
        selected_id = self.get_selected_id()
        if not selected_id:
            messagebox.showerror("Select Task", "Please select a task to edit.")
            return

        name = self.name_entry.get()
        description = self.desc_entry.get()
        priority = self.prio_cb_add.get()
        due_date = self.date_entry.get()

        if not name or name == "Task Name" or not due_date or due_date == "YYYY-MM-DD":
            messagebox.showerror("Missing Info", "Task name and due date are required.")
            return

        if not priority:
            messagebox.showerror("Missing Info", "Priority is required.")
            return

        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Date Error", "Enter date in %Y-%m-%d format.")
            return

        updated_task = Task(name, description, priority, due_date, task_id=selected_id)
        if self.manager.update_task(selected_id, updated_task):
            self.load_table()
            self.clear_add_fields()
        else:
            messagebox.showerror("Error", "Could not update task.")

    def delete_task(self):
        selected_id = self.get_selected_id()
        if not selected_id:
            messagebox.showerror("Select Task", "Please select a task to delete.")
            return

        confirm = messagebox.askyesno("Delete Task", "Are you sure you want to delete this task?")
        if confirm:
            self.manager.delete_task(selected_id)
            self.load_table()
            self.clear_add_fields()

    def get_selected_id(self):
        selected = self.tree.selection()
        if selected:
            return self.tree.item(selected[0])['values'][0]
        return None

    def populate_fields_from_selection(self, event):
        selected_id = self.get_selected_id()
        if selected_id:
            for task in self.manager.tasks:
                if task.id == selected_id:
                    self.name_entry.delete(0, tk.END)
                    self.name_entry.insert(0, task.name)
                    self.desc_entry.delete(0, tk.END)
                    self.desc_entry.insert(0, task.description)
                    self.prio_cb_add.set(task.priority)
                    self.date_entry.delete(0, tk.END)
                    self.date_entry.insert(0, task.due_date)
                    break

    def clear_add_fields(self):
        self.name_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.reset_name_placeholder(None)
        self.reset_desc_placeholder(None)
        self.reset_date_placeholder(None)
        self.prio_cb_add.set("Medium")

    def clear_name_placeholder(self, event):
        if self.name_entry.get() == "Task Name":
            self.name_entry.delete(0, tk.END)
            self.name_entry.focus()

    def reset_name_placeholder(self, event):
        if self.name_entry.get() == "":
            self.name_entry.insert(0, "Task Name")

    def clear_desc_placeholder(self, event):
        if self.desc_entry.get() == "Description":
            self.desc_entry.delete(0, tk.END)
            self.desc_entry.focus()

    def reset_desc_placeholder(self, event):
        if self.desc_entry.get() == "":
            self.desc_entry.insert(0, "Description")

    def clear_date_placeholder(self, event):
        if self.date_entry.get() == "YYYY-MM-DD":
            self.date_entry.delete(0, tk.END)
            self.date_entry.focus()

    def reset_date_placeholder(self, event):
        if self.date_entry.get() == "":
            self.date_entry.insert(0, "YYYY-MM-DD")

# Run Personal task manager
if __name__ == "__main__":
    root = tk.Tk()
    app = TaskGUI(root)
    root.mainloop()
