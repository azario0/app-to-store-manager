import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import mysql.connector
import os
import shutil

# Database connection setup
db = mysql.connector.connect(
    host="localhost",
    user="username",
    password="password",
    database="store_db"
)
cursor = db.cursor()

# Initialize main app window
app = ctk.CTk()
app.title("Store Manager")
app.geometry("1000x800")

# Global variables
selected_image_path = None
current_image_label = None
preview_image_label = None
UPLOAD_FOLDER = ""  # This will store the selected upload directory

def setup_upload_folder():
    global UPLOAD_FOLDER
    if not UPLOAD_FOLDER:
        UPLOAD_FOLDER = filedialog.askdirectory(title="Select Upload Directory for Images")
        if not UPLOAD_FOLDER:
            messagebox.showwarning("Warning", "Please select an upload directory for images")
            return False
    return True

def copy_image_to_uploads(source_path):
    if not setup_upload_folder():
        return None
        

    original_filename = os.path.basename(source_path)
    destination_path = os.path.join(UPLOAD_FOLDER, original_filename)
    
    try:
        # Copy the file to the uploads directory
        shutil.copy2(source_path, destination_path)
        return original_filename
    except Exception as e:
        messagebox.showerror("Error", f"Failed to copy image: {str(e)}")
        return None

def resize_image(image_path, size=(200, 200)):
    img = Image.open(image_path)
    img = img.resize(size, Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(img)

# Functions for the "Sales Analytics" Tab
def show_sales_chart():
    cursor.execute("SELECT p.name, COUNT(*) FROM purchases pu JOIN products p ON pu.product_id = p.id GROUP BY p.name")
    data = cursor.fetchall()

    if data:
        labels, sizes = zip(*data)
        plt.pie(sizes, labels=labels, autopct='%1.1f%%')
        plt.title("Sales Distribution by Product")
        plt.show()
    else:
        messagebox.showinfo("Info", "No sales data available.")

def delete_product():
    selected_product = product_listbox.get(tk.ACTIVE)
    if not selected_product:
        messagebox.showwarning("Warning", "Please select a product to delete")
        return
        
    product_id = selected_product.split("ID: ")[-1].strip(")")
    
    # Confirm deletion
    if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this product?"):
        return
        
    try:
        # Get image path before deletion
        cursor.execute("SELECT image FROM products WHERE id=%s", (product_id,))
        image_path = cursor.fetchone()[0]
        
        # Delete from database
        cursor.execute("DELETE FROM products WHERE id=%s", (product_id,))
        db.commit()
        
        # Delete image file if it exists
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except:
                pass  # Ignore if file deletion fails
                
        # Clear the form
        name_entry.delete(0, tk.END)
        detail_textbox.delete("1.0", tk.END)
        if preview_image_label:
            preview_image_label.destroy()
            
        messagebox.showinfo("Success", "Product deleted successfully")
        load_products()
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete product: {str(e)}")
        db.rollback()

# Functions for the "Edit Product" Tab
def load_products():
    product_listbox.delete(0, tk.END)
    cursor.execute("SELECT id, name, image FROM products")
    for product in cursor.fetchall():
        product_listbox.insert(tk.END, f"{product[1]} (ID: {product[0]})")

def select_image():
    global selected_image_path
    selected_image_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
    if selected_image_path:
        display_preview_image(selected_image_path)

def display_preview_image(image_path):
    global preview_image_label
    
    # Remove existing preview if it exists
    if preview_image_label:
        preview_image_label.destroy()
    
    try:
        photo = resize_image(image_path)
        preview_image_label = ctk.CTkLabel(image_frame, text="")
        preview_image_label.image = photo  # Keep a reference
        preview_image_label.configure(image=photo)
        preview_image_label.pack(pady=5)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load image: {str(e)}")

def on_product_select(event):
    selected_product = product_listbox.get(tk.ACTIVE)
    if selected_product:
        product_id = selected_product.split("ID: ")[-1].strip(")")
        cursor.execute("SELECT name, detail, image FROM products WHERE id=%s", (product_id,))
        product = cursor.fetchone()
        
        if product:
            name_entry.delete(0, tk.END)
            name_entry.insert(0, product[0])
            detail_textbox.delete("1.0", tk.END)
            detail_textbox.insert("1.0", product[1] or "")
            print(product)
            
            # Display the product image if it exists
            if product[2] :
                
                
                display_preview_image(UPLOAD_FOLDER+'/'+product[2])

def update_product():
    selected_product = product_listbox.get(tk.ACTIVE)
    if not selected_product:
        messagebox.showwarning("Warning", "Please select a product to update")
        return
        
    product_id = selected_product.split("ID: ")[-1].strip(")")
    new_name = name_entry.get()
    new_detail = detail_textbox.get("1.0", tk.END).strip()
    
    try:
        if selected_image_path:
            # Copy image to uploads directory
            new_image_path = copy_image_to_uploads(selected_image_path)
            if new_image_path:
                cursor.execute("UPDATE products SET name=%s, detail=%s, image=%s WHERE id=%s", 
                            (new_name, new_detail, new_image_path, product_id))
            else:
                return
        else:
            cursor.execute("UPDATE products SET name=%s, detail=%s WHERE id=%s", 
                        (new_name, new_detail, product_id))
        db.commit()
        messagebox.showinfo("Success", "Product updated successfully")
        load_products()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to update product: {str(e)}")
        db.rollback()

# Functions for the "Manage Products" Tab
def add_product():
    global selected_image_path
    name = add_name_entry.get()
    detail = add_detail_textbox.get("1.0", tk.END).strip()

    if not all([name, detail, selected_image_path]):
        messagebox.showwarning("Warning", "Please fill all fields and select an image.")
        return

    try:
        # Copy image to uploads directory
        new_image_path = copy_image_to_uploads(selected_image_path)
        if not new_image_path:
            return
            
        cursor.execute("INSERT INTO products (name, detail, image) VALUES (%s, %s, %s)", 
                    (name, detail, new_image_path))
        db.commit()
        messagebox.showinfo("Success", "Product added successfully!")
        
        # Clear the form
        add_name_entry.delete(0, tk.END)
        add_detail_textbox.delete("1.0", tk.END)
        if preview_image_label:
            preview_image_label.destroy()
        selected_image_path = None

        # Load the products to update the list in the Edit Product tab
        load_products()
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to add product: {str(e)}")
        db.rollback()


# Setup tabs
tabs = ctk.CTkTabview(app, width=950, height=750)
tabs.pack(pady=10)

# Sales Analytics Tab
analytics_tab = tabs.add("Sales Analytics")
analytics_button = ctk.CTkButton(analytics_tab, text="Show Sales Chart", command=show_sales_chart)
analytics_button.pack(pady=20)

# Edit Product Tab
edit_tab = tabs.add("Edit Product")

# Create left and right frames for better organization
left_frame = ctk.CTkFrame(edit_tab)
left_frame.pack(side="left", padx=10, pady=10, fill="y")

right_frame = ctk.CTkFrame(edit_tab)
right_frame.pack(side="right", padx=10, pady=10, fill="both", expand=True)

# Left frame contents (product list)
product_listbox = tk.Listbox(left_frame, width=40, height=20)
product_listbox.pack(side="left", pady=10)
product_listbox.bind('<<ListboxSelect>>', on_product_select)

scrollbar = ctk.CTkScrollbar(left_frame)
scrollbar.pack(side="right", fill="y")
product_listbox.config(yscrollcommand=scrollbar.set)
scrollbar.configure(command=product_listbox.yview)

# Right frame contents (edit form)
name_entry = ctk.CTkEntry(right_frame, placeholder_text="Edit Name", width=300)
name_entry.pack(pady=5)

detail_label = ctk.CTkLabel(right_frame, text="Edit Detail")
detail_label.pack(pady=5)
detail_textbox = ctk.CTkTextbox(right_frame, width=300, height=100)
detail_textbox.pack(pady=5)

# Image frame for preview
image_frame = ctk.CTkFrame(right_frame)
image_frame.pack(pady=10)

image_button = ctk.CTkButton(right_frame, text="Select New Image", command=select_image)
image_button.pack(pady=5)

# Buttons frame
buttons_frame = ctk.CTkFrame(right_frame)
buttons_frame.pack(pady=10)

update_button = ctk.CTkButton(buttons_frame, text="Update Product", command=update_product)
update_button.pack(side="left", padx=5)

delete_button = ctk.CTkButton(buttons_frame, text="Delete Product", 
                             command=delete_product,
                             fg_color="#FF4444",
                             hover_color="#DD2222")
delete_button.pack(side="left", padx=5)

# Set Upload Directory Button
set_upload_dir_button = ctk.CTkButton(right_frame, 
                                     text="Set Upload Directory",
                                     command=setup_upload_folder)
set_upload_dir_button.pack(pady=5)

# Manage Products Tab
manage_tab = tabs.add("Manage Products")

add_name_entry = ctk.CTkEntry(manage_tab, width=300, placeholder_text="Product Name")
add_name_entry.pack(pady=5)

add_detail_label = ctk.CTkLabel(manage_tab, text="Product Detail")
add_detail_label.pack(pady=5)
add_detail_textbox = ctk.CTkTextbox(manage_tab, width=300, height=100)
add_detail_textbox.pack(pady=5)

# Image preview frame for new products
add_image_frame = ctk.CTkFrame(manage_tab)
add_image_frame.pack(pady=10)

add_image_button = ctk.CTkButton(manage_tab, text="Select Image", command=select_image)
add_image_button.pack(pady=5)

add_product_button = ctk.CTkButton(manage_tab, text="Add Product", command=add_product)
add_product_button.pack(pady=10)

# Load initial product data
load_products()

# Initial setup of upload directory
setup_upload_folder()

# Run the app
app.mainloop()